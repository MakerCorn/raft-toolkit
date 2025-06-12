# RAFT Toolkit Architecture

## Overview

The RAFT Toolkit has been refactored to follow 12-factor application principles with a clean separation between CLI and web interfaces, both sharing common core functionality.

## 12-Factor App Compliance

### 1. Codebase
- Single codebase tracked in git
- Multiple deployments (CLI, web, containerized)

### 2. Dependencies
- All dependencies explicitly declared in `requirements.txt` and `requirements-web.txt`
- No system-wide packages assumed

### 3. Config
- All configuration stored in environment variables
- Example configuration in `.env.example`
- Configuration class in `core/config.py`

### 4. Backing Services
- LLM services (OpenAI/Azure) treated as attached resources
- Redis for job queuing (optional)
- File storage abstracted

### 5. Build, Release, Run
- Dockerfile for containerized deployments
- Separate entry points for CLI and web
- Configuration injected at runtime

### 6. Processes
- Stateless processes
- Job state stored externally (Redis/database)
- No sticky sessions

### 7. Port Binding
- Web app binds to port via environment variable
- Self-contained service

### 8. Concurrency
- Configurable worker processes
- Horizontal scaling via containers

### 9. Disposability
- Fast startup and graceful shutdown
- Robust against process termination

### 10. Dev/Prod Parity
- Same codebase for all environments
- Environment variables for configuration
- Docker for consistent environments

### 11. Logs
- Logs written to stdout/stderr
- Structured logging support
- Log aggregation via external tools

### 12. Admin Processes
- CLI tools for administrative tasks
- Database migrations via scripts
- One-off processes in same environment

## Architecture Components

### Core (`core/`)
Shared business logic and services used by both CLI and web interfaces:

- `config.py` - Configuration management following 12-factor principles
- `models.py` - Data models and types
- `raft_engine.py` - Main orchestration engine
- `services/` - Business logic services
  - `document_service.py` - Document processing and chunking
  - `llm_service.py` - LLM interaction for Q&A generation
  - `dataset_service.py` - Dataset formatting and export

### CLI (`cli/`)
Command-line interface:

- `main.py` - CLI entry point and argument parsing
- Uses core services for all business logic
- Environment variable configuration support

### Web (`web/`)
Web interface with REST API:

- `app.py` - FastAPI application
- `static/` - Frontend assets (HTML, CSS, JS)
- RESTful API for all operations
- Real-time job status updates
- File upload and download

### Legacy Files
Original files maintained for backward compatibility but marked for eventual removal:

- `raft.py` - Original monolithic implementation
- Various utility modules

## Data Flow

1. **Input Processing**
   - Documents uploaded via CLI or web
   - Validation and type detection
   - Chunking based on strategy

2. **Question Generation**
   - LLM-based question generation per chunk
   - Configurable number of questions
   - Template-based prompt engineering

3. **Answer Generation**
   - Context assembly with distractors
   - LLM-based answer generation
   - Chain-of-thought reasoning

4. **Dataset Assembly**
   - Multiple output formats supported
   - Configurable schema
   - Export to various file types

## Configuration

All configuration follows the hierarchy:
1. Environment variables (highest priority)
2. .env file
3. Command line arguments (CLI only)
4. Default values (lowest priority)

### Key Environment Variables

- `OPENAI_API_KEY` - OpenAI API key
- `AZURE_OPENAI_ENABLED` - Enable Azure OpenAI
- `RAFT_*` - Application-specific settings
- `WEB_*` - Web server settings

## Deployment Options

### Development
```bash
# CLI
python run_cli.py --datapath sample.pdf --output ./output

# Web
python run_web.py
```

### Production
```bash
# Docker
docker-compose up -d

# Direct
gunicorn web.app:app --bind 0.0.0.0:8000 --workers 4
```

## API Endpoints

### Web UI
- `GET /` - Main interface
- `GET /static/*` - Static assets

### REST API
- `POST /api/upload` - File upload
- `POST /api/preview` - Processing preview
- `POST /api/process` - Start processing
- `GET /api/jobs/{id}/status` - Job status
- `GET /api/jobs/{id}/download` - Download results
- `GET /api/jobs` - List all jobs
- `DELETE /api/jobs/{id}` - Delete job

## Security Considerations

- API keys stored in environment variables
- File uploads validated and sandboxed
- CORS policies configurable
- Rate limiting recommended for production
- HTTPS termination via reverse proxy

## Scaling

- Horizontal scaling via multiple container instances
- Redis for shared job state
- Background task processing with Celery (optional)
- Load balancing via nginx/similar

## Monitoring

- Health check endpoint for containers
- Structured logging for observability
- Metrics via application performance monitoring
- Job status tracking and error reporting