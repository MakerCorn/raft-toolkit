# Testing Guide

This document describes the testing strategy and setup for the RAFT Toolkit.

## 🧪 Test Structure

The test suite is organized into several categories:

```
tests/
├── unit/                 # Unit tests for individual modules
│   ├── test_config.py   # Configuration tests
│   ├── test_models.py   # Data model tests
│   ├── test_clients.py  # Client utility tests
│   └── test_utils.py    # Utility function tests
├── integration/         # Integration tests for services
│   ├── test_document_service.py
│   ├── test_llm_service.py
│   └── test_raft_engine.py
├── api/                 # API endpoint tests
│   └── test_web_app.py
├── cli/                 # CLI interface tests
│   ├── test_cli_main.py
│   └── test_eval_tool.py
└── conftest.py         # Shared fixtures and configuration
```

## 🚀 Quick Start

### Install Test Dependencies

```bash
pip install -r requirements-test.txt
```

### Run All Tests

```bash
# Using the test runner
python run_tests.py

# Using pytest directly
pytest
```

### Run Specific Test Categories

```bash
# Unit tests only
python run_tests.py --unit

# Integration tests only
python run_tests.py --integration

# API tests only
python run_tests.py --api

# CLI tests only
python run_tests.py --cli
```

### Run with Coverage

```bash
python run_tests.py --coverage
```

## 📊 Test Categories

### Unit Tests

Test individual modules and functions in isolation:

- **Configuration**: Environment loading, validation, defaults
- **Models**: Data structures, serialization, validation
- **Clients**: OpenAI client creation, Azure integration
- **Utils**: File operations, environment config, identity management

**Example:**
```python
def test_config_from_env():
    """Test loading config from environment variables."""
    env_vars = {
        "DATAPATH": "test.pdf",
        "OUTPUT": "output_dir",
        "OPENAI_API_KEY": "test-key"
    }
    
    with patch.dict(os.environ, env_vars):
        config = RaftConfig.from_env()
        assert config.datapath == Path("test.pdf")
        assert config.output == "output_dir"
```

### Integration Tests

Test interactions between services and components:

- **Document Service**: File processing, chunking strategies
- **LLM Service**: Q&A generation, batch processing
- **RAFT Engine**: End-to-end pipeline orchestration

**Example:**
```python
def test_end_to_end_processing(raft_engine, temp_directory):
    """Test complete processing pipeline."""
    # Create test document
    test_file = temp_directory / "test.txt"
    test_file.write_text("Test content about AI...")
    
    # Run processing
    stats = raft_engine.generate_dataset(test_file, output_path)
    
    assert stats["total_qa_points"] > 0
    assert stats["successful_chunks"] > 0
```

### API Tests

Test web interface endpoints and responses:

- **Health**: Service health checks
- **Upload**: File upload handling
- **Processing**: Job management and execution
- **Download**: Result retrieval

**Example:**
```python
def test_upload_file_success(client, temp_upload_file):
    """Test successful file upload."""
    with open(temp_upload_file, "rb") as f:
        response = client.post(
            "/api/upload",
            files={"file": ("test.txt", f, "text/plain")}
        )
    
    assert response.status_code == 200
    assert response.json()["success"] is True
```

### CLI Tests

Test command-line interface functionality:

- **Argument Parsing**: Command line option handling
- **Preview Mode**: Processing estimation
- **Validation**: Input validation
- **Main Flow**: Complete CLI execution

**Example:**
```python
def test_main_preview_mode(temp_directory):
    """Test CLI in preview mode."""
    test_args = ["raft.py", "--datapath", "test.pdf", "--preview"]
    
    with patch('sys.argv', test_args):
        with patch('cli.main.show_preview') as mock_preview:
            main()
            mock_preview.assert_called_once()
```

## 🔧 Test Configuration

### Environment Variables

Set these environment variables for testing:

```bash
export OPENAI_API_KEY="demo-key"  # For API integration tests
export AZURE_OPENAI_ENABLED="false"  # Disable Azure for tests
```

### Pytest Configuration

The `pytest.ini` file configures:

- Test discovery patterns
- Coverage reporting
- Warning filters
- Test markers

### Fixtures

Common test fixtures in `conftest.py`:

- `sample_config`: Test configuration object
- `sample_document_chunk`: Test document chunk
- `sample_qa_datapoint`: Test Q&A data point
- `temp_directory`: Temporary directory for test files
- `mock_openai_client`: Mocked OpenAI client
- `mock_embeddings`: Mocked embeddings model

## 📈 Coverage Requirements

- **Minimum Coverage**: 80%
- **Target Coverage**: 90%+
- **Coverage Reports**: Generated in `htmlcov/` directory

### View Coverage Report

```bash
python run_tests.py --coverage
open htmlcov/index.html  # View detailed coverage report
```

## 🎯 Test Markers

Use pytest markers to categorize tests:

```python
@pytest.mark.unit
def test_unit_function():
    """Unit test example."""
    pass

@pytest.mark.integration  
def test_integration_flow():
    """Integration test example."""
    pass

@pytest.mark.slow
def test_expensive_operation():
    """Slow test that can be skipped."""
    pass
```

### Run Tests by Marker

```bash
# Run only unit tests
pytest -m unit

# Run only fast tests (skip slow ones)
pytest -m "not slow"

# Run unit OR integration tests
pytest -m "unit or integration"
```

## 🚀 Continuous Integration

### GitHub Actions

The CI pipeline runs automatically on:

- Push to `main` or `develop` branches
- Pull requests to `main`

**Pipeline stages:**
1. **Test**: Run all test categories across Python 3.11-3.12
2. **Lint**: Code style and quality checks
3. **Security**: Security vulnerability scanning

### Local Pre-commit

Run before committing:

```bash
# Run all tests
python run_tests.py

# Run linting
black . && isort . && flake8 .

# Run security checks
bandit -r core/ cli/ web/
safety check
```

## 🔍 Debugging Tests

### Run Single Test

```bash
pytest tests/unit/test_config.py::TestRaftConfig::test_config_creation -v
```

### Debug Mode

```bash
pytest --pdb  # Drop into debugger on failure
pytest -s    # Don't capture stdout (see print statements)
```

### Test Coverage for Specific Module

```bash
pytest --cov=core.config tests/unit/test_config.py --cov-report=term-missing
```

## 📝 Writing New Tests

### Test Naming Convention

- Test files: `test_*.py`
- Test classes: `Test*`
- Test functions: `test_*`

### Best Practices

1. **Arrange-Act-Assert**: Structure tests clearly
2. **Mock External Dependencies**: Use mocks for APIs, file system
3. **Test Edge Cases**: Include error conditions and boundary cases
4. **Keep Tests Fast**: Mock expensive operations
5. **Use Descriptive Names**: Test names should explain what is being tested

### Example Test Template

```python
class TestNewFeature:
    """Test new feature functionality."""
    
    def test_feature_success_case(self, fixture):
        """Test successful execution of feature."""
        # Arrange
        input_data = "test input"
        expected_output = "expected result"
        
        # Act
        result = new_feature(input_data)
        
        # Assert
        assert result == expected_output
    
    def test_feature_error_case(self):
        """Test feature handles errors correctly."""
        with pytest.raises(ValueError, match="Expected error message"):
            new_feature(invalid_input)
```

## 🛠️ Test Utilities

### Mock Helpers

Common mocking patterns:

```python
# Mock OpenAI client
@patch('core.services.llm_service.build_openai_client')
def test_with_mock_client(mock_build_client):
    mock_client = Mock()
    mock_build_client.return_value = mock_client
    # ... test logic

# Mock file operations
@patch('pathlib.Path.exists')
def test_file_check(mock_exists):
    mock_exists.return_value = True
    # ... test logic
```

### Temporary Files

```python
def test_with_temp_file(temp_directory):
    """Test using temporary directory fixture."""
    test_file = temp_directory / "test.txt"
    test_file.write_text("test content")
    
    # File will be automatically cleaned up
```

## 📚 Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [pytest-mock](https://pytest-mock.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Python unittest.mock](https://docs.python.org/3/library/unittest.mock.html)