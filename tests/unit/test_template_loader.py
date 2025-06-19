"""
Tests for template loader utility.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from raft_toolkit.core.config import RaftConfig
from raft_toolkit.core.utils.template_loader import TemplateLoader, create_template_loader


@pytest.mark.unit
class TestTemplateLoader:
    """Test TemplateLoader class."""

    @pytest.fixture
    def config(self):
        """Create test config."""
        return RaftConfig(datapath=Path("test.pdf"), output="output", openai_key="test-key", templates="./templates")

    @pytest.fixture
    def template_loader(self, config):
        """Create TemplateLoader instance."""
        return TemplateLoader(config)

    def test_init(self, template_loader, config):
        """Test TemplateLoader initialization."""
        assert template_loader.config == config
        assert template_loader.templates_dir == Path("./templates")

    def test_load_template_file_exists(self, template_loader, tmp_path):
        """Test loading template when file exists."""
        # Create a test template file
        template_content = "Test template: {content}"
        template_file = tmp_path / "test_template.txt"
        template_file.write_text(template_content)

        template_loader.templates_dir = tmp_path

        result = template_loader.load_template("test_template.txt")
        assert result == template_content

    def test_load_template_file_not_exists(self, template_loader):
        """Test loading template when file doesn't exist."""
        result = template_loader.load_template("nonexistent.txt")
        assert result is None

    def test_load_embedding_template_custom(self, template_loader, tmp_path):
        """Test loading custom embedding template."""
        template_content = "Embedding template: {content}"
        template_file = tmp_path / "custom_embedding.txt"
        template_file.write_text(template_content)

        result = template_loader.load_embedding_template(str(template_file))
        assert result == template_content

    def test_load_embedding_template_default(self, template_loader, tmp_path):
        """Test loading default embedding template."""
        template_content = "Default embedding: {content}"
        template_file = tmp_path / "embedding_prompt_template.txt"
        template_file.write_text(template_content)

        template_loader.templates_dir = tmp_path

        result = template_loader.load_embedding_template()
        assert result == template_content

    def test_load_qa_template_custom(self, template_loader, tmp_path):
        """Test loading custom QA template."""
        template_content = "QA template: {context}"
        template_file = tmp_path / "custom_qa.txt"
        template_file.write_text(template_content)

        result = template_loader.load_qa_template("gpt", str(template_file))
        assert result == template_content

    def test_load_qa_template_default(self, template_loader, tmp_path):
        """Test loading default QA template."""
        template_content = "Generate %d questions: {context}"
        template_file = tmp_path / "gpt_qa_template.txt"
        template_file.write_text(template_content)

        template_loader.templates_dir = tmp_path

        result = template_loader.load_qa_template("gpt")
        assert result == template_content

    def test_load_answer_template_custom(self, template_loader, tmp_path):
        """Test loading custom answer template."""
        template_content = "Answer template: {question} {context}"
        template_file = tmp_path / "custom_answer.txt"
        template_file.write_text(template_content)

        result = template_loader.load_answer_template("gpt", str(template_file))
        assert result == template_content

    def test_load_answer_template_default(self, template_loader, tmp_path):
        """Test loading default answer template."""
        template_content = "Answer: {question} {context}"
        template_file = tmp_path / "gpt_template.txt"
        template_file.write_text(template_content)

        template_loader.templates_dir = tmp_path

        result = template_loader.load_answer_template("gpt")
        assert result == template_content

    def test_format_template_basic(self, template_loader):
        """Test basic template formatting."""
        template = "Hello {name}, you are {age} years old."
        result = template_loader.format_template(template, name="John", age=30)
        assert result == "Hello John, you are 30 years old."

    def test_format_template_missing_vars(self, template_loader):
        """Test template formatting with missing variables."""
        template = "Hello {name}, you are {age} years old."
        result = template_loader.format_template(template, name="John")
        # Should handle missing variables gracefully
        assert "John" in result

    def test_get_template_path(self, template_loader):
        """Test getting template path."""
        path = template_loader.get_template_path("test.txt")
        assert path == Path("./templates/test.txt")

    def test_template_exists(self, template_loader, tmp_path):
        """Test checking if template exists."""
        template_file = tmp_path / "existing.txt"
        template_file.write_text("content")

        template_loader.templates_dir = tmp_path

        assert template_loader.template_exists("existing.txt") is True
        assert template_loader.template_exists("nonexistent.txt") is False


@pytest.mark.unit
class TestCreateTemplateLoader:
    """Test create_template_loader factory function."""

    def test_create_template_loader(self):
        """Test creating template loader."""
        config = RaftConfig(datapath=Path("test.pdf"), output="output", openai_key="test-key")

        loader = create_template_loader(config)

        assert isinstance(loader, TemplateLoader)
        assert loader.config == config
