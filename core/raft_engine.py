"""
Main RAFT engine that orchestrates the entire process.
"""
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

from .config import RaftConfig
from .models import DocumentChunk, ProcessingResult
from .services.document_service import DocumentService
from .services.llm_service import LLMService
from .services.dataset_service import DatasetService

logger = logging.getLogger(__name__)

class RaftEngine:
    """Main engine for RAFT dataset generation."""
    
    def __init__(self, config: RaftConfig):
        self.config = config
        self.llm_service = LLMService(config)
        self.document_service = DocumentService(config, self.llm_service)
        self.dataset_service = DatasetService(config)
    
    def generate_dataset(self, data_path: Path, output_path: str) -> Dict[str, Any]:
        """
        Main method to generate a RAFT dataset.
        
        Args:
            data_path: Path to input documents
            output_path: Path to save output dataset
            
        Returns:
            Dictionary with generation statistics and metadata
        """
        start_time = time.time()
        logger.info("Starting RAFT dataset generation")
        
        try:
            # Step 1: Process documents into chunks
            logger.info("Step 1: Processing documents and creating chunks")
            chunks = self.document_service.process_documents(data_path)
            logger.info(f"Created {len(chunks)} chunks from documents")
            
            if not chunks:
                raise ValueError("No chunks were created from the input documents")
            
            # Step 2: Generate QA data points
            logger.info("Step 2: Generating questions and answers")
            results = self.llm_service.process_chunks_batch(chunks)
            
            # Step 3: Create and save dataset
            logger.info("Step 3: Creating and saving dataset")
            dataset = self.dataset_service.create_dataset_from_results(results)
            self.dataset_service.save_dataset(dataset, output_path)
            
            # Calculate statistics
            processing_time = time.time() - start_time
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
        
        total_qa_points = sum(len(r.qa_data_points) for r in successful_results)
        total_tokens = sum(r.token_usage.get('total_tokens', 0) for r in successful_results)
        total_prompt_tokens = sum(r.token_usage.get('prompt_tokens', 0) for r in successful_results)
        total_completion_tokens = sum(r.token_usage.get('completion_tokens', 0) for r in successful_results)
        
        return {
            'total_qa_points': total_qa_points,
            'successful_chunks': len(successful_results),
            'failed_chunks': len(failed_results),
            'total_processing_time': processing_time,
            'avg_time_per_chunk': processing_time / len(results) if results else 0,
            'token_usage': {
                'total_tokens': total_tokens,
                'prompt_tokens': total_prompt_tokens,
                'completion_tokens': total_completion_tokens,
                'tokens_per_second': total_tokens / processing_time if processing_time > 0 else 0
            },
            'config_used': {
                'doctype': self.config.doctype,
                'chunk_size': self.config.chunk_size,
                'questions_per_chunk': self.config.questions,
                'distractors': self.config.distractors,
                'chunking_strategy': self.config.chunking_strategy,
                'completion_model': self.config.completion_model,
                'embedding_model': self.config.embedding_model
            }
        }
    
    def validate_inputs(self, data_path: Path) -> None:
        """Validate input parameters and paths."""
        if not data_path.exists():
            raise FileNotFoundError(f"Input data path does not exist: {data_path}")
        
        if data_path.is_file():
            expected_extension = f".{self.config.doctype}"
            if not str(data_path).endswith(expected_extension):
                raise ValueError(f"File extension does not match doctype. Expected {expected_extension}, got {data_path.suffix}")
        
        # Validate configuration
        self.config.validate()
        
        logger.info("Input validation completed successfully")
    
    def get_processing_preview(self, data_path: Path) -> Dict[str, Any]:
        """Get a preview of what would be processed without actually processing."""
        if not data_path.exists():
            raise FileNotFoundError(f"Input data path does not exist: {data_path}")
        
        preview = {
            'input_path': str(data_path),
            'doctype': self.config.doctype,
            'files_to_process': [],
            'estimated_chunks': 0,
            'estimated_qa_points': 0
        }
        
        # Get files that would be processed
        if data_path.is_dir():
            files = list(data_path.rglob(f'**/*.{self.config.doctype}'))
        else:
            files = [data_path]
        
        preview['files_to_process'] = [str(f) for f in files]
        
        # Rough estimation (this could be improved with actual file analysis)
        if self.config.doctype == "api":
            # For API docs, estimate based on JSON structure
            preview['estimated_chunks'] = len(files)  # Assume one API per file
        else:
            # For text documents, rough estimate based on average file size
            total_chars = sum(f.stat().st_size for f in files if f.exists())
            preview['estimated_chunks'] = max(1, total_chars // (self.config.chunk_size * 4))  # Rough char to token ratio
        
        preview['estimated_qa_points'] = preview['estimated_chunks'] * self.config.questions
        
        return preview