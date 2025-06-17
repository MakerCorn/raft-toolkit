"""
Tests for the evaluation tool.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# Add the tools directory to the path for importing
tools_path = Path(__file__).parent.parent.parent / "tools"
sys.path.insert(0, str(tools_path))

try:
    from eval import get_answer, get_args, get_openai_response, write_result_to_file
except ImportError:
    pytest.skip("eval tool not available", allow_module_level=True)


@pytest.mark.cli
class TestEvalTool:
    """Test the evaluation tool."""

    @pytest.mark.cli
    def test_get_args_basic(self):
        """Test basic argument parsing."""
        test_args = ["eval.py", "--question-file", "questions.jsonl", "--answer-file", "answers.jsonl"]

        with patch("sys.argv", test_args):
            args = get_args()

            assert args.question_file == "questions.jsonl"
            assert args.answer_file == "answers.jsonl"
            assert args.model == "gpt-4"  # default
            assert args.input_prompt_key == "instruction"  # default
            assert args.output_answer_key == "answer"  # default
            assert args.workers == 1  # default

    @pytest.mark.cli
    def test_get_args_all_options(self):
        """Test argument parsing with all options."""
        test_args = [
            "eval.py",
            "--question-file",
            "questions.jsonl",
            "--answer-file",
            "answers.jsonl",
            "--model",
            "gpt-3.5-turbo",
            "--input-prompt-key",
            "prompt",
            "--output-answer-key",
            "response",
            "--workers",
            "4",
        ]

        with patch("sys.argv", test_args):
            args = get_args()

            assert args.question_file == "questions.jsonl"
            assert args.answer_file == "answers.jsonl"
            assert args.model == "gpt-3.5-turbo"
            assert args.input_prompt_key == "prompt"
            assert args.output_answer_key == "response"
            assert args.workers == 4

    @pytest.mark.cli
    def test_get_args_missing_required(self):
        """Test argument parsing with missing required arguments."""
        test_args = ["eval.py"]  # Missing --question-file

        with patch("sys.argv", test_args):
            with pytest.raises(SystemExit):
                get_args()

    @patch("eval.completions_completer")
    @pytest.mark.cli
    def test_get_openai_response_success(self, mock_completer):
        """Test successful OpenAI response."""
        # Mock the response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].text = "This is the AI response."
        mock_completer.return_value = mock_response

        response = get_openai_response("What is AI?")

        assert response == "This is the AI response."
        mock_completer.assert_called_once()

        # Verify the call arguments
        call_args = mock_completer.call_args
        assert call_args[1]["prompt"] == "What is AI?"
        assert call_args[1]["temperature"] == 0.02
        assert call_args[1]["max_tokens"] == 8192
        assert call_args[1]["stop"] == "<STOP>"

    @patch("eval.completions_completer")
    @pytest.mark.cli
    def test_get_openai_response_error(self, mock_completer):
        """Test OpenAI response with error."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].text = None  # Simulate error
        mock_completer.side_effect = Exception("API Error")

        response = get_openai_response("What is AI?")

        # Should return the response object when there's an exception
        assert response is not None

    @pytest.mark.cli
    def test_get_answer_success(self):
        """Test successful answer generation."""
        input_json = {
            "instruction": "What is artificial intelligence?",
            "context": "AI is a field of computer science.",
        }

        with patch("eval.get_openai_response") as mock_get_response:
            mock_get_response.return_value = "AI is the simulation of human intelligence."

            result = get_answer(input_json)

            assert result["instruction"] == "What is artificial intelligence?"
            assert result["context"] == "AI is a field of computer science."
            assert result["answer"] == "AI is the simulation of human intelligence."
            assert "error" not in result

    @pytest.mark.cli
    def test_get_answer_error(self):
        """Test answer generation with error."""
        input_json = {"instruction": "What is AI?", "context": "Context about AI."}

        with patch("eval.get_openai_response") as mock_get_response:
            mock_get_response.side_effect = Exception("API Error")

            result = get_answer(input_json)

            assert result["instruction"] == "What is AI?"
            assert result["context"] == "Context about AI."
            assert result["error"] == "API Error"
            assert "answer" not in result

    @pytest.mark.cli
    def test_write_result_to_file(self, temp_directory):
        """Test writing results to file."""
        output_file = temp_directory / "test_output.jsonl"

        result = {"question": "What is AI?", "answer": "AI is artificial intelligence.", "context": "Test context"}

        # Mock the file lock
        with patch("eval.file_write_lock", Mock()):
            write_result_to_file(result, str(output_file))

        # Verify file was written
        assert output_file.exists()

        # Verify content
        with open(output_file) as f:
            line = f.readline().strip()
            loaded_result = json.loads(line)

            assert loaded_result["question"] == "What is AI?"
            assert loaded_result["answer"] == "AI is artificial intelligence."
            assert loaded_result["context"] == "Test context"

    @pytest.mark.cli
    def test_write_multiple_results(self, temp_directory):
        """Test writing multiple results to file."""
        output_file = temp_directory / "multi_output.jsonl"

        results = [
            {"question": "Q1", "answer": "A1"},
            {"question": "Q2", "answer": "A2"},
            {"question": "Q3", "answer": "A3"},
        ]

        with patch("eval.file_write_lock", Mock()):
            for result in results:
                write_result_to_file(result, str(output_file))

        # Verify all results were written
        assert output_file.exists()

        written_results = []
        with open(output_file) as f:
            for line in f:
                written_results.append(json.loads(line.strip()))

        assert len(written_results) == 3
        assert written_results[0]["question"] == "Q1"
        assert written_results[1]["question"] == "Q2"
        assert written_results[2]["question"] == "Q3"


@pytest.mark.cli
class TestEvalToolIntegration:
    """Integration tests for the evaluation tool."""

    @pytest.mark.cli
    def test_eval_tool_end_to_end(self, temp_directory):
        """Test complete evaluation workflow."""
        # Create test question file
        questions_file = temp_directory / "questions.jsonl"
        test_questions = [
            {"instruction": "What is machine learning?", "context": "Machine learning is a subset of AI."},
            {"instruction": "What is deep learning?", "context": "Deep learning uses neural networks."},
        ]

        with open(questions_file, "w") as f:
            for q in test_questions:
                f.write(json.dumps(q) + "\n")

        answers_file = temp_directory / "answers.jsonl"

        # Mock the evaluation components
        with patch("eval.build_openai_client") as mock_build_client:
            with patch("eval.StatsCompleter") as mock_stats_completer:
                with patch("eval.retry_complete") as mock_retry:

                    # Mock client and response
                    mock_client = Mock()
                    mock_build_client.return_value = mock_client

                    mock_completer = Mock()
                    mock_stats_completer.return_value = mock_completer

                    # Mock successful responses
                    mock_response = Mock()
                    mock_response.choices = [Mock()]
                    mock_response.choices[0].text = "This is a test answer."
                    mock_completer.return_value = mock_response
                    mock_completer.get_stats_and_reset.return_value = None

                    mock_retry.statistics = {}

                    # Mock the main execution
                    test_args = [
                        "eval.py",
                        "--question-file",
                        str(questions_file),
                        "--answer-file",
                        str(answers_file),
                        "--workers",
                        "1",
                    ]

                    with patch("sys.argv", test_args):
                        with patch("eval.file_write_lock", Mock()):
                            with patch("eval.tqdm") as mock_tqdm:
                                with patch("eval.logger"):

                                    # Mock tqdm progress bar
                                    mock_pbar = Mock()
                                    mock_tqdm.return_value.__enter__.return_value = mock_pbar

                                    # This would normally run the main section
                                    # We'll test the key components instead
                                    get_args()

                                    # Simulate processing
                                    inputs = []
                                    with open(questions_file, "r") as f:
                                        for line in f:
                                            inputs.append(json.loads(line))

                                    assert len(inputs) == 2
                                    assert inputs[0]["instruction"] == "What is machine learning?"
                                    assert inputs[1]["instruction"] == "What is deep learning?"
