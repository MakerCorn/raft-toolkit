"""
Tests for core.config module.
"""
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch

from core.config import RaftConfig, get_config


@pytest.mark.unit
class TestRaftConfig:
    """Test RaftConfig class."""
    
    @pytest.mark.unit
    def test_config_creation(self):
        """Test basic config creation."""
        config = RaftConfig(
            datapath=Path("test.pdf"),
            output="output_dir",
            openai_key="test-key"
        )
        
        assert config.datapath == Path("test.pdf")
        assert config.output == "output_dir"
        assert config.openai_key == "test-key"
        assert config.chunk_size == 512  # default value
        assert config.questions == 5  # default value
    
    @pytest.mark.unit
    def test_config_defaults(self):
        """Test default configuration values."""
        config = RaftConfig(
            datapath=Path("test.pdf"),
            output="output_dir",
            openai_key="test-key"
        )
        
        assert config.output_format == "hf"
        assert config.output_type == "jsonl"
        assert config.doctype == "pdf"
        assert config.chunking_strategy == "semantic"
        assert config.completion_model == "llama3.2"
        assert config.embedding_model == "nomic-embed-text"
        assert config.workers == 1
        assert config.embed_workers == 1
        assert config.distractors == 1
        assert config.p == 1.0
        assert config.pace is True
        assert config.use_azure_identity is False
    
    def test_config_validation_invalid_doctype(self):
        """Test config validation with invalid doctype."""
        config = RaftConfig(openai_key="demo_key_for_testing", doctype="invalid_type")
        with pytest.raises(ValueError, match="Invalid doctype"):
            config.validate()
    
    def test_config_validation_missing_api_key(self):
        """Test config validation with missing API key."""
        config = RaftConfig()
        with pytest.raises(ValueError, match="OpenAI API key is required"):
            config.validate()
    
    def test_config_from_env(self):
        """Test loading config from environment variables."""
        env_vars = {
            "RAFT_DATAPATH": "env_test.pdf",
            "RAFT_OUTPUT": "env_output",
            "OPENAI_API_KEY": "env-key",
            "RAFT_COMPLETION_MODEL": "gpt-3.5-turbo",
            "RAFT_CHUNK_SIZE": "256",
            "RAFT_QUESTIONS": "3",
            "RAFT_WORKERS": "2"
        }
        
        with patch.dict(os.environ, env_vars):
            config = RaftConfig.from_env()
            
            assert str(config.datapath) == "env_test.pdf"
            assert config.output == "env_output"
            assert config.openai_key == "env-key"
            assert config.completion_model == "gpt-3.5-turbo"
            assert config.chunk_size == 256
            assert config.questions == 3
            assert config.workers == 2
    
    def test_config_from_env_file(self):
        """Test loading config from .env file."""
        env_content = """
RAFT_DATAPATH=file_test.pdf
RAFT_OUTPUT=file_output
OPENAI_API_KEY=file-key
RAFT_COMPLETION_MODEL=gpt-4
RAFT_CHUNK_SIZE=1024
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write(env_content)
            env_file = f.name
        
        try:
            # Clear environment variables to test file loading
            with patch.dict(os.environ, {}, clear=False):
                # Remove potentially conflicting environment variables
                for key in ['OPENAI_API_KEY', 'RAFT_OUTPUT', 'RAFT_DATAPATH', 'RAFT_COMPLETION_MODEL', 'RAFT_CHUNK_SIZE']:
                    if key in os.environ:
                        del os.environ[key]
                config = RaftConfig.from_env(env_file)
                
                assert str(config.datapath) == "file_test.pdf"
                assert config.output == "file_output"
                assert config.openai_key == "file-key"
                assert config.completion_model == "gpt-4"
                assert config.chunk_size == 1024
        finally:
            os.unlink(env_file)
    
    def test_config_chunking_params_parsing(self):
        """Test chunking params JSON parsing."""
        config = RaftConfig(
            datapath=Path("test.pdf"),
            output="output_dir",
            openai_key="test-key",
            chunking_params={"overlap": 50, "min_chunk_size": 200}
        )
        
        assert config.chunking_params["overlap"] == 50
        assert config.chunking_params["min_chunk_size"] == 200
    
    def test_config_invalid_output_format(self):
        """Test config validation with invalid output format."""
        with tempfile.NamedTemporaryFile(suffix='.pdf') as temp_file:
            config = RaftConfig(
                datapath=Path(temp_file.name),
                output="output_dir",
                openai_key="demo_key_for_testing",
                output_format="invalid"
            )
            with pytest.raises(ValueError, match="Invalid output format"):
                config.validate()
    
    def test_config_invalid_chunking_strategy(self):
        """Test config validation with invalid chunking strategy."""
        with tempfile.NamedTemporaryFile(suffix='.pdf') as temp_file:
            config = RaftConfig(
                datapath=Path(temp_file.name),
                output="output_dir",
                openai_key="demo_key_for_testing",
                chunking_strategy="invalid"
            )
            with pytest.raises(ValueError, match="Invalid chunking strategy"):
                config.validate()


class TestGetConfig:
    """Test get_config function."""
    
    def test_get_config_with_env_file(self, temp_directory):
        """Test get_config with environment file."""
        # Create a temporary test file
        test_file = temp_directory / "config_test.pdf"
        test_file.write_text("test content")
        
        env_content = f"""
RAFT_DATAPATH={test_file}
RAFT_OUTPUT=config_output
OPENAI_API_KEY=config-key
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write(env_content)
            env_file = f.name
        
        try:
            # Temporarily remove the environment variable set by the autouse fixture
            original_key = os.environ.pop("OPENAI_API_KEY", None)
            try:
                config = get_config(env_file)
                
                assert str(config.datapath) == str(test_file)
                assert config.output == "config_output"
                assert config.openai_key == "config-key"
            finally:
                # Restore the original environment variable
                if original_key is not None:
                    os.environ["OPENAI_API_KEY"] = original_key
        finally:
            os.unlink(env_file)
    
    def test_get_config_without_env_file(self, temp_directory):
        """Test get_config without environment file."""
        # Create a temporary test file
        test_file = temp_directory / "default_test.pdf"
        test_file.write_text("test content")
        
        env_vars = {
            "RAFT_DATAPATH": str(test_file),
            "RAFT_OUTPUT": "default_output",
            "OPENAI_API_KEY": "default-key"
        }
        
        with patch.dict(os.environ, env_vars):
            config = get_config()
            
            assert str(config.datapath) == str(test_file)
            assert config.output == "default_output"
            assert config.openai_key == "default-key"