#!/usr/bin/env python3
"""
Docker test validation script.

This script validates that the Docker testing environment is working correctly
and can run the RAFT Toolkit test suite.

Usage:
    python scripts/test_docker.py                  # Test Docker environment only
    python scripts/test_docker.py --full          # Run full test suite in Docker
    python scripts/test_docker.py --build         # Build Docker image first
    python scripts/test_docker.py --clean         # Clean up Docker resources
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional


class DockerTestRunner:
    """Docker test environment validator."""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent.parent
        self.compose_file = self.project_root / "docker-compose.test.yml"
        self.dockerfile = self.project_root / "Dockerfile"

    def check_docker_available(self) -> bool:
        """Check if Docker is available and running."""
        try:
            result = subprocess.run(["docker", "--version"], capture_output=True, text=True, check=False)
            if result.returncode != 0:
                print("❌ Docker is not available")
                return False

            print(f"✅ Docker available: {result.stdout.strip()}")

            # Check if Docker daemon is running
            result = subprocess.run(["docker", "info"], capture_output=True, text=True, check=False)
            if result.returncode != 0:
                print("❌ Docker daemon is not running")
                return False

            print("✅ Docker daemon is running")
            return True

        except FileNotFoundError:
            print("❌ Docker command not found")
            return False

    def check_docker_compose_available(self) -> bool:
        """Check if Docker Compose is available."""
        try:
            result = subprocess.run(["docker", "compose", "version"], capture_output=True, text=True, check=False)
            if result.returncode != 0:
                # Try legacy docker-compose
                result = subprocess.run(["docker-compose", "--version"], capture_output=True, text=True, check=False)
                if result.returncode != 0:
                    print("❌ Docker Compose is not available")
                    return False
                print(f"✅ Docker Compose available: {result.stdout.strip()}")
                return True

            print(f"✅ Docker Compose available: {result.stdout.strip()}")
            return True

        except FileNotFoundError:
            print("❌ Docker Compose command not found")
            return False

    def check_required_files(self) -> bool:
        """Check if required Docker files exist."""
        required_files = [
            self.dockerfile,
            self.compose_file,
            self.project_root / "requirements.txt",
            self.project_root / "run_tests.py",
        ]

        missing_files = []
        for file_path in required_files:
            if not file_path.exists():
                missing_files.append(str(file_path))

        if missing_files:
            print("❌ Missing required files:")
            for file_path in missing_files:
                print(f"   - {file_path}")
            return False

        print("✅ All required Docker files present")
        return True

    def build_docker_image(self) -> bool:
        """Build the Docker test image."""
        print("🔨 Building Docker test image...")

        try:
            result = subprocess.run(
                ["docker", "compose", "-f", str(self.compose_file), "build", "raft-test"],
                cwd=self.project_root,
                check=False,
            )

            if result.returncode != 0:
                print("❌ Failed to build Docker test image")
                return False

            print("✅ Docker test image built successfully")
            return True

        except Exception as e:
            print(f"❌ Error building Docker image: {e}")
            return False

    def run_docker_environment_tests(self) -> bool:
        """Run Docker environment validation tests."""
        print("🧪 Running Docker environment tests...")

        try:
            result = subprocess.run(
                [
                    "docker",
                    "compose",
                    "-f",
                    str(self.compose_file),
                    "run",
                    "--rm",
                    "raft-test",
                    "python",
                    "-m",
                    "pytest",
                    "tests/docker/",
                    "-v",
                    "--tb=short",
                ],
                cwd=self.project_root,
                check=False,
            )

            if result.returncode != 0:
                print("❌ Docker environment tests failed")
                return False

            print("✅ Docker environment tests passed")
            return True

        except Exception as e:
            print(f"❌ Error running Docker environment tests: {e}")
            return False

    def run_full_test_suite(self) -> bool:
        """Run the full test suite in Docker."""
        print("🧪 Running full test suite in Docker...")

        try:
            result = subprocess.run(
                [
                    "docker",
                    "compose",
                    "-f",
                    str(self.compose_file),
                    "run",
                    "--rm",
                    "raft-test",
                    "python",
                    "run_tests.py",
                    "--coverage",
                    "--fast",  # Skip slow tests for Docker validation
                ],
                cwd=self.project_root,
                check=False,
            )

            if result.returncode != 0:
                print("❌ Full test suite failed in Docker")
                return False

            print("✅ Full test suite passed in Docker")
            return True

        except Exception as e:
            print(f"❌ Error running full test suite: {e}")
            return False

    def clean_docker_resources(self) -> bool:
        """Clean up Docker resources."""
        print("🧹 Cleaning up Docker resources...")

        try:
            # Stop and remove containers
            subprocess.run(
                ["docker", "compose", "-f", str(self.compose_file), "down", "-v"], cwd=self.project_root, check=False
            )

            # Remove test image
            subprocess.run(["docker", "image", "rm", "-f", "raft-toolkit_raft-test"], capture_output=True, check=False)

            print("✅ Docker resources cleaned up")
            return True

        except Exception as e:
            print(f"⚠️  Error cleaning Docker resources: {e}")
            return False

    def validate_docker_setup(self) -> bool:
        """Validate the complete Docker setup."""
        print("🐳 RAFT Toolkit Docker Test Validator")
        print("=" * 50)

        # Check prerequisites
        if not self.check_docker_available():
            return False

        if not self.check_docker_compose_available():
            return False

        if not self.check_required_files():
            return False

        print("\n✅ All prerequisites met")
        return True


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Validate Docker test environment")
    parser.add_argument("--build", action="store_true", help="Build Docker image first")
    parser.add_argument("--full", action="store_true", help="Run full test suite")
    parser.add_argument("--clean", action="store_true", help="Clean up Docker resources")
    parser.add_argument("--project-root", help="Project root directory")

    args = parser.parse_args()

    # Initialize runner
    project_root = Path(args.project_root) if args.project_root else None
    runner = DockerTestRunner(project_root)

    try:
        # Validate setup
        if not runner.validate_docker_setup():
            print("\n❌ Docker setup validation failed")
            return 1

        # Clean up if requested
        if args.clean:
            runner.clean_docker_resources()
            print("\n✅ Docker cleanup completed")
            return 0

        # Build image if requested
        if args.build:
            if not runner.build_docker_image():
                print("\n❌ Docker image build failed")
                return 1

        # Run environment tests
        print("\n" + "=" * 50)
        if not runner.run_docker_environment_tests():
            print("\n❌ Docker environment validation failed")
            return 1

        # Run full test suite if requested
        if args.full:
            print("\n" + "=" * 50)
            if not runner.run_full_test_suite():
                print("\n❌ Full test suite failed")
                return 1

        print("\n🎉 Docker test validation completed successfully!")
        return 0

    except KeyboardInterrupt:
        print("\n⏸️  Docker test validation interrupted")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
