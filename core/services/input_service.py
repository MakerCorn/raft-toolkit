"""
Input source service for handling multiple input types (local, S3, SharePoint).
Integrates with existing document processing pipeline.
"""

import logging
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Dict, List

from ..config import RaftConfig
from ..models import DocumentChunk
from ..sources import InputSourceConfig, InputSourceFactory, SourceDocument, SourceValidationError
from .document_service import DocumentService
from .llm_service import LLMService

logger = logging.getLogger(__name__)


class InputService:
    """Service for handling multiple input source types and processing documents."""

    def __init__(self, config: RaftConfig, llm_service: LLMService):
        self.config = config
        self.llm_service = llm_service

        # Create document service for actual processing
        self.document_service = DocumentService(config, llm_service)

        # Create input source based on configuration
        self.input_source = self._create_input_source()

    def _create_input_source(self):
        """Create input source based on configuration."""
        # Determine source URI
        source_uri = self.config.source_uri
        if not source_uri:
            # Fallback to datapath for local sources
            if self.config.source_type == "local":
                source_uri = str(self.config.datapath)
            else:
                raise ValueError(f"source_uri is required for source type: {self.config.source_type}")

        # Create input source configuration
        source_config = InputSourceConfig(
            source_type=self.config.source_type,
            source_uri=source_uri,
            credentials=self.config.source_credentials,
            include_patterns=self.config.source_include_patterns,
            exclude_patterns=self.config.source_exclude_patterns,
            supported_types=[self.config.doctype] if self.config.doctype != "api" else ["json"],
            max_file_size=self.config.source_max_file_size,
            batch_size=self.config.source_batch_size,
            recursive=True,
        )

        return InputSourceFactory.create_source(source_config)

    async def validate_source(self) -> None:
        """Validate the input source configuration and connectivity."""
        try:
            await self.input_source.validate()
            logger.info(f"Successfully validated {self.config.source_type} input source")
        except SourceValidationError as e:
            logger.error(f"Input source validation failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during input source validation: {e}")
            raise SourceValidationError(f"Input source validation failed: {e}")

    async def get_processing_preview(self) -> Dict[str, Any]:
        """Get a preview of what will be processed without actually processing."""
        try:
            preview_data = await self.input_source.get_processing_preview()
            preview: Dict[str, Any] = dict(preview_data)  # Ensure it's a dict

            # Add estimated processing info
            supported_docs = preview["supported_documents"]
            estimated_chunks = max(1, supported_docs * 3)  # Rough estimate
            estimated_qa_points = estimated_chunks * self.config.questions

            preview.update(
                {
                    "estimated_chunks": estimated_chunks,
                    "estimated_qa_points": estimated_qa_points,
                    "chunking_strategy": self.config.chunking_strategy,
                    "chunk_size": self.config.chunk_size,
                    "questions_per_chunk": self.config.questions,
                    "distractors": self.config.distractors,
                }
            )

            return preview

        except Exception as e:
            logger.error(f"Failed to get processing preview: {e}")
            raise

    async def process_documents(self) -> List[DocumentChunk]:
        """Process all documents from the input source."""
        try:
            # Get list of documents
            logger.info("Listing documents from input source...")
            documents = await self.input_source.list_documents()

            if not documents:
                logger.warning("No documents found in input source")
                return []

            logger.info(f"Found {len(documents)} documents to process")

            # Process documents based on source type
            if self.config.source_type == "local":
                # For local sources, use existing file-based processing
                return await self._process_local_documents(documents)
            else:
                # For remote sources, download and process
                return await self._process_remote_documents(documents)

        except Exception as e:
            logger.error(f"Failed to process documents: {e}")
            raise

    async def _process_local_documents(self, documents: List[SourceDocument]) -> List[DocumentChunk]:
        """Process local documents using existing document service."""
        # For local documents, we can use the existing file-based processing
        # Extract the paths and process them directly

        all_chunks = []

        for doc in documents:
            try:
                file_path = Path(doc.source_path)

                # Process single file using existing document service
                chunks = self.document_service.process_documents(file_path)

                # Update chunk metadata to include source information
                for chunk in chunks:
                    chunk.metadata.update(
                        {
                            "source_type": self.config.source_type,
                            "source_uri": self.config.source_uri or str(self.config.datapath),
                            "source_file_size": doc.size,
                            "source_last_modified": doc.last_modified.isoformat() if doc.last_modified else None,
                        }
                    )

                all_chunks.extend(chunks)

            except Exception as e:
                logger.error(f"Failed to process document {doc.name}: {e}")
                continue

        return all_chunks

    async def _process_remote_documents(self, documents: List[SourceDocument]) -> List[DocumentChunk]:
        """Process remote documents by downloading them first."""
        all_chunks = []

        # Process documents in batches to manage memory
        batch_size = min(self.config.source_batch_size, 10)  # Limit concurrent downloads

        for i in range(0, len(documents), batch_size):
            batch = documents[i : i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(documents) + batch_size - 1)//batch_size}")

            # Process batch
            batch_chunks = await self._process_document_batch(batch)
            all_chunks.extend(batch_chunks)

        return all_chunks

    async def _process_document_batch(self, documents: List[SourceDocument]) -> List[DocumentChunk]:
        """Process a batch of documents."""
        batch_chunks = []

        for doc in documents:
            try:
                # Download document content
                logger.debug(f"Downloading document: {doc.name}")
                doc_with_content = await self.input_source.get_document(doc)

                if not doc_with_content.content:
                    logger.warning(f"No content retrieved for document: {doc.name}")
                    continue

                # Create temporary file for processing
                with NamedTemporaryFile(suffix=doc.extension, delete=False) as temp_file:
                    temp_file.write(doc_with_content.content)
                    temp_file_path = Path(temp_file.name)

                try:
                    # Process using existing document service
                    chunks = self.document_service.process_documents(temp_file_path)

                    # Update chunk metadata with source information
                    for chunk in chunks:
                        chunk.metadata.update(
                            {
                                "source_type": self.config.source_type,
                                "source_uri": self.config.source_uri,
                                "source_path": doc.source_path,
                                "source_file_size": doc.size,
                                "source_last_modified": doc.last_modified.isoformat() if doc.last_modified else None,
                                "original_filename": doc.name,
                            }
                        )

                        # Add cloud-specific metadata
                        if self.config.source_type == "s3":
                            chunk.metadata.update(
                                {
                                    "s3_bucket": doc.metadata.get("s3_bucket"),
                                    "s3_key": doc.metadata.get("s3_key"),
                                    "etag": doc.metadata.get("etag"),
                                }
                            )
                        elif self.config.source_type == "sharepoint":
                            chunk.metadata.update(
                                {
                                    "sharepoint_item_id": doc.metadata.get("sharepoint_item_id"),
                                    "author": doc.metadata.get("author"),
                                    "version": doc.metadata.get("version"),
                                }
                            )

                    batch_chunks.extend(chunks)
                    logger.debug(f"Processed {doc.name}: {len(chunks)} chunks")

                finally:
                    # Clean up temporary file
                    try:
                        temp_file_path.unlink()
                    except Exception as e:
                        logger.warning(f"Failed to delete temporary file {temp_file_path}: {e}")

            except Exception as e:
                logger.error(f"Failed to process document {doc.name}: {e}")
                continue

        return batch_chunks

    def get_source_info(self) -> Dict[str, Any]:
        """Get information about the configured input source."""
        return {
            "source_type": self.config.source_type,
            "source_uri": self.config.source_uri or str(self.config.datapath),
            "supported_types": [self.config.doctype] if self.config.doctype != "api" else ["json"],
            "max_file_size_mb": self.config.source_max_file_size / (1024 * 1024),
            "batch_size": self.config.source_batch_size,
            "include_patterns": self.config.source_include_patterns,
            "exclude_patterns": self.config.source_exclude_patterns,
        }
