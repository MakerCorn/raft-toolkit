"""
Local filesystem input source implementation.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import List

from .base import BaseInputSource, SourceDocument, SourceValidationError


class LocalInputSource(BaseInputSource):
    """Input source for local filesystem paths."""

    async def validate(self) -> None:
        """Validate local path exists and is accessible."""
        from ..security import SecurityConfig

        # Security validation first
        if not SecurityConfig.validate_file_path(self.config.source_uri):
            raise SourceValidationError(f"Path is unsafe: {self.config.source_uri}")

        path = Path(self.config.source_uri).resolve()

        # Re-validate after normalization
        if not SecurityConfig.validate_file_path(str(path)):
            raise SourceValidationError(f"Resolved path is unsafe: {path}")

        if not path.exists():
            raise SourceValidationError(f"Path does not exist: {path}")

        if not (path.is_file() or path.is_dir()):
            raise SourceValidationError(f"Path is not a file or directory: {path}")

        if not os.access(path, os.R_OK):
            raise SourceValidationError(f"Path is not readable: {path}")

        self._validated = True
        self.logger.info(f"Validated local source: {path}")

    async def list_documents(self) -> List[SourceDocument]:
        """List all documents in the local path."""
        if not self._validated:
            await self.validate()

        path = Path(self.config.source_uri).resolve()
        documents = []

        if path.is_file():
            # Single file
            documents.append(self._create_document_from_path(path))
        else:
            # Directory - recursively find files
            if self.config.recursive:
                pattern = "**/*"
            else:
                pattern = "*"

            for file_path in path.glob(pattern):
                if file_path.is_file():
                    try:
                        documents.append(self._create_document_from_path(file_path))
                    except Exception as e:
                        self.logger.warning(f"Error processing {file_path}: {e}")
                        continue

        # Apply filtering
        filtered_documents = self._filter_documents(documents)

        self.logger.info(f"Found {len(documents)} total files, {len(filtered_documents)} after filtering")
        return filtered_documents

    async def get_document(self, document: SourceDocument) -> SourceDocument:
        """Retrieve document content from local filesystem."""
        file_path = Path(document.source_path)

        if not file_path.exists():
            raise SourceValidationError(f"Document no longer exists: {file_path}")

        try:
            # Read file content
            with open(file_path, "rb") as f:
                content = f.read()

            # Update document with content
            document.content = content
            document.size = len(content)

            return document

        except Exception as e:
            raise SourceValidationError(f"Failed to read document {file_path}: {e}")

    def _create_document_from_path(self, file_path: Path) -> SourceDocument:
        """Create a SourceDocument from a local file path."""
        try:
            stat = file_path.stat()

            return SourceDocument(
                name=file_path.name,
                source_path=str(file_path.absolute()),
                content_type="",  # Will be inferred in __post_init__
                size=stat.st_size,
                last_modified=datetime.fromtimestamp(stat.st_mtime),
                metadata={
                    "full_path": str(file_path.absolute()),
                    "relative_path": self._get_safe_relative_path(file_path),
                    "permissions": oct(stat.st_mode)[-3:],
                },
            )
        except Exception as e:
            raise SourceValidationError(f"Failed to get file info for {file_path}: {e}")

    def _get_safe_relative_path(self, file_path: Path) -> str:
        """Get relative path safely, handling path resolution issues."""
        try:
            # Try the normal approach first
            source_path = Path(self.config.source_uri).resolve()
            file_path_resolved = file_path.resolve()
            return str(file_path_resolved.relative_to(source_path))
        except ValueError:
            # Fallback: try with both paths normalized to handle /private prefix on macOS
            try:
                source_str = str(Path(self.config.source_uri).resolve())
                file_str = str(file_path.resolve())

                # Handle macOS /private prefix inconsistency
                if source_str.startswith("/var/") and file_str.startswith("/private/var/"):
                    file_str = file_str.replace("/private", "", 1)
                elif source_str.startswith("/private/var/") and file_str.startswith("/var/"):
                    source_str = source_str.replace("/private", "", 1)

                # Calculate relative path manually
                if file_str.startswith(source_str):
                    return file_str[len(source_str) :].lstrip("/")
                else:
                    # Final fallback: just use the filename
                    return file_path.name
            except Exception:
                # Ultimate fallback
                return file_path.name
