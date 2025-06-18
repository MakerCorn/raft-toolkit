# Requirements Management

This document describes the dependency management structure for RAFT Toolkit.

## Requirements Files Structure

The project uses a modular requirements structure with reference-based dependency management:

```
requirements.txt           # Core dependencies only
requirements-web.txt       # Web UI dependencies
requirements-cloud.txt     # Cloud storage and Azure/AWS services
requirements-k8s.txt       # Kubernetes deployment dependencies
requirements-tracing.txt   # Observability and tracing dependencies
requirements-test.txt      # Testing and development tools
requirements-dev.txt       # Complete development environment
requirements.in           # Source file for pip-tools
```

## Installation Patterns

### Basic Installation
```bash
pip install -r requirements.txt
```

### Web UI Development
```bash
pip install -r requirements.txt -r requirements-web.txt
```

### Cloud Integration
```bash
pip install -r requirements.txt -r requirements-cloud.txt
```

### Complete Development Environment
```bash
pip install -r requirements-dev.txt
```

### Using PyProject.toml (Recommended)
```bash
# Core installation
pip install .

# With optional dependencies
pip install ".[web]"
pip install ".[cloud]"
pip install ".[kubernetes]"
pip install ".[tracing]"
pip install ".[dev]"

# All features
pip install ".[all]"
```

## Dependency Management

### Version Constraints
- All dependencies use semantic version ranges (e.g., `>=1.0.0,<2.0.0`)
- Pin specific versions only when necessary for compatibility
- Use lower bounds for minimum required features
- Use upper bounds to prevent breaking changes

### Reference Structure
- Base `requirements.txt` contains only core dependencies
- Feature-specific files reference base with `-r requirements.txt`
- Prevents duplication and ensures consistency
- Enables modular installation patterns

### Maintenance
- Primary dependency definitions are in `pyproject.toml`
- Requirements files should align with optional dependencies
- Use `pip-tools` for lockfile generation when needed:
  ```bash
  pip-compile requirements.in
  ```

## Key Dependencies

### Core ML/AI
- **OpenAI**: LLM integration and embeddings
- **Transformers**: Hugging Face model support
- **LangChain**: Text processing and document handling
- **Sentence Transformers**: Embedding generation
- **Scikit-learn**: Machine learning utilities

### Data Processing
- **Datasets**: Hugging Face datasets integration
- **Pandas**: Data manipulation and analysis
- **PyArrow**: Efficient data serialization
- **JSONLines**: JSONL format support

### Document Processing
- **PyPDF**: PDF text extraction
- **python-pptx**: PowerPoint processing
- **pdfplumber**: Advanced PDF parsing

### Web Framework
- **FastAPI**: Modern web API framework
- **Uvicorn**: ASGI server
- **Redis/Celery**: Background task processing

### Cloud Services
- **Azure SDK**: Complete Azure integration
- **Boto3**: AWS services integration
- **MSAL**: Microsoft authentication

### Development Tools
- **pytest**: Testing framework
- **black/isort**: Code formatting
- **mypy**: Type checking
- **flake8**: Linting
- **bandit/safety**: Security scanning

## Best Practices

1. **Always use version ranges** instead of exact pins unless required
2. **Reference base requirements** in feature-specific files
3. **Group related dependencies** with comments
4. **Test dependency combinations** in CI/CD
5. **Keep pyproject.toml as source of truth** for dependency definitions
6. **Use optional dependencies** for feature-specific installations
7. **Document installation patterns** for different use cases

## Troubleshooting

### Common Issues

#### httpx Version Conflicts
The project pins `httpx<0.28` due to FastAPI TestClient compatibility:
```bash
# Fix: Use the pinned version
pip install "httpx<0.28,>=0.24.0"
```

#### Azure SDK Conflicts
Azure packages should be updated together:
```bash
# Fix: Update all Azure packages
pip install --upgrade azure-identity azure-core azure-storage-blob
```

#### Dependency Resolution
If you encounter dependency conflicts:
```bash
# Use pip-tools to resolve
pip-compile requirements.in
pip-sync requirements.txt
```

## Migration from Legacy Requirements

If migrating from the old requirements structure:

1. **Install with new structure**: `pip install -r requirements-dev.txt`
2. **Test functionality**: Run test suite to verify compatibility
3. **Update CI/CD**: Use new requirements files in build processes
4. **Clean environment**: `pip freeze | pip uninstall -y -r /dev/stdin` if needed