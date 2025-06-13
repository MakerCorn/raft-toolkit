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
    
Directory Configuration:
    python run_tests.py --output-dir ./results     # Custom output directory
    python run_tests.py --temp-dir /tmp/my-temp    # Custom temp directory
    python run_tests.py --coverage-dir ./cov       # Custom coverage directory
    
Environment Variables:
    TEST_OUTPUT_DIR      # Default output directory
    TEST_TEMP_DIR        # Default temp directory  
    TEST_COVERAGE_DIR    # Default coverage directory
    
Examples:
    # Use custom directories
    python run_tests.py --integration --output-dir ./ci-results --temp-dir /tmp/ci
    
    # Use environment variables
    export TEST_OUTPUT_DIR=./my-results
    export TEST_TEMP_DIR=/tmp/my-temp
    python run_tests.py --coverage
    
    # Docker with custom directories
    export HOST_TEST_RESULTS_DIR=./docker-results
    docker compose -f docker-compose.test.yml up
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
    parser.add_argument("--output-dir", help="Output directory for test results and coverage reports")
    parser.add_argument("--temp-dir", help="Temporary directory for test artifacts (default: system temp)")
    parser.add_argument("--coverage-dir", help="Directory for coverage reports (default: output-dir/coverage)")
    
    # File pattern
    parser.add_argument("pattern", nargs="?", help="Test file pattern to run")
    
    args = parser.parse_args()
    
    # Configure directories with environment variable fallbacks
    import shutil
    import os
    import tempfile
    
    # Determine output directory (CLI arg > env var > default)
    output_dir = args.output_dir or os.getenv('TEST_OUTPUT_DIR')
    
    # Determine temp directory (CLI arg > env var > system temp)
    temp_dir = args.temp_dir or os.getenv('TEST_TEMP_DIR') or tempfile.gettempdir()
    
    # Determine coverage directory (CLI arg > env var > output_dir/coverage > temp/coverage)
    if args.coverage_dir:
        coverage_dir = args.coverage_dir
    elif os.getenv('TEST_COVERAGE_DIR'):
        coverage_dir = os.getenv('TEST_COVERAGE_DIR')
    elif output_dir:
        coverage_dir = Path(output_dir) / "coverage"
    else:
        coverage_dir = Path(temp_dir) / "coverage"
    
    # Update args with resolved directories
    args.output_dir = output_dir
    args.temp_dir = temp_dir
    args.coverage_dir = str(coverage_dir)
    
    # Try system Python first, then current python
    python_candidates = ["/usr/bin/python3", shutil.which("python3"), shutil.which("python"), sys.executable]
    python_cmd = None
    
    for candidate in python_candidates:
        if candidate and os.path.exists(candidate):
            # Test if pytest is available
            try:
                test_result = subprocess.run([candidate, "-m", "pytest", "--version"], 
                                           capture_output=True, check=False)
                if test_result.returncode == 0:
                    python_cmd = candidate
                    break
            except:
                continue
    
    if not python_cmd:
        python_cmd = sys.executable
        print("Warning: pytest may not be available. Install with: pip install pytest pytest-cov")
    
    cmd = [python_cmd, "-m", "pytest"]
    
    # Add test selection - use direct path specification instead of markers
    test_paths = []
    if args.unit:
        test_paths.append("tests/unit/")
    if args.integration:
        test_paths.append("tests/integration/")
    if args.api:
        test_paths.append("tests/api/")
    if args.cli:
        test_paths.append("tests/cli/")
    
    if test_paths:
        # Use direct paths instead of markers to avoid marker issues
        cmd.extend(test_paths)
    else:
        # If no specific test type selected, test all
        cmd.append("tests/")
    
    # Add options
    if args.coverage:
        coverage_args = ["--cov=core", "--cov=cli", "--cov=web", "--cov-report=term-missing", "--cov-fail-under=5"]
        
        # Create directories as needed
        if args.output_dir:
            output_path = Path(args.output_dir)
            try:
                output_path.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                # Fall back to temp directory if we can't create in the specified location
                print(f"Warning: Cannot create output directory {output_path}, using temp directory")
                args.output_dir = str(Path(temp_dir) / "test-results")
                output_path = Path(args.output_dir)
                output_path.mkdir(parents=True, exist_ok=True)
        
        coverage_path = Path(args.coverage_dir)
        try:
            coverage_path.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            # Fall back to temp directory if we can't create in the specified location
            print(f"Warning: Cannot create coverage directory {coverage_path}, using temp directory")
            args.coverage_dir = str(Path(temp_dir) / "coverage")
            coverage_path = Path(args.coverage_dir)
            coverage_path.mkdir(parents=True, exist_ok=True)
        
        # Configure coverage reports
        if args.output_dir:
            # Put XML in output dir for CI/CD, HTML in coverage dir
            coverage_args.extend([
                f"--cov-report=html:{coverage_path}/htmlcov",
                f"--cov-report=xml:{Path(args.output_dir)}/coverage.xml"
            ])
        else:
            # Put both in coverage dir
            coverage_args.extend([
                f"--cov-report=html:{coverage_path}/htmlcov",
                f"--cov-report=xml:{coverage_path}/coverage.xml"
            ])
        
        cmd.extend(coverage_args)
    
    if args.fast:
        cmd.extend(["-m", "not slow"])
    
    if args.verbose:
        cmd.append("-v")
    elif args.quiet:
        cmd.append("-q")
    
    if args.parallel:
        cmd.extend(["-n", str(args.parallel)])
    
    # Add JUnit XML output for CI/CD
    if args.output_dir:
        output_path = Path(args.output_dir)
        cmd.extend(["--junitxml", str(output_path / "junit.xml")])
    
    # Add pattern if specified
    if args.pattern:
        cmd.append(args.pattern)
    
    # Configure test environment
    test_env = os.environ.copy()
    
    # Set temp directory for subprocess
    if args.temp_dir:
        test_env['TMPDIR'] = args.temp_dir
        test_env['TEMP'] = args.temp_dir
        test_env['TMP'] = args.temp_dir
    
    # Set pytest temp directory
    if args.temp_dir:
        cmd.extend(["--basetemp", args.temp_dir])
    
    # Ensure we're in the right directory
    project_root = Path(__file__).parent
    
    print(f"Running tests from: {project_root}")
    print(f"Output directory: {args.output_dir or 'None'}")
    print(f"Temp directory: {args.temp_dir}")
    print(f"Coverage directory: {args.coverage_dir}")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 60)
    
    # Run the tests with security considerations
    try:
        # Validate that cmd contains only expected pytest commands
        if not all(isinstance(arg, str) for arg in cmd):
            raise ValueError("All command arguments must be strings")
        if not (cmd[0].endswith(('pytest', 'python', 'python3')) or 'python' in cmd[0]):
            raise ValueError("Command must start with pytest or python")
            
        result = subprocess.run(cmd, cwd=project_root, env=test_env, check=False, shell=False)  # nosec B603
        return result.returncode
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        return 1
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())