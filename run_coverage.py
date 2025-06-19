#!/usr/bin/env python3
"""
Simple test coverage runner.
"""

import subprocess
import sys


def run_tests_with_coverage():
    """Run tests with coverage reporting."""
    try:
        # Install required packages
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "pytest", "pytest-cov", "pytest-mock", "pytest-asyncio"],
            check=True,
        )

        # Run tests with coverage
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "--cov=raft_toolkit",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            "tests/",
            "-v",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        print("STDOUT:")
        print(result.stdout)

        if result.stderr:
            print("STDERR:")
            print(result.stderr)

        return result.returncode == 0

    except subprocess.CalledProcessError as e:
        print(f"Error running tests: {e}")
        return False


if __name__ == "__main__":
    success = run_tests_with_coverage()
    sys.exit(0 if success else 1)
