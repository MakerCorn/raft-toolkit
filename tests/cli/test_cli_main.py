"""
Tests for CLI main module.
"""

import json
import sys
import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from cli.main import create_parser, main, override_config_from_args, show_preview, validate_only
from core.config import RaftConfig
from core.raft_engine import RaftEngine


@pytest.mark.cli
class TestCreateParser:
    """Test CLI argument parser creation."""

    @pytest.mark.cli
    def test_parser_creation(self):
        """Test basic parser creation."""
        parser = create_parser()

        assert parser is not None
        assert parser.description is not None
        assert "RAFT" in parser.description

    @pytest.mark.cli
    def test_required_arguments(self):
        """Test argument parsing."""
        parser = create_parser()

        # Test with no arguments (should work with defaults)
        args = parser.parse_args([])
        assert args.source_type == "local"  # default
        assert args.output == "./raft_output"  # default

        # Test with datapath argument
        args = parser.parse_args(["--datapath", "test.pdf"])
        assert args.datapath == Path("test.pdf")

    @pytest.mark.cli
    def test_default_values(self):
        """Test default argument values."""
        parser = create_parser()
        args = parser.parse_args(["--datapath", "test.pdf"])

        assert args.output == "./raft_output"
        assert args.output_format == "hf"
        assert args.output_type == "jsonl"
        assert args.distractors == 1
        assert args.p == 1.0
        assert args.questions == 5
        assert args.chunk_size == 512
        assert args.doctype == "pdf"
        assert args.chunking_strategy == "semantic"
        assert args.embedding_model == "nomic-embed-text"
        assert args.completion_model == "llama3.2"
        assert args.workers == 1
        assert args.embed_workers == 1
        assert args.pace is True

    @pytest.mark.cli
    def test_all_arguments(self):
        """Test parsing all arguments."""
        parser = create_parser()
        args = parser.parse_args(
            [
                "--datapath",
                "input.pdf",
                "--output",
                "custom_output",
                "--output-format",
                "completion",
                "--output-type",
                "parquet",
                "--output-chat-system-prompt",
                "Custom system prompt",
                "--distractors",
                "3",
                "--p",
                "0.8",
                "--questions",
                "10",
                "--chunk_size",
                "1024",
                "--doctype",
                "txt",
                "--chunking-strategy",
                "fixed",
                "--chunking-params",
                '{"overlap": 50}',
                "--openai_key",
                "test-key",
                "--embedding_model",
                "custom-embedding",
                "--completion_model",
                "gpt-4",
                "--workers",
                "4",
                "--embed-workers",
                "2",
                "--templates",
                "./custom_templates",
                "--use-azure-identity",
                "--auto-clean-checkpoints",
                "--preview",
                "--validate",
                "--env-file",
                ".custom.env",
            ]
        )

        assert args.datapath == Path("input.pdf")
        assert args.output == "custom_output"
        assert args.output_format == "completion"
        assert args.output_type == "parquet"
        assert args.output_chat_system_prompt == "Custom system prompt"
        assert args.distractors == 3
        assert args.p == 0.8
        assert args.questions == 10
        assert args.chunk_size == 1024
        assert args.doctype == "txt"
        assert args.chunking_strategy == "fixed"
        assert args.chunking_params == '{"overlap": 50}'
        assert args.openai_key == "test-key"
        assert args.embedding_model == "custom-embedding"
        assert args.completion_model == "gpt-4"
        assert args.workers == 4
        assert args.embed_workers == 2
        assert args.templates == "./custom_templates"
        assert args.use_azure_identity is True
        assert args.auto_clean_checkpoints is True
        assert args.preview is True
        assert args.validate is True
        assert args.env_file == ".custom.env"


@pytest.mark.cli
class TestOverrideConfigFromArgs:
    """Test configuration override from CLI arguments."""

    @pytest.mark.cli
    def test_override_basic_args(self, sample_config):
        """Test overriding basic configuration arguments."""
        parser = create_parser()
        args = parser.parse_args(
            [
                "--datapath",
                "new_input.pdf",
                "--output",
                "new_output",
                "--output-format",
                "chat",
                "--questions",
                "8",
                "--chunk_size",
                "256",
            ]
        )

        updated_config = override_config_from_args(sample_config, args)

        assert updated_config.datapath == Path("new_input.pdf")
        assert updated_config.output == "new_output"
        assert updated_config.output_format == "chat"
        assert updated_config.questions == 8
        assert updated_config.chunk_size == 256

    @pytest.mark.cli
    def test_override_only_changed_values(self, sample_config):
        """Test that only non-default values are overridden."""
        parser = create_parser()
        args = parser.parse_args(
            [
                "--datapath",
                "test.pdf",
                # Use default values for other args
            ]
        )

        original_output = sample_config.output
        updated_config = override_config_from_args(sample_config, args)

        # Should not override with default value
        assert updated_config.output == original_output
        assert updated_config.datapath == Path("test.pdf")  # This should be updated

    @pytest.mark.cli
    def test_override_chunking_params(self, sample_config):
        """Test overriding chunking parameters."""
        parser = create_parser()
        args = parser.parse_args(
            ["--datapath", "test.pdf", "--chunking-params", '{"overlap": 100, "min_chunk_size": 50}']
        )

        updated_config = override_config_from_args(sample_config, args)

        assert updated_config.chunking_params["overlap"] == 100
        assert updated_config.chunking_params["min_chunk_size"] == 50

    @pytest.mark.cli
    def test_invalid_chunking_params_json(self, sample_config, capsys):
        """Test handling invalid JSON in chunking params."""
        parser = create_parser()
        args = parser.parse_args(["--datapath", "test.pdf", "--chunking-params", "invalid json"])

        with pytest.raises(SystemExit):
            override_config_from_args(sample_config, args)


@pytest.mark.cli
class TestShowPreview:
    """Test preview functionality."""

    @pytest.mark.cli
    def test_show_preview_success(self, capsys):
        """Test successful preview display."""
        mock_engine = Mock(spec=RaftEngine)
        mock_config = Mock()
        mock_config.questions = 5
        mock_config.distractors = 2
        mock_config.source_type = "local"
        mock_config.datapath = "/test/path"
        mock_config.chunking_strategy = "semantic"
        mock_engine.config = mock_config

        mock_preview = {
            "input_path": "/test/path",
            "doctype": "pdf",
            "files_to_process": ["file1.pdf", "file2.pdf"],
            "estimated_chunks": 10,
            "estimated_qa_points": 50,
        }
        mock_engine.get_processing_preview.return_value = mock_preview

        show_preview(mock_engine, mock_config)

        captured = capsys.readouterr()
        assert "RAFT PROCESSING PREVIEW" in captured.out
        assert "/test/path" in captured.out
        assert "pdf" in captured.out
        assert "10" in captured.out  # estimated chunks
        assert "50" in captured.out  # estimated QA points
        assert "file1.pdf" in captured.out
        assert "file2.pdf" in captured.out

    @pytest.mark.cli
    def test_show_preview_many_files(self, capsys):
        """Test preview with many files (truncation)."""
        mock_engine = Mock(spec=RaftEngine)
        mock_config = Mock()
        mock_config.questions = 3
        mock_config.distractors = 1
        mock_config.source_type = "local"
        mock_config.datapath = "/test/path"
        mock_config.chunking_strategy = "semantic"
        mock_engine.config = mock_config

        # Create many files to test truncation
        many_files = [f"file{i}.pdf" for i in range(10)]
        mock_preview = {
            "input_path": "/test/path",
            "doctype": "pdf",
            "files_to_process": many_files,
            "estimated_chunks": 20,
            "estimated_qa_points": 60,
        }
        mock_engine.get_processing_preview.return_value = mock_preview

        show_preview(mock_engine, mock_config)

        captured = capsys.readouterr()
        assert "file0.pdf" in captured.out
        assert "file1.pdf" in captured.out
        assert "file2.pdf" in captured.out
        assert "... and 7 more files" in captured.out

    @pytest.mark.cli
    def test_show_preview_error(self, capsys):
        """Test preview with engine error."""
        mock_engine = Mock(spec=RaftEngine)
        mock_config = Mock()
        mock_config.source_type = "local"
        mock_config.datapath = "/test/path"
        mock_engine.get_processing_preview.side_effect = Exception("Preview error")

        with pytest.raises(SystemExit):
            show_preview(mock_engine, mock_config)


@pytest.mark.cli
class TestValidateOnly:
    """Test validation-only functionality."""

    @pytest.mark.cli
    def test_validate_only_success(self, capsys):
        """Test successful validation."""
        mock_engine = Mock(spec=RaftEngine)
        mock_config = Mock()
        mock_config.source_type = "local"
        mock_config.datapath = "/test/input"
        mock_config.output = "/test/output"
        mock_config.doctype = "pdf"
        mock_config.output_format = "hf"
        mock_config.output_type = "jsonl"
        mock_engine.config = mock_config
        mock_engine.validate_inputs.return_value = None  # No exception

        validate_only(mock_engine, mock_config)

        captured = capsys.readouterr()
        assert "Configuration and inputs are valid!" in captured.out
        assert "/test/input" in captured.out
        assert "/test/output" in captured.out
        assert "pdf" in captured.out
        assert "hf" in captured.out

    @pytest.mark.cli
    def test_validate_only_error(self, capsys):
        """Test validation with error."""
        mock_engine = Mock(spec=RaftEngine)
        mock_config = Mock()
        mock_config.source_type = "local"
        mock_config.datapath = "/test/input"
        mock_engine.validate_inputs.side_effect = ValueError("Validation failed")

        with pytest.raises(SystemExit):
            validate_only(mock_engine, mock_config)


@pytest.mark.cli
class TestMainFunction:
    """Test main CLI function."""

    @pytest.mark.cli
    def test_main_preview_mode(self, temp_directory):
        """Test main function in preview mode."""
        test_file = temp_directory / "test.pdf"
        test_file.write_text("test content")

        test_args = ["raft.py", "--datapath", str(test_file), "--preview"]

        with patch("sys.argv", test_args):
            with patch("cli.main.get_config") as mock_get_config:
                with patch("cli.main.RaftEngine") as mock_engine_class:
                    with patch("cli.main.show_preview") as mock_show_preview:

                        mock_config = Mock()
                        mock_config.source_type = "local"
                        mock_config.datapath = test_file
                        mock_config.source_uri = str(test_file)
                        mock_config.sentry_dsn = None
                        mock_get_config.return_value = mock_config

                        mock_engine = Mock()
                        mock_engine_class.return_value = mock_engine

                        main()

                        mock_show_preview.assert_called_once()
                        # Check that show_preview was called with the engine and config
                        call_args = mock_show_preview.call_args[0]
                        assert len(call_args) == 2  # engine and config
                        assert call_args[0] == mock_engine  # First argument should be engine
                        assert call_args[1] == mock_config  # Second argument should be config

    @pytest.mark.cli
    def test_main_validate_mode(self, temp_directory):
        """Test main function in validate mode."""
        test_file = temp_directory / "test.pdf"
        test_file.write_text("test content")

        test_args = ["raft.py", "--datapath", str(test_file), "--validate"]

        with patch("sys.argv", test_args):
            with patch("cli.main.get_config") as mock_get_config:
                with patch("cli.main.RaftEngine") as mock_engine_class:
                    with patch("cli.main.validate_only") as mock_validate:

                        mock_config = Mock()
                        mock_config.source_type = "local"
                        mock_config.datapath = test_file
                        mock_config.sentry_dsn = None
                        mock_get_config.return_value = mock_config

                        mock_engine = Mock()
                        mock_engine_class.return_value = mock_engine

                        main()

                        mock_validate.assert_called_once()

    @pytest.mark.cli
    def test_main_normal_processing(self, temp_directory, capsys):
        """Test main function in normal processing mode."""
        test_file = temp_directory / "test.pdf"
        test_file.write_text("test content")
        output_dir = temp_directory / "output"

        test_args = ["raft.py", "--datapath", str(test_file), "--output", str(output_dir)]

        with patch("sys.argv", test_args):
            with patch("cli.main.get_config") as mock_get_config:
                with patch("cli.main.RaftEngine") as mock_engine_class:
                    with patch("cli.main.get_logger") as mock_get_logger:
                        with patch("cli.main.log_setup"):

                            mock_config = Mock()
                            mock_config.source_type = "local"
                            mock_config.datapath = test_file
                            mock_config.output = str(output_dir)
                            mock_config.doctype = "pdf"
                            mock_config.chunking_strategy = "semantic"
                            mock_config.completion_model = "gpt-4"
                            mock_config.sentry_dsn = None
                            mock_get_config.return_value = mock_config

                            # Mock logger with all required methods
                            mock_logger = Mock()
                            mock_logger.set_context = Mock()
                            mock_logger.set_progress = Mock()
                            mock_logger.info = Mock()
                            mock_logger.start_operation = Mock()
                            mock_logger.add_trace_event = Mock()
                            mock_logger.end_operation = Mock()
                            mock_logger.error = Mock()
                            mock_get_logger.return_value = mock_logger

                            mock_engine = Mock()
                            mock_engine.validate_inputs.return_value = None
                            mock_engine.generate_dataset.return_value = {
                                "total_qa_points": 10,
                                "successful_chunks": 5,
                                "failed_chunks": 0,
                                "avg_time_per_chunk": 2.5,
                                "token_usage": {"tokens_per_second": 50.0, "total_tokens": 1000},
                            }

                            # Make async methods return coroutines
                            async def mock_validate_input_source():
                                return None

                            mock_engine.validate_input_source = mock_validate_input_source
                            mock_engine_class.return_value = mock_engine

                            main()

                            # Verify processing was called
                            mock_engine.validate_inputs.assert_called_once_with(test_file)
                            mock_engine.generate_dataset.assert_called_once_with(test_file, str(output_dir))

                            # Verify output
                            captured = capsys.readouterr()
                            assert "RAFT GENERATION COMPLETED" in captured.out
                            assert "Total QA Points Generated: 10" in captured.out
                            assert "Successful Chunks: 5" in captured.out

    @pytest.mark.cli
    def test_main_keyboard_interrupt(self, temp_directory, capsys):
        """Test main function with keyboard interrupt."""
        test_file = temp_directory / "test.pdf"
        test_file.write_text("test content")

        test_args = ["raft.py", "--datapath", str(test_file)]

        with patch("sys.argv", test_args):
            with patch("cli.main.get_config") as mock_get_config:
                with patch("cli.main.RaftEngine") as mock_engine_class:

                    mock_config = Mock()
                    mock_get_config.return_value = mock_config

                    mock_engine = Mock()
                    mock_engine.validate_inputs.side_effect = KeyboardInterrupt()
                    mock_engine_class.return_value = mock_engine

                    with pytest.raises(SystemExit):
                        main()

    @pytest.mark.cli
    def test_main_general_error(self, temp_directory):
        """Test main function with general error."""
        test_file = temp_directory / "test.pdf"
        test_file.write_text("test content")

        test_args = ["raft.py", "--datapath", str(test_file)]

        with patch("sys.argv", test_args):
            with patch("cli.main.get_config") as mock_get_config:
                with patch("cli.main.RaftEngine") as mock_engine_class:

                    mock_config = Mock()
                    mock_get_config.return_value = mock_config

                    mock_engine = Mock()
                    mock_engine.validate_inputs.side_effect = ValueError("Test error")
                    mock_engine_class.return_value = mock_engine

                    with pytest.raises(SystemExit):
                        main()

    @pytest.mark.cli
    def test_main_with_env_file(self, temp_directory):
        """Test main function with custom env file."""
        test_file = temp_directory / "test.pdf"
        test_file.write_text("test content")
        env_file = temp_directory / "custom.env"
        env_file.write_text("OPENAI_API_KEY=test-key")

        test_args = ["raft.py", "--datapath", str(test_file), "--env-file", str(env_file), "--preview"]

        with patch("sys.argv", test_args):
            with patch("cli.main.get_config") as mock_get_config:
                with patch("cli.main.RaftEngine") as mock_engine_class:
                    with patch("cli.main.show_preview"):

                        mock_config = Mock()
                        mock_config.source_type = "local"
                        mock_config.datapath = test_file
                        mock_config.sentry_dsn = None
                        mock_get_config.return_value = mock_config
                        mock_engine_class.return_value = Mock()

                        main()

                        # Verify get_config was called with the env file
                        mock_get_config.assert_called_once_with(str(env_file))
