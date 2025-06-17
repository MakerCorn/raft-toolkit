# Test Directory Configuration

The RAFT Toolkit test runner supports configurable directories for test outputs, temporary files, and coverage reports. This allows for flexible deployment in different environments including CI/CD pipelines, development machines, and containerized environments.

## Configuration Methods

Directory configuration follows this priority order:
1. **CLI Arguments** (highest priority)
2. **Environment Variables**  
3. **Default Values** (lowest priority)

## CLI Arguments

```bash
# Basic usage with custom directories
python run_tests.py --output-dir ./test-output --temp-dir /tmp/custom --coverage-dir ./coverage

# Integration tests with custom temp directory
python run_tests.py --integration --temp-dir /fast-ssd/temp

# Coverage with separate coverage directory
python run_tests.py --coverage --coverage-dir /shared/coverage-reports
```

## Environment Variables

### Test Runner Variables
- `TEST_OUTPUT_DIR` - Directory for test results (JUnit XML, etc.)
- `TEST_TEMP_DIR` - Temporary directory for test artifacts
- `TEST_COVERAGE_DIR` - Directory for coverage reports

### Docker Host Variables (for docker-compose)
- `HOST_TEST_RESULTS_DIR` - Host directory mounted to container
- `HOST_COVERAGE_DIR` - Host directory for coverage reports
- `HOST_TEMP_DIR` - Host directory for temporary files

## Default Values

| Variable | Default Value | Description |
|----------|---------------|-------------|
| `TEST_OUTPUT_DIR` | None | No output directory (results in working dir) |
| `TEST_TEMP_DIR` | System temp | Usually `/tmp` on Unix, `%TEMP%` on Windows |
| `TEST_COVERAGE_DIR` | `{output_dir}/coverage` or `{temp_dir}/coverage` | Based on output/temp dir |
| `HOST_TEST_RESULTS_DIR` | `./test-results` | Local directory for Docker bind mount |
| `HOST_COVERAGE_DIR` | `./coverage-reports` | Local directory for Docker bind mount |
| `HOST_TEMP_DIR` | `./temp` | Local directory for Docker bind mount |

## Usage Examples

### Development Environment

```bash
# Quick local testing
python run_tests.py --unit

# With custom temp on fast SSD
export TEST_TEMP_DIR=/mnt/fast-ssd/temp
python run_tests.py --integration --coverage
```

### CI/CD Pipeline

```bash
# Configure for CI environment
export TEST_OUTPUT_DIR=/workspace/test-results
export TEST_TEMP_DIR=/workspace/temp
export TEST_COVERAGE_DIR=/workspace/coverage

# Run tests
python run_tests.py --coverage --output-dir $TEST_OUTPUT_DIR
```

### Docker Environment

```bash
# Configure host directories
export HOST_TEST_RESULTS_DIR=/tmp/ci-results
export HOST_COVERAGE_DIR=/tmp/ci-coverage
export HOST_TEMP_DIR=/tmp/ci-temp

# Run with docker-compose
docker compose -f docker-compose.test.yml up --abort-on-container-exit
```

### Shared Storage Environment

```bash
# Use network shared storage
export TEST_OUTPUT_DIR=/shared/project/test-results
export TEST_COVERAGE_DIR=/shared/project/coverage
export TEST_TEMP_DIR=/local/fast-temp

python run_tests.py --integration --coverage
```

## Environment File Configuration

Copy and customize the provided template:

```bash
cp .env.test.example .env.test
# Edit .env.test with your preferred directories
source .env.test
python run_tests.py --coverage
```

## Directory Structure

When configured, the test runner creates the following structure:

```
{output_dir}/
├── junit.xml           # JUnit test results
├── coverage.xml        # Coverage XML for CI/CD
└── logs/              # Test execution logs

{coverage_dir}/
├── htmlcov/           # HTML coverage reports
├── coverage.xml       # Coverage XML (copy)
└── .coverage          # Coverage database

{temp_dir}/
├── pytest-of-{user}/ # Pytest temporary files
├── test-artifacts/    # Test-generated files
└── cache/             # Test cache files
```

## Best Practices

### Performance
- Use fast storage (SSD) for `TEST_TEMP_DIR`
- Use network storage for `TEST_OUTPUT_DIR` and `TEST_COVERAGE_DIR` in CI/CD

### Security
- Ensure temp directories have proper permissions
- Clean up temp directories after test runs
- Don't store sensitive data in shared temp directories

### CI/CD Integration
- Use separate directories for each build/job
- Include build ID in directory names for parallel builds
- Archive output and coverage directories as artifacts

### Docker Considerations
- Use bind mounts for easier result extraction
- Ensure host directories exist before starting containers
- Use consistent paths between host and container environments

## Troubleshooting

### Permission Issues
```bash
# Ensure directories are writable
chmod 755 $TEST_OUTPUT_DIR $TEST_COVERAGE_DIR
chmod 1777 $TEST_TEMP_DIR  # Sticky bit for temp
```

### Disk Space Issues
```bash
# Monitor temp directory usage
du -sh $TEST_TEMP_DIR

# Clean up after tests
rm -rf $TEST_TEMP_DIR/*
```

### Docker Mount Issues
```bash
# Verify bind mounts work
docker run --rm -v $HOST_TEST_RESULTS_DIR:/test alpine ls -la /test
```