"""
LangWatch observability service for tracking LLM interactions and performance.
"""

import logging
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Union

from ..config import RaftConfig
from ..models import DocumentChunk, QADataPoint, Question

logger = logging.getLogger(__name__)


class LangWatchService:
    """Service for LangWatch observability and tracing."""

    def __init__(self, config: RaftConfig):
        self.config = config
        self.enabled: bool = config.langwatch_enabled
        self.langwatch: Optional[Any] = None
        self.current_trace: Optional[Any] = None

        if self.enabled:
            self._initialize_langwatch()

    def _initialize_langwatch(self) -> None:
        """Initialize LangWatch with graceful fallback."""
        if not self.enabled:
            return

        try:
            import langwatch

            # Setup LangWatch with configuration
            setup_kwargs: Dict[str, Union[str, int, float, bool, List[str]]] = {}
            if self.config.langwatch_api_key:
                setup_kwargs["api_key"] = self.config.langwatch_api_key
            if self.config.langwatch_endpoint:
                setup_kwargs["endpoint"] = self.config.langwatch_endpoint

            langwatch.setup(**setup_kwargs)  # type: ignore
            self.langwatch = langwatch

            logger.info("LangWatch observability initialized successfully")
            if self.config.langwatch_debug:
                logger.info("LangWatch debug mode enabled")

        except ImportError:
            logger.warning("LangWatch SDK not available. Install with: pip install langwatch")
            self.enabled = False
            self.langwatch = None
        except Exception as e:
            logger.error(f"Failed to initialize LangWatch: {e}")
            self.enabled = False
            self.langwatch = None

    @contextmanager
    def trace_operation(self, name: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Context manager for tracing an operation.

        Args:
            name: Name of the operation
            metadata: Additional metadata for the trace
        """
        # Check if LangWatch is available and enabled
        if self.enabled and self.langwatch is not None:
            # Create a new trace for the operation
            try:
                trace = self.langwatch.trace(name=name, metadata=metadata or {})
                self.current_trace = trace

                if self.config.langwatch_debug:
                    logger.debug(f"Started LangWatch trace: {name}")

                yield trace

            except Exception as e:
                logger.warning(f"LangWatch trace error: {e}")
                yield None
            finally:
                if hasattr(self, "current_trace") and self.current_trace:
                    try:
                        self.current_trace.deferred_send_spans()
                    except Exception as e:
                        logger.warning(f"Error sending LangWatch spans: {e}")
                self.current_trace = None
        else:
            # LangWatch not available, yield None
            yield None

    @contextmanager
    def span_operation(
        self,
        name: str,
        span_type: str = "workflow",
        input_data: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Context manager for creating a span within a trace.

        Args:
            name: Name of the span
            span_type: Type of span (llm, retrieval, workflow, etc.)
            input_data: Input data for the span
            metadata: Additional metadata
        """
        # Check if LangWatch and current trace are available
        if self.enabled and self.langwatch is not None and self.current_trace is not None:
            # Create span
            try:
                span = self.current_trace.span(name=name, type=span_type, input=input_data, metadata=metadata or {})

                if self.config.langwatch_debug:
                    logger.debug(f"Started LangWatch span: {name} (type: {span_type})")

                yield span

            except Exception as e:
                logger.warning(f"LangWatch span error: {e}")
                yield None
        else:
            # LangWatch or trace not available, yield None
            yield None

    def setup_openai_tracking(self, client):
        """
        Setup automatic tracking for OpenAI client calls.

        Args:
            client: OpenAI client instance
        """
        if self.enabled and self.langwatch and self.current_trace:
            try:
                self.current_trace.autotrack_openai_calls(client)
                if self.config.langwatch_debug:
                    logger.debug("OpenAI automatic tracking enabled for current trace")
            except Exception as e:
                logger.warning(f"Failed to setup OpenAI tracking: {e}")

    def track_document_processing(
        self, chunks: List[DocumentChunk], processing_time: float, metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Track document processing operation.

        Args:
            chunks: List of document chunks processed
            processing_time: Time taken for processing
            metadata: Additional metadata
        """
        if not self.enabled:
            return

        operation_metadata = {
            "operation_type": "document_processing",
            "chunks_count": len(chunks),
            "processing_time_seconds": processing_time,
            "chunk_strategy": chunks[0].metadata.get("chunking_strategy") if chunks else None,
            **(metadata or {}),
        }

        with self.trace_operation("document_processing", operation_metadata) as trace:
            if not trace:
                return

            with self.span_operation(
                "chunk_documents",
                "workflow",
                input_data={
                    "documents_count": len(set(chunk.source for chunk in chunks)),
                    "total_chunks": len(chunks),
                },
                metadata=operation_metadata,
            ) as span:
                if span:
                    span.output = {"chunks_generated": len(chunks), "success": True}

    def track_question_generation(
        self, chunk: DocumentChunk, questions: List[Question], processing_time: float, model_name: str
    ):
        """
        Track question generation operation.

        Args:
            chunk: Source document chunk
            questions: Generated questions
            processing_time: Time taken for generation
            model_name: Name of the model used
        """
        if not self.enabled:
            return

        with self.span_operation(
            "generate_questions",
            "llm",
            input_data={
                "chunk_content": chunk.content[:500] + "..." if len(chunk.content) > 500 else chunk.content,
                "chunk_size": len(chunk.content),
                "questions_requested": len(questions),
            },
            metadata={
                "model": model_name,
                "operation_type": "question_generation",
                "chunk_id": chunk.id,
                "processing_time_seconds": processing_time,
            },
        ) as span:
            if span:
                span.output = {
                    "questions": [q.text for q in questions],
                    "questions_count": len(questions),
                    "success": True,
                }

    def track_answer_generation(
        self, question: str, context: str, answer: str, processing_time: float, model_name: str
    ):
        """
        Track answer generation operation.

        Args:
            question: The question being answered
            context: Context used for answering
            answer: Generated answer
            processing_time: Time taken for generation
            model_name: Name of the model used
        """
        if not self.enabled:
            return

        with self.span_operation(
            "generate_answer",
            "llm",
            input_data={"question": question, "context": context[:500] + "..." if len(context) > 500 else context},
            metadata={
                "model": model_name,
                "operation_type": "answer_generation",
                "processing_time_seconds": processing_time,
                "context_length": len(context),
            },
        ) as span:
            if span:
                span.output = {"answer": answer, "answer_length": len(answer), "success": True}

    def track_qa_dataset_generation(
        self, qa_data_points: List[QADataPoint], total_processing_time: float, metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Track the complete QA dataset generation process.

        Args:
            qa_data_points: Generated QA data points
            total_processing_time: Total time for dataset generation
            metadata: Additional metadata
        """
        if not self.enabled:
            return

        operation_metadata = {
            "operation_type": "qa_dataset_generation",
            "qa_pairs_count": len(qa_data_points),
            "total_processing_time_seconds": total_processing_time,
            "avg_time_per_qa_pair": total_processing_time / len(qa_data_points) if qa_data_points else 0,
            **(metadata or {}),
        }

        with self.trace_operation("qa_dataset_generation", operation_metadata) as trace:
            if not trace:
                return

            with self.span_operation(
                "generate_qa_dataset",
                "workflow",
                input_data={"qa_pairs_requested": len(qa_data_points)},
                metadata=operation_metadata,
            ) as span:
                if span:
                    span.output = {
                        "qa_pairs_generated": len(qa_data_points),
                        "success": True,
                        "dataset_size_bytes": sum(
                            len(str(qa.question)) + len(str(qa.cot_answer)) + len(str(qa.oracle_context))
                            for qa in qa_data_points
                        ),
                    }

    def track_embedding_generation(self, chunks: List[DocumentChunk], processing_time: float, model_name: str):
        """
        Track embedding generation operation.

        Args:
            chunks: Document chunks for embedding
            processing_time: Time taken for embedding generation
            model_name: Name of the embedding model
        """
        if not self.enabled:
            return

        with self.span_operation(
            "generate_embeddings",
            "embedding",
            input_data={
                "chunks_count": len(chunks),
                "total_content_length": sum(len(chunk.content) for chunk in chunks),
            },
            metadata={
                "model": model_name,
                "operation_type": "embedding_generation",
                "processing_time_seconds": processing_time,
            },
        ) as span:
            if span:
                span.output = {
                    "embeddings_generated": len(chunks),
                    "success": True,
                    "avg_embedding_dimension": (
                        len(chunks[0].embedding)
                        if chunks and hasattr(chunks[0], "embedding") and chunks[0].embedding
                        else None
                    ),
                }

    def get_stats(self) -> Dict[str, Any]:
        """Get LangWatch service statistics."""
        return {
            "enabled": self.enabled,
            "initialized": self.langwatch is not None,
            "debug_mode": self.config.langwatch_debug if self.enabled else False,
            "current_trace_active": self.current_trace is not None,
            "api_key_configured": bool(self.config.langwatch_api_key),
            "project_configured": bool(self.config.langwatch_project),
        }


def create_langwatch_service(config: RaftConfig) -> LangWatchService:
    """Create and return a LangWatch service instance."""
    return LangWatchService(config)
