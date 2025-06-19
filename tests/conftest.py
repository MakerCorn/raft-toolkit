"""
Pytest configuration and shared fixtures.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from core.config import RaftConfig
from core.models import DocumentChunk, QADataPoint


@pytest.fixture
def sample_config():
    """Create a test configuration."""
    return RaftConfig(
        datapath=Path("test_data.pdf"),
        output="test_output",
        openai_key="test-key",
        completion_model="gpt-4",
        embedding_model="text-embedding-ada-002",
        chunk_size=512,
        questions=3,
        distractors=2,
        workers=1,
        embed_workers=1,
    )


@pytest.fixture
def sample_document_chunk():
    """Create a sample document chunk for testing."""
    return DocumentChunk.create(
        content="This is a test document chunk about artificial intelligence.",
        source="test_document.pdf",
        metadata={"type": "pdf", "chunk_index": 0},
    )


@pytest.fixture
def sample_qa_datapoint():
    """Create a sample QA data point for testing."""
    return QADataPoint(
        id="test-qa-1",
        type="cot",
        question="What is artificial intelligence?",
        context="This is a test document chunk about artificial intelligence.",
        oracle_context="This is a test document chunk about artificial intelligence.",
        cot_answer="Artificial intelligence is a field of computer science focused on creating systems that can perform tasks that typically require human intelligence.",
        instruction="Answer the following question based on the context provided.",
    )


@pytest.fixture
def temp_directory():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_pdf_content():
    """Sample PDF content for testing."""
    return b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(Test document) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000010 00000 n \n0000000053 00000 n \n0000000125 00000 n \n0000000185 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n274\n%%EOF"


@pytest.fixture
def sample_text_content():
    """Sample text content for testing."""
    return "This is a test document. It contains multiple sentences for testing purposes. The document discusses artificial intelligence and machine learning concepts."


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "Test AI response"
    mock_response.usage.total_tokens = 100
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client


@pytest.fixture
def mock_embeddings():
    """Mock embeddings model for testing."""
    mock_embeddings = Mock()
    mock_embeddings.embed_documents.return_value = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
    mock_embeddings.embed_query.return_value = [0.1, 0.2, 0.3]
    return mock_embeddings


@pytest.fixture(autouse=True)
def set_test_env():
    """Set test environment variables."""
    test_env = {"OPENAI_API_KEY": "test-key", "COMPLETION_MODEL": "gpt-4", "EMBEDDING_MODEL": "text-embedding-ada-002"}

    original_env: dict[str, str | None] = {}
    for key, value in test_env.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value

    yield

    # Restore original environment
    for key, original_value in original_env.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value
