"""
Main RAFT engine that orchestrates the entire process.
"""

import asyncio
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .config import RaftConfig
from .models import ProcessingResult
from .services.dataset_service import DatasetService
from .services.document_service import DocumentService
from .services.input_service import InputService
from .services.llm_service import LLMService
from .sources import SourceValidationError

logger = logging.getLogger(__name__)


class RaftEngine:
    """Main engine for RAFT dataset generation."""

    def __init__(self, config: RaftConfig):
        self.config = config
        self.llm_service = LLMService(config)
        self.document_service = DocumentService(config, self.llm_service)
        self.input_service = InputService(config, self.llm_service)
        self.dataset_service = DatasetService(config)

    async def validate_input_source(self) -> None:
        """Validate input source configuration and connectivity."""
        try:
            await self.input_service.validate_source()
            logger.info("Input source validation successful")
        except SourceValidationError as e:
            logger.error(f"Input validation failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during input validation: {e}")
            raise

    async def get_processing_preview_async(self) -> Dict[str, Any]:
        """Get a preview of what will be processed without actually processing."""
        try:
            return await self.input_service.get_processing_preview()
        except Exception as e:
            logger.error(f"Failed to get processing preview: {e}")
            raise

    def generate_dataset(self, data_path: Optional[Path] = None, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Main method to generate a RAFT dataset.

        Args:
            data_path: Legacy path parameter (optional, uses config if not provided)
            output_path: Path to save output dataset (uses config if not provided)

        Returns:
            Dictionary with generation statistics and metadata
        """
        # Use asyncio to run the async version
        return asyncio.run(self.generate_dataset_async(data_path, output_path))

    async def generate_dataset_async(
        self, data_path: Optional[Path] = None, output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Async version of dataset generation.

        Args:
            data_path: Legacy path parameter (optional, uses config if not provided)
            output_path: Path to save output dataset (uses config if not provided)

        Returns:
            Dictionary with generation statistics and metadata
        """
        start_time = time.time()
        logger.info("Starting RAFT dataset generation")

        # Use output path from parameter or config
        if not output_path:
            output_path = self.config.output

        try:
            # Step 1: Validate input source
            logger.info("Step 1: Validating input source")
            await self.validate_input_source()

            # Step 2: Process documents into chunks
            logger.info("Step 2: Processing documents and creating chunks")
            chunks = await self.input_service.process_documents()
            logger.info(f"Created {len(chunks)} chunks from documents")

            if not chunks:
                raise ValueError("No chunks were created from the input documents")

            # Step 3: Generate QA data points
            logger.info("Step 3: Generating questions and answers")
            results = self.llm_service.process_chunks_batch(chunks)

            # Step 4: Create and save dataset
            logger.info("Step 4: Creating and saving dataset")
            dataset = self.dataset_service.create_dataset_from_results(results)
            self.dataset_service.save_dataset(dataset, output_path)

            # Calculate statistics
            end_time = time.time()
            processing_time = float(end_time - start_time)
            stats = self._calculate_stats(results, processing_time)

            logger.info(f"RAFT dataset generation completed in {processing_time:.2f}s")
            logger.info(f"Generated {stats['total_qa_points']} QA data points")

            return stats

        except Exception as e:
            logger.error(f"Error during dataset generation: {e}")
            raise

    def _calculate_stats(self, results: List[ProcessingResult], processing_time: float) -> Dict[str, Any]:
        """Calculate generation statistics."""
        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]

        # Calculate token usage statistics
        token_usage: Dict[str, Union[int, float]] = {
            "total_tokens": sum(r.token_usage.get("total_tokens", 0) for r in successful_results),
            "prompt_tokens": sum(r.token_usage.get("prompt_tokens", 0) for r in successful_results),
            "completion_tokens": sum(r.token_usage.get("completion_tokens", 0) for r in successful_results),
        }

        # Add tokens per second if processing time is valid
        if processing_time > 0:
            token_usage["tokens_per_second"] = float(token_usage["total_tokens"]) / float(processing_time)
        else:
            token_usage["tokens_per_second"] = 0.0

        # Get rate limiting statistics from LLM service
        rate_limit_stats = self.llm_service.get_rate_limit_statistics()

        return {
            "total_qa_points": sum(len(r.qa_data_points) for r in successful_results),
            "successful_chunks": len(successful_results),
            "failed_chunks": len(failed_results),
            "total_processing_time": processing_time,
            "avg_time_per_chunk": processing_time / len(results) if results else 0,
            "token_usage": token_usage,
            "rate_limiting": rate_limit_stats,
            "input_source": self.input_service.get_source_info(),
            "config_used": {
                "doctype": self.config.doctype,
                "chunk_size": self.config.chunk_size,
                "questions_per_chunk": self.config.questions,
                "distractors": self.config.distractors,
                "chunking_strategy": self.config.chunking_strategy,
                "completion_model": self.config.completion_model,
                "embedding_model": self.config.embedding_model,
                "rate_limiting_enabled": self.config.rate_limit_enabled,
                "rate_limiting_strategy": self.config.rate_limit_strategy if self.config.rate_limit_enabled else None,
            },
        }

    def validate_inputs(self, data_path: Path) -> None:
        """
        Legacy method for validating local file inputs.
        For new input sources, use validate_inputs() without parameters.
        """
        if self.config.source_type != "local":
            # For non-local sources, use the new async validation
            asyncio.run(self.validate_input_source())
            return

        if not data_path.exists():
            raise FileNotFoundError(f"Input data path does not exist: {data_path}")

        if data_path.is_file():
            expected_extension = f".{self.config.doctype}"
            if not str(data_path).endswith(expected_extension):
                raise ValueError(
                    f"File extension does not match doctype. Expected {expected_extension}, got {data_path.suffix}"
                )

        # Validate configuration
        self.config.validate()

        logger.info("Input validation completed successfully")

    def get_processing_preview(self, data_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Get a preview of what would be processed without actually processing.

        Args:
            data_path: Legacy parameter for local files (optional)
        """
        if self.config.source_type != "local":
            # For non-local sources, use the new async method
            return asyncio.run(self.get_processing_preview_async())

        # Legacy local file handling
        if data_path is None:
            config_datapath = self.config.datapath
            if config_datapath is None:
                raise ValueError("No data path specified")
            data_path = Path(config_datapath) if isinstance(config_datapath, str) else config_datapath

        # Normalize and validate the path
        normalized_path = Path(os.path.normpath(data_path)).resolve()

        if not normalized_path.exists():
            raise FileNotFoundError(f"Input data path does not exist: {normalized_path}")

        preview = {
            "input_path": str(normalized_path),
            "doctype": self.config.doctype,
            "files_to_process": [],
            "estimated_chunks": 0,
            "estimated_qa_points": 0,
        }

        # Get files that would be processed
        if normalized_path.is_dir():
            files = list(normalized_path.rglob(f"**/*.{self.config.doctype}"))
        else:
            files = [normalized_path]

        preview["files_to_process"] = [str(f) for f in files]

        # Rough estimation (this could be improved with actual file analysis)
        if self.config.doctype == "api":
            # For API docs, estimate based on JSON structure
            preview["estimated_chunks"] = len(files)  # Assume one API per file
        else:
            # For text documents, rough estimate based on average file size
            total_chars = sum(f.stat().st_size for f in files if f.exists())
            # Ensure chunk_size is an integer for division
            chunk_size_int = int(self.config.chunk_size)
            # Ensure we're using integer division
            ratio = 4  # Rough char to token ratio
            if total_chars > 0 and chunk_size_int > 0:
                estimated = total_chars // (chunk_size_int * ratio)
                preview["estimated_chunks"] = max(1, estimated)
            else:
                preview["estimated_chunks"] = 1

        # Ensure questions is an integer for multiplication
        questions_int = int(self.config.questions)
        # Use a direct integer value to avoid type issues
        estimated_chunks = preview["estimated_chunks"]
        if isinstance(estimated_chunks, int):
            chunks_count = estimated_chunks
        else:
            chunks_count = int(float(str(estimated_chunks)))
        preview["estimated_qa_points"] = chunks_count * questions_int

        return preview
