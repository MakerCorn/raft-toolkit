#!/usr/bin/env python3
"""
Test runner script for RAFT Toolkit.

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py --unit             # Run only unit tests  
    python run_tests.py --integration      # Run only integration tests
    python run_tests.py --api              # Run only API tests
    python run_tests.py --cli              # Run only CLI tests
    python run_tests.py --coverage         # Run with coverage report
    python run_tests.py --fast             # Skip slow tests
"""
import argparse
import sys
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Run RAFT Toolkit tests")
    
    # Test selection options
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--api", action="store_true", help="Run API tests only")
    parser.add_argument("--cli", action="store_true", help="Run CLI tests only")
    
    # Test options
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--fast", action="store_true", help="Skip slow tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--quiet", "-q", action="store_true", help="Quiet output")
    parser.add_argument("--parallel", "-n", type=int, help="Run tests in parallel (requires pytest-xdist)")
    
    # File pattern
    parser.add_argument("pattern", nargs="?", help="Test file pattern to run")
    
    args = parser.parse_args()
    
    # Build pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add test selection
    test_markers = []
    if args.unit:
        test_markers.append("unit")
    if args.integration:
        test_markers.append("integration")
    if args.api:
        test_markers.append("api")
    if args.cli:
        test_markers.append("cli")
    
    if test_markers:
        cmd.extend(["-m", " or ".join(test_markers)])
    
    # Add options
    if args.coverage:
        cmd.extend(["--cov=core", "--cov=cli", "--cov=web", "--cov-report=term-missing", "--cov-report=html"])
    
    if args.fast:
        cmd.extend(["-m", "not slow"])
    
    if args.verbose:
        cmd.append("-v")
    elif args.quiet:
        cmd.append("-q")
    
    if args.parallel:
        cmd.extend(["-n", str(args.parallel)])
    
    # Add pattern if specified
    if args.pattern:
        cmd.append(args.pattern)
    
    # Ensure we're in the right directory
    project_root = Path(__file__).parent
    
    print(f"Running tests from: {project_root}")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 60)
    
    # Run the tests
    try:
        result = subprocess.run(cmd, cwd=project_root, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        return 1
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())