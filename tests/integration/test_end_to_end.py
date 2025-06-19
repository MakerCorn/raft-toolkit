"""
End-to-end integration tests.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from raft_toolkit.core.config import RaftConfig
from raft_toolkit.core.raft_engine import RaftEngine


@pytest.mark.integration
class TestEndToEnd:
    """Test complete end-to-end workflows."""

    @pytest.fixture
    def test_pdf_content(self):
        """Create test PDF content."""
        return "This is a test document about artificial intelligence. AI is transforming many industries."

    @pytest.fixture
    def test_json_content(self):
        """Create test JSON content."""
        return {
            "text": "Machine learning is a subset of artificial intelligence. It enables computers to learn without being explicitly programmed."
        }

    @pytest.fixture
    def test_api_content(self):
        """Create test API content."""
        return [
            {
                "user_name": "test_user",
                "api_name": "get_weather",
                "api_call": "GET /weather",
                "api_version": "v1",
                "api_arguments": {"location": "string"},
                "functionality": "Get current weather for a location",
            }
        ]

    def test_pdf_processing_workflow(self, test_pdf_content, tmp_path):
        """Test complete PDF processing workflow."""
        # Create test PDF file
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text(test_pdf_content)

        # Create output directory
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Configure RAFT
        config = RaftConfig(
            datapath=pdf_file,
            output=str(output_dir / "dataset.jsonl"),
            openai_key="demo_key_for_testing",
            doctype="pdf",
            chunk_size=100,
            questions=2,
            distractors=1,
            chunking_strategy="fixed",
        )

        # Mock external dependencies
        with (
            patch("raft_toolkit.core.services.llm_service.ChatCompleter") as mock_completer,
            patch("raft_toolkit.core.services.llm_service.build_openai_client"),
            patch("raft_toolkit.core.services.document_service.pypdf") as mock_pypdf,
        ):

            # Mock PDF reading
            mock_reader = Mock()
            mock_page = Mock()
            mock_page.extract_text.return_value = test_pdf_content
            mock_reader.pages = [mock_page]
            mock_pypdf.PdfReader.return_value = mock_reader

            # Mock LLM responses
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "What is AI?\nHow does AI work?"
            mock_completer_instance = Mock()
            mock_completer_instance.return_value = mock_response
            mock_completer_instance.get_stats_and_reset.return_value = Mock(
                prompt_tokens=50, completion_tokens=25, total_tokens=75
            )
            mock_completer.return_value = mock_completer_instance

            # Create and run engine
            engine = RaftEngine(config)

            # Test preview
            preview = engine.get_processing_preview(pdf_file)
            assert "estimated_chunks" in preview
            assert "estimated_qa_points" in preview

            # Test validation
            engine.validate_inputs(pdf_file)

            # Test dataset generation
            stats = engine.generate_dataset(pdf_file, config.output)

            assert "total_qa_points" in stats
            assert "successful_chunks" in stats
            assert stats["successful_chunks"] > 0

    def test_json_processing_workflow(self, test_json_content, tmp_path):
        """Test complete JSON processing workflow."""
        # Create test JSON file
        json_file = tmp_path / "test.json"
        with open(json_file, "w") as f:
            json.dump(test_json_content, f)

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        config = RaftConfig(
            datapath=json_file,
            output=str(output_dir / "dataset.jsonl"),
            openai_key="demo_key_for_testing",
            doctype="json",
            chunk_size=50,
            questions=1,
            distractors=0,
            chunking_strategy="fixed",
        )

        with (
            patch("raft_toolkit.core.services.llm_service.ChatCompleter") as mock_completer,
            patch("raft_toolkit.core.services.llm_service.build_openai_client"),
        ):

            # Mock LLM responses
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "What is machine learning?"
            mock_completer_instance = Mock()
            mock_completer_instance.return_value = mock_response
            mock_completer_instance.get_stats_and_reset.return_value = Mock(
                prompt_tokens=30, completion_tokens=15, total_tokens=45
            )
            mock_completer.return_value = mock_completer_instance

            engine = RaftEngine(config)
            stats = engine.generate_dataset(json_file, config.output)

            assert stats["total_qa_points"] >= 0

    def test_api_processing_workflow(self, test_api_content, tmp_path):
        """Test complete API processing workflow."""
        # Create test API file
        api_file = tmp_path / "test.json"
        with open(api_file, "w") as f:
            json.dump(test_api_content, f)

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        config = RaftConfig(
            datapath=api_file,
            output=str(output_dir / "dataset.jsonl"),
            openai_key="demo_key_for_testing",
            doctype="api",
            questions=1,
            distractors=0,
        )

        with (
            patch("raft_toolkit.core.services.llm_service.ChatCompleter") as mock_completer,
            patch("raft_toolkit.core.services.llm_service.build_openai_client"),
        ):

            # Mock LLM responses for API
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "How to get weather data?"
            mock_completer_instance = Mock()
            mock_completer_instance.return_value = mock_response
            mock_completer_instance.get_stats_and_reset.return_value = Mock(
                prompt_tokens=40, completion_tokens=20, total_tokens=60
            )
            mock_completer.return_value = mock_completer_instance

            engine = RaftEngine(config)
            stats = engine.generate_dataset(api_file, config.output)

            assert stats["total_qa_points"] >= 0

    def test_different_output_formats(self, test_json_content, tmp_path):
        """Test different output formats."""
        json_file = tmp_path / "test.json"
        with open(json_file, "w") as f:
            json.dump(test_json_content, f)

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        formats = ["hf", "completion", "chat", "eval"]

        for output_format in formats:
            config = RaftConfig(
                datapath=json_file,
                output=str(output_dir / f"dataset_{output_format}.jsonl"),
                openai_key="demo_key_for_testing",
                doctype="json",
                output_format=output_format,
                chunk_size=50,
                questions=1,
                distractors=0,
            )

            with (
                patch("raft_toolkit.core.services.llm_service.ChatCompleter") as mock_completer,
                patch("raft_toolkit.core.services.llm_service.build_openai_client"),
            ):

                mock_response = Mock()
                mock_response.choices = [Mock()]
                mock_response.choices[0].message.content = "Test question?"
                mock_completer_instance = Mock()
                mock_completer_instance.return_value = mock_response
                mock_completer_instance.get_stats_and_reset.return_value = Mock(
                    prompt_tokens=20, completion_tokens=10, total_tokens=30
                )
                mock_completer.return_value = mock_completer_instance

                engine = RaftEngine(config)
                stats = engine.generate_dataset(json_file, config.output)

                assert stats["total_qa_points"] >= 0

                # Verify output file exists
                output_file = Path(config.output)
                if stats["total_qa_points"] > 0:
                    assert output_file.exists()

    def test_error_handling(self, tmp_path):
        """Test error handling in end-to-end workflow."""
        # Test with nonexistent file
        config = RaftConfig(
            datapath=Path("nonexistent.pdf"), output=str(tmp_path / "output.jsonl"), openai_key="demo_key_for_testing"
        )

        engine = RaftEngine(config)

        with pytest.raises(FileNotFoundError):
            engine.validate_inputs(Path("nonexistent.pdf"))

    def test_chunking_strategies(self, test_json_content, tmp_path):
        """Test different chunking strategies."""
        json_file = tmp_path / "test.json"
        with open(json_file, "w") as f:
            json.dump(test_json_content, f)

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        strategies = ["fixed", "sentence"]

        for strategy in strategies:
            config = RaftConfig(
                datapath=json_file,
                output=str(output_dir / f"dataset_{strategy}.jsonl"),
                openai_key="demo_key_for_testing",
                doctype="json",
                chunking_strategy=strategy,
                chunk_size=30,
                questions=1,
                distractors=0,
            )

            with (
                patch("raft_toolkit.core.services.llm_service.ChatCompleter") as mock_completer,
                patch("raft_toolkit.core.services.llm_service.build_openai_client"),
            ):

                mock_response = Mock()
                mock_response.choices = [Mock()]
                mock_response.choices[0].message.content = "Test question?"
                mock_completer_instance = Mock()
                mock_completer_instance.return_value = mock_response
                mock_completer_instance.get_stats_and_reset.return_value = Mock(
                    prompt_tokens=15, completion_tokens=8, total_tokens=23
                )
                mock_completer.return_value = mock_completer_instance

                engine = RaftEngine(config)
                stats = engine.generate_dataset(json_file, config.output)

                assert "chunking_strategy" in stats["config_used"]
                assert stats["config_used"]["chunking_strategy"] == strategy
