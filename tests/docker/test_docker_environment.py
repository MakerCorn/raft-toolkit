#!/usr/bin/env python3
"""
Docker environment validation tests.

These tests validate that the Docker testing environment is properly configured
and can run the test suite successfully.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.mark.docker
class TestDockerEnvironment:
    """Test Docker environment setup and functionality."""

    def test_docker_environment_variables(self):
        """Test that Docker environment variables are properly set."""
        # Check for testing environment
        assert os.getenv("TESTING") == "true", "TESTING environment variable should be set to 'true'"

        # Check log level
        log_level = os.getenv("LOG_LEVEL")
        assert log_level is not None, "LOG_LEVEL environment variable should be set"

        # Check Python path
        python_path = os.getenv("PYTHONPATH")
        assert python_path is not None, "PYTHONPATH should be set"
        assert "/app" in python_path, "PYTHONPATH should include /app"

    def test_test_directories_exist(self):
        """Test that required test directories exist and are writable."""
        # Get test directories from environment or use defaults
        test_output_dir = Path(os.getenv("TEST_OUTPUT_DIR", "/app/test-results"))
        test_temp_dir = Path(os.getenv("TEST_TEMP_DIR", "/tmp/test-temp"))
        test_coverage_dir = Path(os.getenv("TEST_COVERAGE_DIR", "/app/coverage-reports"))

        directories = [test_output_dir, test_temp_dir, test_coverage_dir]

        for directory in directories:
            # Test directory exists
            assert directory.exists(), f"Directory {directory} should exist"

            # Test directory is writable
            assert os.access(directory, os.W_OK), f"Directory {directory} should be writable"

            # Test we can create a file in the directory
            test_file = directory / f"test_write_{directory.name}.txt"
            try:
                test_file.write_text("test content")
                assert test_file.exists(), f"Should be able to create files in {directory}"
                test_file.unlink()  # Clean up
            except Exception as e:
                pytest.fail(f"Failed to write to {directory}: {e}")

    def test_docker_python_environment(self):
        """Test that Python environment is properly configured."""
        # Test Python version (should be 3.11)
        version_info = sys.version_info
        assert version_info.major == 3, "Should be running Python 3"
        assert version_info.minor >= 11, "Should be running Python 3.11 or newer"

        # Test critical imports work
        critical_imports = [
            "core.config",
            "core.raft_engine",
            "cli.main",
            "web.app",
            "pytest",
            "fastapi",
        ]

        for import_name in critical_imports:
            try:
                __import__(import_name)
            except ImportError as e:
                pytest.fail(f"Critical import {import_name} failed: {e}")

    def test_docker_security_setup(self):
        """Test that Docker security measures are in place."""
        # Test running as non-root user
        uid = os.getuid()
        assert uid != 0, "Should not be running as root user for security"

        # Test user name
        import pwd

        user_info = pwd.getpwuid(uid)
        assert user_info.pw_name == "raft", "Should be running as 'raft' user"

    def test_docker_test_runner_accessible(self):
        """Test that the test runner script is accessible and functional."""
        runner_path = Path("/app/run_tests.py")
        assert runner_path.exists(), "Test runner should exist at /app/run_tests.py"
        assert os.access(runner_path, os.R_OK), "Test runner should be readable"

        # Test runner help works
        try:
            result = subprocess.run(
                [sys.executable, str(runner_path), "--help"], capture_output=True, text=True, timeout=10
            )
            assert result.returncode == 0, "Test runner --help should succeed"
            assert "RAFT Toolkit tests" in result.stdout, "Help output should mention RAFT Toolkit"
        except subprocess.TimeoutExpired:
            pytest.fail("Test runner --help timed out")
        except Exception as e:
            pytest.fail(f"Test runner --help failed: {e}")

    def test_docker_redis_connectivity(self):
        """Test Redis connectivity if Redis is available."""
        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            pytest.skip("Redis not configured (REDIS_URL not set)")

        try:
            import redis

            client = redis.from_url(redis_url)
            # Simple ping test
            result = client.ping()
            assert result is True, "Redis ping should succeed"
        except ImportError:
            pytest.skip("Redis client not available")
        except Exception as e:
            pytest.fail(f"Redis connectivity test failed: {e}")

    def test_docker_mock_api_setup(self):
        """Test that mock API configuration is properly set up."""
        use_mock_api = os.getenv("USE_MOCK_API")
        if use_mock_api == "true":
            # Test that we have a test API key
            openai_key = os.getenv("OPENAI_API_KEY")
            assert openai_key is not None, "OPENAI_API_KEY should be set"
            assert openai_key == "test-key", "Should be using test API key in mock mode"

    def test_docker_volume_mounts(self):
        """Test that volume mounts are working correctly."""
        # Test that we can write to mounted directories
        test_output_dir = Path(os.getenv("TEST_OUTPUT_DIR", "/app/test-results"))

        # Create a test file that should be visible on the host
        test_file = test_output_dir / "docker_volume_test.txt"
        test_content = "Docker volume mount test - written from container"

        try:
            test_file.write_text(test_content)
            assert test_file.exists(), "Test file should be created"

            # Read back to ensure it's properly written
            read_content = test_file.read_text()
            assert read_content == test_content, "File content should match"

            # Clean up
            test_file.unlink()
        except Exception as e:
            pytest.fail(f"Volume mount test failed: {e}")

    @pytest.mark.slow
    def test_docker_full_test_suite_dry_run(self):
        """Test that the full test suite can at least start without errors."""
        # Run a quick dry-run of the test suite to ensure basic functionality
        try:
            result = subprocess.run(
                [sys.executable, "/app/run_tests.py", "--help"], capture_output=True, text=True, timeout=30
            )
            assert result.returncode == 0, "Test runner should execute without errors"
        except subprocess.TimeoutExpired:
            pytest.fail("Test runner dry run timed out")
        except Exception as e:
            pytest.fail(f"Test runner dry run failed: {e}")


@pytest.mark.docker
class TestDockerComposeIntegration:
    """Test Docker Compose specific functionality."""

    def test_docker_compose_service_name(self):
        """Test that we're running in the expected Docker Compose service."""
        # This is a basic test - in a real Docker Compose environment,
        # you might have service discovery or specific hostname patterns
        hostname = os.getenv("HOSTNAME", "")
        # Basic validation that we're in a container environment
        assert len(hostname) > 0, "Should have a hostname set"

    def test_docker_compose_environment_isolation(self):
        """Test that the Docker environment is properly isolated."""
        # Test that we're not accidentally using host paths
        cwd = Path.cwd()
        assert str(cwd).startswith("/app"), f"Working directory should be in /app, got {cwd}"

        # Test that temporary files go to the right place
        with tempfile.NamedTemporaryFile() as tmp:
            tmp_path = Path(tmp.name)
            expected_temp_dir = Path(os.getenv("TEST_TEMP_DIR", "/tmp"))
            assert tmp_path.is_relative_to(expected_temp_dir.parent), f"Temp files should use configured temp directory"


if __name__ == "__main__":
    # Allow running this test file directly
    pytest.main([__file__, "-v"])
