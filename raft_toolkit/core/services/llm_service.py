"""
LLM service for question generation and answering.
"""

import logging
import secrets
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict, Iterator, List, Optional, Protocol, Type, TypeVar

# Import tqdm for progress bars
try:
    from tqdm import tqdm
except ImportError:
    # Create a fallback tqdm function if not available
    def tqdm(iterable: Iterator, *args: Any, **kwargs: Any) -> Iterator:  # type: ignore[no-redef]
        return iterable


# Import tenacity for retry logic
try:
    from tenacity import retry, retry_if_exception_type, wait_exponential

    HAS_TENACITY = True
except ImportError:
    HAS_TENACITY = False
    T = TypeVar("T")

    def retry(*args: Any, **kwargs: Any) -> Callable[[T], T]:  # type: ignore[no-redef]
        def decorator(func: T) -> T:
            return func

        return decorator

    class wait_exponential:  # type: ignore[no-redef]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

    class retry_if_exception_type:  # type: ignore[no-redef]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass


# Import OpenAI's RateLimitError
try:
    from openai import RateLimitError

    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

    class RateLimitError(Exception):  # type: ignore[no-redef]
        pass


from raft_toolkit.core.config import RaftConfig
from raft_toolkit.core.models import DocumentChunk, ProcessingJob, ProcessingResult, QADataPoint, Question
from raft_toolkit.core.services.langwatch_service import create_langwatch_service
from raft_toolkit.core.utils.rate_limiter import create_rate_limiter_from_config, get_common_rate_limits
from raft_toolkit.core.utils.template_loader import create_template_loader


# Define protocol for chat completion
class ChatCompleterStats:
    """Statistics for chat completion."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    duration: float = 0.0


class ChatCompleterBase(Protocol):
    """Protocol for chat completion implementations."""

    client: Any

    def __call__(self, **kwargs) -> Any:
        """Execute chat completion."""
        ...

    def get_stats_and_reset(self) -> ChatCompleterStats:
        """Get usage statistics and reset counters."""
        ...


# Try to import real implementation
try:
    from raft_toolkit.core.clients import ChatCompleter as RealChatCompleter
    from raft_toolkit.core.clients import build_openai_client as real_build_openai_client

    ChatCompleter: Type = RealChatCompleter

    def build_openai_client(env_prefix: str = "", **kwargs) -> Any:
        return real_build_openai_client(env_prefix, **kwargs)

except ImportError:
    # Mock implementation for testing
    class MockChatCompleter:
        def __init__(self, client: Any) -> None:
            self.client = client

        def __call__(self, **kwargs) -> Any:
            class MockResponse:
                def __init__(self) -> None:
                    self.choices = [MockChoice()]

            class MockChoice:
                def __init__(self) -> None:
                    self.message = MockMessage()

            class MockMessage:
                def __init__(self) -> None:
                    self.content = "This is a mock response for testing."

            return MockResponse()

        def get_stats_and_reset(self) -> ChatCompleterStats:
            stats = ChatCompleterStats()
            stats.prompt_tokens = 100
            stats.completion_tokens = 50
            stats.total_tokens = 150
            stats.duration = 2.5
            return stats

    def build_openai_client(env_prefix: str = "", **kwargs) -> Any:
        class MockClient:
            pass

        return MockClient()

    ChatCompleter = MockChatCompleter

logger = logging.getLogger(__name__)


class LLMService:
    """Service for LLM-based question generation and answering."""

    def __init__(self, config: RaftConfig):
        self.config = config
        self.client = self._build_client()
        self.chat_completer = ChatCompleter(self.client)
        self.template_loader = create_template_loader(config)
        self.prompt_templates = self._load_prompt_templates()
        self.rate_limiter = self._create_rate_limiter()
        self.langwatch_service = create_langwatch_service(config)

    def _build_client(self):
        """Build OpenAI client."""
        try:
            if self.config.use_azure_identity:
                from raft_toolkit.core.utils import get_azure_openai_token

                api_key = get_azure_openai_token()
            else:
                api_key = self.config.openai_key

            return build_openai_client(api_key=api_key)
        except ImportError:
            return build_openai_client()

    def _load_prompt_templates(self) -> Dict[str, str]:
        """Load prompt templates using the template loader with robust fallback."""
        templates = {}

        # Load embedding template
        try:
            templates["embedding"] = self.template_loader.load_embedding_template(self.config.embedding_prompt_template)
        except Exception as e:
            logger.warning(f"Failed to load embedding template: {e}. Using default.")
            templates["embedding"] = "Generate an embedding for: {content}"

        # Load answer template for the current model type
        try:
            templates[self.config.system_prompt_key] = self.template_loader.load_answer_template(
                self.config.system_prompt_key, self.config.answer_prompt_template
            )
        except Exception as e:
            logger.warning(f"Failed to load answer template: {e}. Using default.")
            templates[self.config.system_prompt_key] = "Question: {question}\nContext: {context}\nAnswer:"

        # Load QA template for the current model type
        try:
            templates[f"{self.config.system_prompt_key}_qa"] = self.template_loader.load_qa_template(
                self.config.system_prompt_key, self.config.qa_prompt_template
            )
        except Exception as e:
            logger.warning(f"Failed to load QA template: {e}. Using default.")
            templates[f"{self.config.system_prompt_key}_qa"] = "Generate %d questions based on: {context}"

        return templates

    def _create_rate_limiter(self):
        """Create and configure rate limiter based on config."""
        if not self.config.rate_limit_enabled:
            # Create a disabled rate limiter
            return create_rate_limiter_from_config(enabled=False)

        # Start with preset configuration if specified
        rate_limit_config = {}
        if self.config.rate_limit_preset:
            presets = get_common_rate_limits()
            if self.config.rate_limit_preset in presets:
                rate_limit_config = presets[self.config.rate_limit_preset].copy()
                logger.info(f"Using rate limit preset: {self.config.rate_limit_preset}")
            else:
                logger.warning(f"Unknown rate limit preset: {self.config.rate_limit_preset}")

        # Override with explicit configuration
        rate_limit_config.update(
            {
                "enabled": True,
                "strategy": self.config.rate_limit_strategy,
                "max_retries": self.config.rate_limit_max_retries,
                "base_retry_delay": self.config.rate_limit_base_delay,
                "burst_window_seconds": self.config.rate_limit_burst_window,
            }
        )

        # Override with specific values if provided
        if self.config.rate_limit_requests_per_minute is not None:
            rate_limit_config["requests_per_minute"] = self.config.rate_limit_requests_per_minute
        if self.config.rate_limit_requests_per_hour is not None:
            rate_limit_config["requests_per_hour"] = self.config.rate_limit_requests_per_hour
        if self.config.rate_limit_tokens_per_minute is not None:
            rate_limit_config["tokens_per_minute"] = self.config.rate_limit_tokens_per_minute
        if self.config.rate_limit_tokens_per_hour is not None:
            rate_limit_config["tokens_per_hour"] = self.config.rate_limit_tokens_per_hour
        if self.config.rate_limit_max_burst is not None:
            rate_limit_config["max_burst_requests"] = self.config.rate_limit_max_burst

        rate_limiter = create_rate_limiter_from_config(**rate_limit_config)

        if rate_limiter.config.enabled:
            logger.info(f"Rate limiting enabled with strategy: {rate_limiter.config.strategy.value}")
            stats = rate_limiter.get_statistics()
            if stats.get("current_rate_limit"):
                logger.info(f"Rate limit: {stats['current_rate_limit']:.1f} requests/minute")

        return rate_limiter

    def process_chunks_batch(self, chunks: List[DocumentChunk]) -> List[ProcessingResult]:
        """Process multiple chunks in parallel with LangWatch tracking."""
        jobs = [
            ProcessingJob.create(
                chunk=chunk,
                num_questions=self.config.questions,
                num_distractors=self.config.distractors,
                include_oracle_probability=self.config.p,
            )
            for chunk in chunks
        ]

        batch_start_time = time.time()

        # Track the entire batch processing operation
        with self.langwatch_service.trace_operation(
            "process_chunks_batch",
            metadata={
                "chunks_count": len(chunks),
                "jobs_count": len(jobs),
                "workers": self.config.workers,
                "questions_per_chunk": self.config.questions,
                "distractors_per_qa": self.config.distractors,
            },
        ) as trace:
            # Setup OpenAI tracking if trace is active
            if trace:
                self.langwatch_service.setup_openai_tracking(self.client)

            results = []
            futures = []

            with tqdm(total=len(jobs), desc="Processing chunks", unit="chunk") as pbar:
                if self.config.workers > 1:
                    with ThreadPoolExecutor(max_workers=self.config.workers) as executor:
                        for job in jobs:
                            future = executor.submit(self._process_single_job, job, chunks)
                            futures.append(future)

                        for future in as_completed(futures):
                            try:
                                result = future.result()
                                results.append(result)
                                pbar.set_postfix(
                                    {
                                        "completed": len(results),
                                        "qa_points": sum(len(r.qa_data_points) for r in results if r.success),
                                    }
                                )
                                pbar.update(1)
                            except Exception as e:
                                logger.error(f"Error processing chunk: {e}")
                                pbar.update(1)
                else:
                    for job in jobs:
                        try:
                            result = self._process_single_job(job, chunks)
                            results.append(result)
                            pbar.set_postfix(
                                {
                                    "completed": len(results),
                                    "qa_points": sum(len(r.qa_data_points) for r in results if r.success),
                                }
                            )
                            pbar.update(1)
                        except Exception as e:
                            logger.error(f"Error processing chunk: {e}")
                            pbar.update(1)

            # Track the complete QA dataset generation
            total_processing_time = time.time() - batch_start_time
            all_qa_points = [qa for result in results if result.success for qa in result.qa_data_points]

            self.langwatch_service.track_qa_dataset_generation(
                all_qa_points,
                total_processing_time,
                metadata={
                    "successful_jobs": sum(1 for r in results if r.success),
                    "failed_jobs": sum(1 for r in results if not r.success),
                    "total_token_usage": sum(r.token_usage.get("total_tokens", 0) for r in results if r.token_usage),
                },
            )

        return results

    def _process_single_job(self, job: ProcessingJob, all_chunks: List[DocumentChunk]) -> ProcessingResult:
        """Process a single job to generate QA data points."""
        start_time = time.time()

        try:
            # Generate questions for the chunk
            questions = self._generate_questions(job.chunk)

            # Generate QA data points
            qa_data_points = []
            for question in questions:
                qa_point = self._generate_qa_data_point(
                    question, job.chunk, all_chunks, job.num_distractors, job.include_oracle_probability
                )
                qa_data_points.append(qa_point)

            processing_time = time.time() - start_time

            # Get token usage stats
            stats = self.chat_completer.get_stats_and_reset()
            token_usage = {
                "prompt_tokens": stats.prompt_tokens if stats else 0,
                "completion_tokens": stats.completion_tokens if stats else 0,
                "total_tokens": stats.total_tokens if stats else 0,
            }

            return ProcessingResult(
                job_id=job.id,
                success=True,
                qa_data_points=qa_data_points,
                processing_time=processing_time,
                token_usage=token_usage,
            )

        except Exception as e:
            processing_time = time.time() - start_time
            return ProcessingResult(
                job_id=job.id,
                success=False,
                qa_data_points=[],
                processing_time=processing_time,
                token_usage={},
                error=str(e),
            )

    def _generate_questions(self, chunk: DocumentChunk) -> List[Question]:
        """Generate questions for a document chunk with rate limiting."""
        return self._rate_limited_api_call(  # type: ignore[no-any-return]
            self._generate_questions_impl, chunk, estimated_tokens=self._estimate_tokens_for_questions(chunk)
        )

    def _generate_questions_impl(self, chunk: DocumentChunk) -> List[Question]:
        """Implementation of question generation without rate limiting."""
        start_time = time.time()

        # Select appropriate question generation method based on document type
        if self.config.doctype == "api":
            questions = self._generate_api_questions(chunk)
        else:
            questions = self._generate_general_questions(chunk)

        # Track question generation
        processing_time = time.time() - start_time
        self.langwatch_service.track_question_generation(
            chunk, questions, processing_time, self.config.completion_model
        )

        return questions

    def _estimate_tokens_for_questions(self, chunk: DocumentChunk) -> int:
        """Estimate tokens needed for question generation."""
        # Constants for token estimation
        WORDS_TO_TOKENS_RATIO = 1.3
        SYSTEM_PROMPT_TOKENS = 100
        TOKENS_PER_QUESTION = 15

        # Calculate components
        chunk_tokens = len(chunk.content.split()) * WORDS_TO_TOKENS_RATIO
        prompt_tokens = SYSTEM_PROMPT_TOKENS
        output_tokens = self.config.questions * TOKENS_PER_QUESTION

        return int(chunk_tokens + prompt_tokens + output_tokens)

    def _rate_limited_api_call(
        self, func: Callable, *args: Any, estimated_tokens: Optional[int] = None, **kwargs: Any
    ) -> Any:
        """
        Make a rate-limited API call with retry logic.

        Args:
            func: Function to call
            *args: Arguments for the function
            estimated_tokens: Estimated token usage for this call
            **kwargs: Keyword arguments for the function

        Returns:
            Result of the function call
        """
        # Get rate limiting configuration
        rate_limiter_enabled = self.rate_limiter.config.enabled
        max_retries = self.rate_limiter.config.max_retries if rate_limiter_enabled else 1
        base_delay = self.rate_limiter.config.base_retry_delay if rate_limiter_enabled else 1.0

        for attempt in range(max_retries + 1):
            try:
                # Apply rate limiting before the call
                wait_time = self.rate_limiter.acquire(estimated_tokens)
                if wait_time > 0:
                    logger.debug(f"Rate limiting: waited {wait_time:.2f}s before API call")

                # Make the API call and time it
                start_time = time.time()
                result = func(*args, **kwargs)
                response_time = time.time() - start_time

                # Record successful response
                self.rate_limiter.record_response(response_time, estimated_tokens)
                return result

            except RateLimitError:
                # Handle rate limit errors
                self.rate_limiter.record_error("rate_limit")

                if attempt >= max_retries:
                    logger.error(f"Rate limit exceeded after {max_retries} retries")
                    raise

                # Calculate backoff delay
                delay = self._calculate_backoff_delay(attempt, base_delay)

                logger.warning(f"Rate limit hit (attempt {attempt + 1}/{max_retries + 1}), retrying in {delay:.1f}s")
                time.sleep(delay)

            except Exception as e:
                # Handle other errors
                error_type = "server_error" if "server" in str(e).lower() else "other_error"
                self.rate_limiter.record_error(error_type)

                # Fast fail on authentication errors
                if "auth" in str(e).lower() and self.rate_limiter.config.fail_fast_on_auth_error:
                    logger.error("Authentication error, failing fast")
                    raise

                # Retry on server errors if configured
                if (
                    error_type == "server_error"
                    and self.rate_limiter.config.retry_on_server_error
                    and attempt < max_retries
                ):

                    delay = base_delay * (attempt + 1)
                    logger.warning(
                        f"Server error (attempt {attempt + 1}/{max_retries + 1}), retrying in {delay:.1f}s: {e}"
                    )
                    time.sleep(delay)
                    continue

                raise

        # Should not reach here
        raise Exception(f"Failed after {max_retries} retries")

    def _calculate_backoff_delay(self, attempt: int, base_delay: float) -> float:
        """Calculate backoff delay with optional jitter."""
        if not self.rate_limiter.config.exponential_backoff:
            return float(base_delay)

        # Calculate exponential backoff
        delay = float(base_delay) * (2**attempt)

        # Add jitter if configured
        if self.rate_limiter.config.jitter:
            import secrets

            # Use cryptographically secure random for jitter
            jitter_factor = 0.5 + (secrets.randbelow(500) / 1000.0)  # 0.5-1.0 range
            delay = float(delay * jitter_factor)

        # Cap at maximum delay
        max_delay = float(self.rate_limiter.config.max_retry_delay)
        return float(min(delay, max_delay))

    def _generate_api_questions(self, chunk: DocumentChunk) -> List[Question]:
        """Generate questions for API documentation."""
        # Ensure questions is an integer
        questions_count = int(self.config.questions)

        messages = [
            {
                "role": "system",
                "content": f"You are a synthetic instruction-api pair generator. Given an API endpoint in the form of a JSON object, generate {questions_count} example queries of instructions a user could ask and would be answered by invoking the API call.",
            },
            {
                "role": "system",
                "content": "Don't mention 'API' or use any hints or the name of the API. Include ONLY the queries in your response.",
            },
            {"role": "user", "content": chunk.content},
        ]

        response = self.chat_completer(model=self.config.completion_model, messages=messages)

        content = str(response.choices[0].message.content)
        question_texts = [q.strip() for q in content.split("\n") if q.strip() and any(c.isalpha() for c in q)]

        # Create questions with explicit type annotation
        questions_list: List[Question] = []
        for text in question_texts:
            questions_list.append(Question.create(text, chunk.id))

        return questions_list

    def _generate_general_questions(self, chunk: DocumentChunk) -> List[Question]:
        """Generate questions for general documents."""
        # Ensure questions is an integer
        questions_count = int(self.config.questions)

        qa_template = self.prompt_templates.get(
            f"{self.config.system_prompt_key}_qa",
            f"Generate {questions_count} questions based on the following context.",
        )

        messages = [
            {"role": "system", "content": qa_template % questions_count},
            {
                "role": "system",
                "content": "The questions should be able to be answered in a few words or less. Include only the questions in your response.",
            },
            {"role": "user", "content": chunk.content},
        ]

        # Ensure integer multiplication for max_tokens
        max_tokens_value = min(25 * questions_count, 512)

        response = self.chat_completer(
            model=self.config.completion_model, messages=messages, max_tokens=max_tokens_value
        )

        content = str(response.choices[0].message.content)
        question_texts = [q.strip() for q in content.split("\n") if q.strip() and any(c.isalpha() for c in q)]

        # Create questions with explicit type annotation
        questions_list: List[Question] = []
        for text in question_texts:
            questions_list.append(Question.create(text, chunk.id))

        return questions_list

    def _generate_qa_data_point(
        self,
        question: Question,
        oracle_chunk: DocumentChunk,
        all_chunks: List[DocumentChunk],
        num_distractors: int,
        oracle_probability: float,
    ) -> QADataPoint:
        """Generate a complete QA data point with context and answer."""
        # Select distractor chunks
        available_chunks = [c for c in all_chunks if c.id != oracle_chunk.id]
        # Use secrets.SystemRandom for cryptographically secure sampling
        secure_random = secrets.SystemRandom()
        distractor_chunks = secure_random.sample(available_chunks, min(num_distractors, len(available_chunks)))

        # Decide whether to include oracle
        include_oracle = secure_random.random() < oracle_probability
        if not include_oracle and available_chunks:
            # Replace oracle with another distractor
            oracle_chunk = secure_random.choice(available_chunks)

        # Generate answer
        answer = self._generate_answer(question.text, oracle_chunk.content)

        # Create QA data point
        return QADataPoint.create(
            question=question.text,
            oracle_context=oracle_chunk.content,
            distractor_contexts=[chunk.content for chunk in distractor_chunks],
            cot_answer=answer,
            doctype=self.config.doctype,
        )

    def _generate_answer(self, question: str, context: str) -> str:
        """Generate an answer for a question given context with rate limiting."""
        return self._rate_limited_api_call(  # type: ignore[no-any-return]
            self._generate_answer_impl,
            question,
            context,
            estimated_tokens=self._estimate_tokens_for_answer(question, context),
        )

    def _generate_answer_impl(self, question: str, context: str) -> str:
        """Implementation of answer generation without rate limiting."""
        start_time = time.time()

        # Select appropriate answer generation method based on document type
        if self.config.doctype == "api":
            answer = self._generate_api_answer(question, context)
        else:
            answer = self._generate_general_answer(question, context)

        # Track answer generation
        processing_time = time.time() - start_time
        self.langwatch_service.track_answer_generation(
            question, context, answer, processing_time, self.config.completion_model
        )

        return answer

    def _estimate_tokens_for_answer(self, question: str, context: str) -> int:
        """Estimate tokens needed for answer generation."""
        # Constants for token estimation
        WORDS_TO_TOKENS_RATIO = 1.3
        SYSTEM_PROMPT_TOKENS = 100
        EXPECTED_ANSWER_TOKENS = 150

        # Calculate components
        question_tokens = len(question.split()) * WORDS_TO_TOKENS_RATIO
        context_tokens = len(context.split()) * WORDS_TO_TOKENS_RATIO

        return int(question_tokens + context_tokens + SYSTEM_PROMPT_TOKENS + EXPECTED_ANSWER_TOKENS)

    def _generate_api_answer(self, question: str, context: str) -> str:
        """Generate answer for API question."""
        # Build structured prompt for API answer generation
        prompt_parts = [
            question,
            f"Write a python program to call API in {context}.",
            "",
            "The answer should follow the format:",
            "<<<domain>>> $DOMAIN",
            "<<<api_call>>>: $API_CALL",
            "<<<api_provider>>>: $API_PROVIDER",
            "<<<explanation>>>: $EXPLANATION",
            "<<<code>>>: $CODE{}",
            "",
            "Here are the requirements:",
            "1. The $DOMAIN should be the domain of the API ('N/A' if unknown).",
            "2. The $API_CALL should have only 1 line of code that calls api.",
            "3. The $API_PROVIDER should be the programming framework used.",
            "4. $EXPLANATION should be a numbered, step-by-step explanation.",
            "5. The $CODE is the python code.",
            "6. Do not repeat the format in your answer.",
        ]

        prompt = "\n".join(prompt_parts)

        messages = [
            {"role": "system", "content": "You are a helpful API writer who can write APIs based on requirements."},
            {"role": "user", "content": prompt},
        ]

        response = self.chat_completer(
            model=self.config.completion_model, messages=messages, temperature=0, max_tokens=512
        )

        result: str = str(response.choices[0].message.content)
        return result

    def _generate_general_answer(self, question: str, context: str) -> str:
        """Generate answer for general question."""
        template = self.prompt_templates.get(
            self.config.system_prompt_key, "Answer the question based on the provided context."
        )

        prompt = template.format(question=question, context=context)

        messages = [
            {
                "role": "system",
                "content": "You are a helpful question answerer who can provide an answer given a question and relevant context.",
            },
            {
                "role": "system",
                "content": "You will ignore any content that does not comply with Open AI's content filtering policies in the context.",
            },
            {"role": "user", "content": prompt},
        ]

        response = self.chat_completer(
            model=self.config.completion_model, messages=messages, temperature=0, max_tokens=512
        )

        result: str = str(response.choices[0].message.content)
        return result

    def get_rate_limit_statistics(self) -> Dict[str, Any]:
        """Get rate limiting statistics."""
        result: Dict[str, Any] = self.rate_limiter.get_statistics()
        return result
