"""
LLM service for question generation and answering.
"""
import logging
import random
import time
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

from tenacity import retry, wait_exponential, retry_if_exception_type
from openai import RateLimitError

from ..models import DocumentChunk, Question, QADataPoint, ProcessingJob, ProcessingResult, DocType
from ..config import RaftConfig
try:
    from ..clients import build_openai_client, ChatCompleter
except ImportError:
    # Mock implementation for demo purposes
    class MockChatCompleter:
        def __init__(self, client):
            self.client = client
            self.stats = None
        
        def __call__(self, **kwargs):
            class MockResponse:
                def __init__(self):
                    self.choices = [MockChoice()]
            
            class MockChoice:
                def __init__(self):
                    self.message = MockMessage()
            
            class MockMessage:
                def __init__(self):
                    self.content = "This is a mock response for testing."
            
            return MockResponse()
        
        def get_stats_and_reset(self):
            class MockStats:
                def __init__(self):
                    self.prompt_tokens = 100
                    self.completion_tokens = 50
                    self.total_tokens = 150
                    self.duration = 2.5
            
            return MockStats()
    
    def build_openai_client(**kwargs):
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
        self.prompt_templates = self._load_prompt_templates()
    
    def _build_client(self):
        """Build OpenAI client."""
        try:
            if self.config.use_azure_identity:
                from ..utils import get_azure_openai_token
                api_key = get_azure_openai_token()
            else:
                api_key = self.config.openai_key
            
            return build_openai_client(api_key=api_key)
        except ImportError:
            return build_openai_client()
    
    def _load_prompt_templates(self) -> Dict[str, str]:
        """Load prompt templates from files."""
        templates = {}
        
        # Load main template
        try:
            template_path = f"{self.config.templates}/{self.config.system_prompt_key}_template.txt"
            with open(template_path, 'r') as f:
                templates[self.config.system_prompt_key] = f.read()
        except FileNotFoundError:
            # Fallback to default templates
            templates['gpt'] = 'You are a helpful assistant who can provide an answer given a question and relevant context.'
            templates['llama'] = 'You are a helpful assistant who can provide an answer given a question and relevant context.'
        
        # Load QA template
        try:
            qa_template_path = f"{self.config.templates}/{self.config.system_prompt_key}_qa_template.txt"
            with open(qa_template_path, 'r') as f:
                templates[f"{self.config.system_prompt_key}_qa"] = f.read()
        except FileNotFoundError:
            # Fallback QA templates
            templates['gpt_qa'] = "Generate %d questions based on the following context that can be answered from the text."
            templates['llama_qa'] = "Generate %d questions based on the following context that can be answered from the text."
        
        return templates
    
    def process_chunks_batch(self, chunks: List[DocumentChunk]) -> List[ProcessingResult]:
        """Process multiple chunks in parallel."""
        jobs = [
            ProcessingJob.create(
                chunk=chunk,
                num_questions=self.config.questions,
                num_distractors=self.config.distractors,
                include_oracle_probability=self.config.p
            )
            for chunk in chunks
        ]
        
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
                            pbar.set_postfix({
                                'completed': len(results),
                                'qa_points': sum(len(r.qa_data_points) for r in results if r.success)
                            })
                            pbar.update(1)
                        except Exception as e:
                            logger.error(f"Error processing chunk: {e}")
                            pbar.update(1)
            else:
                for job in jobs:
                    try:
                        result = self._process_single_job(job, chunks)
                        results.append(result)
                        pbar.set_postfix({
                            'completed': len(results),
                            'qa_points': sum(len(r.qa_data_points) for r in results if r.success)
                        })
                        pbar.update(1)
                    except Exception as e:
                        logger.error(f"Error processing chunk: {e}")
                        pbar.update(1)
        
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
                "total_tokens": stats.total_tokens if stats else 0
            }
            
            return ProcessingResult(
                job_id=job.id,
                qa_data_points=qa_data_points,
                processing_time=processing_time,
                token_usage=token_usage
            )
        
        except Exception as e:
            processing_time = time.time() - start_time
            return ProcessingResult(
                job_id=job.id,
                qa_data_points=[],
                processing_time=processing_time,
                token_usage={},
                error=str(e)
            )
    
    @retry(wait=wait_exponential(multiplier=1, min=10, max=120), 
           reraise=True, retry=retry_if_exception_type(RateLimitError))
    def _generate_questions(self, chunk: DocumentChunk) -> List[Question]:
        """Generate questions for a document chunk."""
        if self.config.doctype == "api":
            return self._generate_api_questions(chunk)
        else:
            return self._generate_general_questions(chunk)
    
    def _generate_api_questions(self, chunk: DocumentChunk) -> List[Question]:
        """Generate questions for API documentation."""
        messages = [
            {
                "role": "system", 
                "content": f"You are a synthetic instruction-api pair generator. Given an API endpoint in the form of a JSON object, generate {self.config.questions} example queries of instructions a user could ask and would be answered by invoking the API call."
            },
            {
                "role": "system",
                "content": "Don't mention 'API' or use any hints or the name of the API. Include ONLY the queries in your response."
            },
            {"role": "user", "content": chunk.content}
        ]
        
        response = self.chat_completer(
            model=self.config.completion_model,
            messages=messages
        )
        
        content = response.choices[0].message.content
        question_texts = [q.strip() for q in content.split('\n') if q.strip() and any(c.isalpha() for c in q)]
        
        return [Question.create(text, chunk.id) for text in question_texts]
    
    def _generate_general_questions(self, chunk: DocumentChunk) -> List[Question]:
        """Generate questions for general documents."""
        qa_template = self.prompt_templates.get(f"{self.config.system_prompt_key}_qa", 
                                                f"Generate {self.config.questions} questions based on the following context.")
        
        messages = [
            {"role": "system", "content": qa_template % self.config.questions},
            {"role": "system", "content": "The questions should be able to be answered in a few words or less. Include only the questions in your response."},
            {"role": "user", "content": chunk.content}
        ]
        
        response = self.chat_completer(
            model=self.config.completion_model,
            messages=messages,
            max_tokens=min(25 * self.config.questions, 512)
        )
        
        content = response.choices[0].message.content
        question_texts = [q.strip() for q in content.split('\n') if q.strip() and any(c.isalpha() for c in q)]
        
        return [Question.create(text, chunk.id) for text in question_texts]
    
    def _generate_qa_data_point(self, question: Question, oracle_chunk: DocumentChunk, 
                               all_chunks: List[DocumentChunk], num_distractors: int, 
                               oracle_probability: float) -> QADataPoint:
        """Generate a complete QA data point with context and answer."""
        # Select distractor chunks
        available_chunks = [c for c in all_chunks if c.id != oracle_chunk.id]
        distractor_chunks = random.sample(available_chunks, min(num_distractors, len(available_chunks)))
        
        # Decide whether to include oracle
        include_oracle = random.random() < oracle_probability
        if not include_oracle and available_chunks:
            # Replace oracle with another distractor
            oracle_chunk = random.choice(available_chunks)
        
        # Generate answer
        answer = self._generate_answer(question.text, oracle_chunk.content)
        
        # Create QA data point
        return QADataPoint.create(
            question=question.text,
            oracle_context=oracle_chunk.content,
            distractor_contexts=[chunk.content for chunk in distractor_chunks],
            cot_answer=answer,
            doctype=self.config.doctype
        )
    
    @retry(wait=wait_exponential(multiplier=1, min=10, max=120), 
           reraise=True, retry=retry_if_exception_type(RateLimitError))
    def _generate_answer(self, question: str, context: str) -> str:
        """Generate an answer for a question given context."""
        if self.config.doctype == "api":
            return self._generate_api_answer(question, context)
        else:
            return self._generate_general_answer(question, context)
    
    def _generate_api_answer(self, question: str, context: str) -> str:
        """Generate answer for API question."""
        prompt = f"{question}\nWrite a python program to call API in {context}.\n\nThe answer should follow the format: <<<domain>>> $DOMAIN \\n, <<<api_call>>>: $API_CALL \\n, <<<api_provider>>>: $API_PROVIDER \\n, <<<explanation>>>: $EXPLANATION \\n, <<<code>>>: $CODE{{}}. Here are the requirements:\\n \\n2. The $DOMAIN should be the domain of the API ('N/A' if unknown). The $API_CALL should have only 1 line of code that calls api.\\n3. The $API_PROVIDER should be the programming framework used.\\n4. $EXPLANATION should be a numbered, step-by-step explanation.\\n5. The $CODE is the python code.\\n6. Do not repeat the format in your answer."
        
        messages = [
            {"role": "system", "content": "You are a helpful API writer who can write APIs based on requirements."},
            {"role": "user", "content": prompt}
        ]
        
        response = self.chat_completer(
            model=self.config.completion_model,
            messages=messages,
            temperature=0,
            max_tokens=512
        )
        
        return response.choices[0].message.content
    
    def _generate_general_answer(self, question: str, context: str) -> str:
        """Generate answer for general question."""
        template = self.prompt_templates.get(self.config.system_prompt_key,
                                           "Answer the question based on the provided context.")
        
        prompt = template.format(question=question, context=context)
        
        messages = [
            {"role": "system", "content": "You are a helpful question answerer who can provide an answer given a question and relevant context."},
            {"role": "system", "content": "You will ignore any content that does not comply with Open AI's content filtering policies in the context."},
            {"role": "user", "content": prompt}
        ]
        
        response = self.chat_completer(
            model=self.config.completion_model,
            messages=messages,
            temperature=0,
            max_tokens=512
        )
        
        return response.choices[0].message.content