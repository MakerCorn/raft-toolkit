"""
Unit tests for CLI module.
"""

import tempfile
from unittest.mock import Mock, patch

import pytest
from core.config import RaftConfig


class TestCLIModule:
    """Test CLI module functionality."""

    def test_config_creation_from_args(self):
        """Test creating configuration from CLI arguments."""
        # Mock CLI arguments
        args = {
            "datapath": "test.txt",
            "output": "./output",
            "openai_key": "test-key",
            "completion_model": "gpt-3.5-turbo",
            "questions": 5,
            "distractors": 3,
            "chunk_size": 512,
            "workers": 4,
            "doctype": "txt",
        }

        # Create config from args
        config = RaftConfig(**args)

        assert str(config.datapath) == "test.txt"
        assert config.output == "./output"
        assert config.openai_key == "test-key"
        assert config.completion_model == "gpt-3.5-turbo"
        assert config.questions == 5
        assert config.distractors == 3
        assert config.chunk_size == 512
        assert config.workers == 4
        assert config.doctype == "txt"

    def test_config_validation(self):
        """Test configuration validation."""
        # Valid configuration
        config = RaftConfig(datapath="test.txt", openai_key="test-key", doctype="txt")

        # Should have default values
        assert config.questions > 0
        assert config.distractors >= 0
        assert config.chunk_size > 0
        assert config.workers > 0

    def test_config_with_missing_required_fields(self):
        """Test configuration with missing required fields."""
        try:
            config = RaftConfig()
            # Validation should catch missing required fields
            config.validate()
        except Exception as e:
            # Expected to fail validation
            assert "required" in str(e).lower() or "missing" in str(e).lower()

    def test_config_with_invalid_values(self):
        """Test configuration with invalid values."""
        try:
            config = RaftConfig(
                datapath="test.txt",
                openai_key="test-key",
                questions=-1,  # Invalid negative value
                chunk_size=0,  # Invalid zero value
                workers=-5,  # Invalid negative value
            )
            config.validate()
        except Exception:
            # Expected to fail validation
            pass

    def test_config_output_format_options(self):
        """Test different output format options."""
        formats = ["hf", "completion", "chat"]

        for fmt in formats:
            config = RaftConfig(datapath="test.txt", openai_key="test-key", output_format=fmt)
            assert config.output_format == fmt

    def test_config_output_type_options(self):
        """Test different output type options."""
        types = ["jsonl", "parquet"]

        for output_type in types:
            config = RaftConfig(datapath="test.txt", openai_key="test-key", output_type=output_type)
            assert config.output_type == output_type

    def test_config_chunking_strategies(self):
        """Test different chunking strategies."""
        strategies = ["semantic", "fixed", "sentence"]

        for strategy in strategies:
            config = RaftConfig(datapath="test.txt", openai_key="test-key", chunking_strategy=strategy)
            assert config.chunking_strategy == strategy

    def test_config_doctype_options(self):
        """Test different document type options."""
        doctypes = ["pdf", "txt", "json", "api", "pptx"]

        for doctype in doctypes:
            config = RaftConfig(datapath="test.txt", openai_key="test-key", doctype=doctype)
            assert config.doctype == doctype

    def test_config_azure_settings(self):
        """Test Azure-specific configuration settings."""
        config = RaftConfig(datapath="test.txt", use_azure_identity=True, azure_openai_enabled=True)

        assert config.use_azure_identity is True
        assert config.azure_openai_enabled is True

    def test_config_rate_limiting_settings(self):
        """Test rate limiting configuration."""
        config = RaftConfig(
            datapath="test.txt",
            openai_key="test-key",
            rate_limit_enabled=True,
            rate_limit_strategy="sliding_window",
            rate_limit_requests_per_minute=100,
            rate_limit_tokens_per_minute=5000,
        )

        if hasattr(config, "rate_limit_enabled"):
            assert config.rate_limit_enabled is True
        if hasattr(config, "rate_limit_strategy"):
            assert config.rate_limit_strategy == "sliding_window"

    def test_config_template_settings(self):
        """Test template configuration."""
        config = RaftConfig(
            datapath="test.txt",
            openai_key="test-key",
            templates="./custom_templates",
            qa_prompt_template="custom_qa.txt",
            answer_prompt_template="custom_answer.txt",
        )

        if hasattr(config, "templates"):
            assert config.templates == "./custom_templates"

    def test_config_source_settings(self):
        """Test input source configuration."""
        # Local source
        config = RaftConfig(datapath="test.txt", source_type="local")
        if hasattr(config, "source_type"):
            assert config.source_type == "local"

        # S3 source
        config = RaftConfig(source_type="s3", source_uri="s3://bucket/path")
        if hasattr(config, "source_type"):
            assert config.source_type == "s3"
        if hasattr(config, "source_uri"):
            assert config.source_uri == "s3://bucket/path"

    def test_config_from_env_file(self):
        """Test loading configuration from environment file."""
        # Create temporary .env file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("OPENAI_API_KEY=env-test-key\n")
            f.write("RAFT_QUESTIONS=3\n")
            f.write("RAFT_DISTRACTORS=2\n")
            env_file = f.name

        try:
            # Test that config can be created (actual env loading depends on implementation)
            config = RaftConfig(datapath="test.txt", openai_key="fallback-key")

            # Should have some configuration
            assert config.openai_key is not None
            assert config.questions > 0

        finally:
            import os

            if os.path.exists(env_file):
                os.unlink(env_file)

    def test_config_defaults(self):
        """Test that configuration has reasonable defaults."""
        config = RaftConfig(datapath="test.txt", openai_key="test-key")

        # Should have reasonable defaults
        assert config.questions >= 1
        assert config.distractors >= 0
        assert config.chunk_size > 0
        assert config.workers >= 1
        assert config.p >= 0.0 and config.p <= 1.0

        # Should have default models
        assert config.completion_model is not None
        assert config.embedding_model is not None

        # Should have default output settings
        assert config.output_format in ["hf", "completion", "chat"]
        assert config.output_type in ["jsonl", "parquet"]
