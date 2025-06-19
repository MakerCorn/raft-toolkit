# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Essential Commands

### Development Setup
```bash
# Install with development dependencies
pip install -e .[dev,all]

# Run all tests with coverage
pytest

# Run specific test categories
pytest tests/unit/                    # Unit tests only
pytest tests/integration/             # Integration tests only  
pytest tests/api/                     # API tests only
pytest tests/cli/                     # CLI tests only
pytest -m "not slow"                  # Skip slow tests

# Run single test file or function
pytest tests/unit/test_config.py
pytest tests/unit/test_config.py::test_specific_function
```

### Code Quality & Validation
```bash
# Python validation commands (run after changes)
python3 -m black .                   # Format code
python3 -m isort .                   # Sort imports  
python3 -m flake8 .                  # Lint code
python3 -m mypy raft_toolkit/        # Type checking
```

### Docker Operations
```bash
# Build and test Linux containers (Windows containers disabled)
docker build -f Dockerfile --target dependencies .
docker build -f Dockerfile --target development .
docker build -f Dockerfile --target production .

# Run containerized application
docker-compose up -d              # Full stack with Redis
docker-compose -f docker-compose.dev.yml up  # Development mode
```

### Web Interface
```bash
# Run web application locally
python -m raft_toolkit.web.app --host 0.0.0.0 --port 8000

# Or use convenience script
python run_web.py
```

### CLI Usage
```bash
# Main CLI entry point
python -m raft_toolkit.cli.main --help

# Evaluation tools
raft-eval --help                     # Console script
raft-answer --help                   # Console script

# Direct tool access
python -m raft_toolkit.tools.eval
python -m raft_toolkit.tools.answer
```

## Architecture Overview

### Core Package Structure
- **`raft_toolkit.core`**: Shared business logic and models
  - `raft_engine.py`: Main RAFT processing engine
  - `models.py`: Pydantic data models and schemas
  - `config.py`: Configuration management with environment variables
  - `services/`: Business logic services (document, LLM, embedding, dataset)
  - `sources/`: Input source adapters (local, S3, SharePoint)
  - `clients/`: External API clients (OpenAI, stats)
  - `utils/`: Shared utilities (templates, rate limiting, file handling)

- **`raft_toolkit.cli`**: Command-line interface
  - `main.py`: CLI entry point using Click framework

- **`raft_toolkit.web`**: Web application 
  - `app.py`: FastAPI web server with async job processing

- **`raft_toolkit.tools`**: Standalone evaluation tools
  - Console scripts for `raft-eval` and `raft-answer` commands

### Dependency Architecture
The project uses an **optimized dependency structure** to minimize installation overhead:

- **Core dependencies**: Essential runtime packages (~15 packages)
- **Optional groups**: Heavy ML libraries in separate install groups
  - `ai`: transformers, sentence-transformers, scikit-learn
  - `langchain`: LangChain ecosystem packages  
  - `embeddings`: nomic embeddings
  - `documents`: extended document processing
  - `web`: FastAPI and web dependencies
  - `cloud`: cloud storage providers
  - `dev`: development and testing tools

Install combinations: `pip install -e .[ai,web]` or `pip install -e .[all]`

### Configuration System
- **Environment-first**: All configuration via environment variables
- **12-Factor compliance**: Configuration separated from code
- **RaftConfig class**: Centralized configuration with Pydantic validation
- **Template system**: Jinja2 templates for prompt customization in `raft_toolkit/templates/`

### Data Flow
1. **Input Sources** → Document ingestion (local files, S3, SharePoint)
2. **Document Service** → Text extraction and chunking  
3. **Embedding Service** → Vector embeddings for chunk retrieval
4. **LLM Service** → Question/answer generation with templates
5. **Dataset Service** → Output formatting (JSON, JSONL, HuggingFace)

### Containerization Strategy
- **Linux containers only**: Windows Docker builds disabled due to complexity
- **Multi-stage builds**: Base → Dependencies → Development → Production → CLI
- **Cross-platform Python packages**: Windows/macOS users use `pip install`
- **Production deployment**: Linux containers for web services

## Important Implementation Details

### Template System
- Templates located in `raft_toolkit/templates/`
- Jinja2-based with variable substitution
- Domain-specific templates for medical, legal, technical documents
- Customizable via configuration or direct template modification

### Rate Limiting
- Built-in rate limiting for API calls (`utils/rate_limiter.py`)
- Configurable via environment variables
- Essential for OpenAI API compliance

### Security
- API key validation and secure storage
- Input sanitization for document processing
- Security scanning with bandit and safety tools

### Testing Strategy
- **Pytest-based** with markers: `unit`, `integration`, `api`, `cli`, `slow`, `docker`
- **Coverage tracking**: Minimum 15% threshold, aiming higher
- **Fixtures in conftest.py**: Shared test data and mocks
- **Environment isolation**: Test environment variables

### Release Process
- **Separate CLI and Web releases**: Independent versioning
- **Linux containers only**: Built and pushed to GHCR
- **Python packages**: Cross-platform distribution via PyPI
- **Automated workflows**: Version bumping, changelog updates, Docker builds

## Validation Requirements

After making changes to Python code, **always run**:
```bash
python3 -m black .
python3 -m isort .  
python3 -m flake8 .
python3 -m mypy raft_toolkit/ --ignore-missing-imports
```

Update the README when making major UI or functionality changes with descriptive examples.
