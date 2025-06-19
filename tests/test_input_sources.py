"""
Tests for input source functionality.
"""

import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from raft_toolkit.core.sources import InputSourceConfig, InputSourceFactory, LocalInputSource, SourceValidationError


class TestInputSourceConfig:
    """Test InputSourceConfig functionality."""

    def test_valid_config(self):
        """Test creating valid configuration."""
        config = InputSourceConfig(source_type="local", source_uri="/tmp/test")
        assert config.source_type == "local"
        assert config.source_uri == "/tmp/test"
        assert config.supported_types == ["pdf", "txt", "json", "pptx"]
        assert config.max_file_size == 50 * 1024 * 1024

    def test_invalid_config(self):
        """Test configuration validation."""
        with pytest.raises(ValueError):
            InputSourceConfig(source_type="", source_uri="/tmp/test")

        with pytest.raises(ValueError):
            InputSourceConfig(source_type="local", source_uri="")

        with pytest.raises(ValueError):
            InputSourceConfig(source_type="local", source_uri="/tmp/test", max_file_size=0)


class TestInputSourceFactory:
    """Test InputSourceFactory functionality."""

    def test_create_local_source(self):
        """Test creating local input source."""
        config = InputSourceConfig(source_type="local", source_uri="/tmp/test")
        source = InputSourceFactory.create_source(config)
        assert isinstance(source, LocalInputSource)

    def test_unsupported_source_type(self):
        """Test handling unsupported source type."""
        config = InputSourceConfig(source_type="unsupported", source_uri="/tmp/test")
        with pytest.raises(SourceValidationError):
            InputSourceFactory.create_source(config)

    def test_create_from_uri_local(self):
        """Test auto-detection of local URIs."""
        source = InputSourceFactory.create_from_uri("/tmp/test")
        assert isinstance(source, LocalInputSource)
        assert source.config.source_type == "local"

    def test_create_from_uri_s3(self):
        """Test auto-detection of S3 URIs."""
        # This will fail if boto3 is not available, but that's expected
        try:
            source = InputSourceFactory.create_from_uri("s3://my-bucket/path")
            assert source.config.source_type == "s3"
        except SourceValidationError as e:
            # Expected if boto3 is not available
            assert "boto3 is required" in str(e)

    def test_create_from_uri_sharepoint(self):
        """Test auto-detection of SharePoint URIs."""
        # This will fail if required packages are not available, but that's expected
        try:
            source = InputSourceFactory.create_from_uri("https://company.sharepoint.com/sites/mysite/Shared Documents")
            assert source.config.source_type == "sharepoint"
        except SourceValidationError as e:
            # Expected if required packages are not available
            assert "is required for SharePoint" in str(e)

    def test_get_supported_types(self):
        """Test getting supported source types."""
        types = InputSourceFactory.get_supported_types()
        assert "local" in types
        assert "s3" in types
        assert "sharepoint" in types


class TestLocalInputSource:
    """Test LocalInputSource functionality."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory with test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test files
            (temp_path / "test1.pdf").write_text("PDF content 1")
            (temp_path / "test2.txt").write_text("Text content 2")
            (temp_path / "test3.json").write_text('{"key": "value"}')
            (temp_path / "ignored.doc").write_text("Ignored file")

            # Create subdirectory
            sub_dir = temp_path / "subdir"
            sub_dir.mkdir()
            (sub_dir / "test4.pdf").write_text("PDF content 4")

            yield temp_path

    @pytest.fixture
    def local_source(self, temp_dir):
        """Create LocalInputSource for testing."""
        config = InputSourceConfig(
            source_type="local", source_uri=str(temp_dir), supported_types=["pdf", "txt", "json"]
        )
        return LocalInputSource(config)

    @pytest.mark.asyncio
    async def test_validate_existing_directory(self, local_source):
        """Test validation of existing directory."""
        await local_source.validate()
        assert local_source._validated

    @pytest.mark.asyncio
    async def test_validate_nonexistent_path(self):
        """Test validation of non-existent path."""
        config = InputSourceConfig(source_type="local", source_uri="/nonexistent/path")
        source = LocalInputSource(config)

        with pytest.raises(SourceValidationError):
            await source.validate()

    @pytest.mark.asyncio
    async def test_list_documents(self, local_source):
        """Test listing documents from local directory."""
        await local_source.validate()
        documents = await local_source.list_documents()

        # Should find supported files (at least 3: pdf, txt, json)
        assert len(documents) >= 3, f"Expected at least 3 documents, got {len(documents)}"

        # Check file types
        extensions = [doc.extension for doc in documents]
        assert ".pdf" in extensions
        assert ".txt" in extensions
        assert ".json" in extensions
        assert ".doc" not in extensions  # Should be filtered out

        # Check that all documents have required fields
        for doc in documents:
            assert doc.name
            assert doc.source_path
            assert doc.content_type
            assert doc.size is not None
            assert doc.last_modified is not None

    @pytest.mark.asyncio
    async def test_get_document(self, local_source, temp_dir):
        """Test retrieving document content."""
        await local_source.validate()
        documents = await local_source.list_documents()

        # Find a PDF document
        pdf_docs = [doc for doc in documents if doc.extension == ".pdf"]
        assert len(pdf_docs) > 0, f"No PDF documents found. Available: {[doc.extension for doc in documents]}"
        pdf_doc = pdf_docs[0]

        # Retrieve content
        doc_with_content = await local_source.get_document(pdf_doc)

        assert doc_with_content.content is not None
        assert len(doc_with_content.content) > 0
        assert doc_with_content.size == len(doc_with_content.content)

    @pytest.mark.asyncio
    async def test_get_processing_preview(self, local_source):
        """Test getting processing preview."""
        preview = await local_source.get_processing_preview()

        assert "source_type" in preview
        assert "source_uri" in preview
        assert "total_documents" in preview
        assert "supported_documents" in preview
        assert "document_types" in preview
        assert preview["source_type"] == "local"
        assert preview["supported_documents"] <= preview["total_documents"]


class TestS3InputSource:
    """Test S3InputSource functionality."""

    def test_s3_uri_parsing(self):
        """Test S3 URI parsing."""
        # Test if S3 source can be created (may fail if boto3 not available)
        try:
            config = InputSourceConfig(source_type="s3", source_uri="s3://my-bucket/my-prefix")
            from raft_toolkit.core.sources.s3 import S3InputSource

            source = S3InputSource(config)
            assert source.bucket_name == "my-bucket"
            assert source.prefix == "my-prefix"
        except (ImportError, SourceValidationError):
            # Expected if boto3 is not available
            pytest.skip("boto3 not available for S3 testing")

    def test_invalid_bucket_names(self):
        """Test S3 bucket name validation."""
        try:
            from raft_toolkit.core.sources.s3 import S3InputSource

            config = InputSourceConfig(source_type="s3", source_uri="s3://Invalid_Bucket_Name/prefix")

            with pytest.raises(SourceValidationError):
                S3InputSource(config)

        except ImportError:
            pytest.skip("boto3 not available for S3 testing")


class TestSharePointInputSource:
    """Test SharePointInputSource functionality."""

    def test_sharepoint_uri_parsing(self):
        """Test SharePoint URI parsing."""
        try:
            config = InputSourceConfig(
                source_type="sharepoint",
                source_uri="https://company.sharepoint.com/sites/mysite/Shared Documents/folder",
            )
            from raft_toolkit.core.sources.sharepoint import SharePointInputSource

            source = SharePointInputSource(config)
            assert source.site_url == "https://company.sharepoint.com/sites/mysite"
            assert source.library_path == "Shared Documents/folder"
        except (ImportError, SourceValidationError):
            # Expected if required packages are not available
            pytest.skip("Required packages not available for SharePoint testing")

    def test_invalid_sharepoint_url(self):
        """Test SharePoint URL validation."""
        try:
            from raft_toolkit.core.sources.sharepoint import SharePointInputSource

            config = InputSourceConfig(source_type="sharepoint", source_uri="https://invalid-url.com/not-sharepoint")

            with pytest.raises(SourceValidationError):
                SharePointInputSource(config)

        except ImportError:
            pytest.skip("Required packages not available for SharePoint testing")


if __name__ == "__main__":
    # Run a simple test if executed directly
    import sys

    async def run_basic_test():
        """Run a basic functionality test."""
        try:
            # Test factory
            print("Testing InputSourceFactory...")
            types = InputSourceFactory.get_supported_types()
            print(f"Supported types: {types}")

            # Test local source creation
            print("\nTesting local source creation...")
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                (temp_path / "test.pdf").write_text("Test content")

                config = InputSourceConfig(source_type="local", source_uri=str(temp_path))
                source = InputSourceFactory.create_source(config)
                print(f"Created source: {type(source).__name__}")

                # Test validation
                await source.validate()
                print("Validation successful")

                # Test document listing
                documents = await source.list_documents()
                print(f"Found {len(documents)} documents")

                # Test preview
                preview = await source.get_processing_preview()
                print(f"Preview: {preview['total_documents']} total documents")

            print("\n✅ Basic functionality test passed!")

        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback

            traceback.print_exc()
            sys.exit(1)

    asyncio.run(run_basic_test())
