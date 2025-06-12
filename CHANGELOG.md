# Changelog

All notable changes to the RAFT Toolkit project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### 🚀 Added

#### Analysis Tools Suite
- **🛠️ Six comprehensive evaluation tools** integrated into web interface
  - **Dataset Evaluation**: Model performance analysis with configurable metrics
  - **Answer Generation**: High-quality answer generation using various LLMs
  - **PromptFlow Analysis**: Multi-dimensional evaluation (relevance, groundedness, fluency, coherence)
  - **Dataset Analysis**: Statistical analysis and quality metrics
  - **Model Comparison**: Side-by-side performance comparison
  - **Batch Processing**: Automated workflows for multiple datasets

#### Enhanced Web Interface
- **Analysis Tools Tab**: Complete tool integration with visual interface
- **Job Management**: Real-time monitoring with progress indicators
- **Results Visualization**: Comprehensive display of metrics and statistics
- **File Upload**: Enhanced drag-and-drop with validation
- **Download Capabilities**: Direct download of analysis results

#### Comprehensive Documentation
- **📚 Complete documentation overhaul**:
  - **RAFT methodology explanation** with pros/cons vs traditional RAG
  - **Fine-tuning process documentation** with best practices
  - **Web Interface Guide** (`docs/WEB_INTERFACE.md`)
  - **Deployment Guide** (`docs/DEPLOYMENT.md`) with cloud platform instructions
  - **Configuration Reference** (`docs/CONFIGURATION.md`)
  - **Enhanced tools documentation** (`tools/README.md`)

#### Advanced Docker & CI/CD
- **🐳 Multi-stage Docker builds**:
  - Production-optimized images with security hardening
  - Development images with debugging support
  - Testing images with coverage reporting
  - CLI-only lightweight images
- **🔧 Comprehensive GitHub workflows**:
  - **Build workflow** with linting, security scanning, and multi-platform builds
  - **Test workflow** with dependency on successful builds
  - **Release workflow** with dependency on successful tests
  - **Security workflow** with automated dependency updates

#### Testing Infrastructure
- **🧪 Complete test suite** with multiple categories:
  - Unit tests across Python versions (3.9, 3.10, 3.11)
  - Integration tests with service dependencies
  - API tests with web interface validation
  - CLI tests for command-line functionality
  - Docker-based testing environment
- **📊 Coverage reporting** with Codecov integration
- **🔍 Security scanning** with Trivy, Bandit, and Safety

### 🔧 Enhanced

#### Developer Experience
- **Visual Process Flow**: Mermaid diagram showing RAFT training process
- **Tool Integration**: Clear documentation of where each tool fits
- **Installation Guides**: Step-by-step for all components
- **Performance Optimization**: Guidelines and benchmarks

#### Documentation Quality
- **Factual Content**: Validated information about RAFT methodology
- **Best Practices**: Comprehensive fine-tuning guidelines
- **Decision Framework**: When to use RAFT vs traditional RAG
- **Examples and Workflows**: Complete end-to-end examples

### 🛡️ Security & Operations

#### Container Security
- **Non-root user execution** in all Docker images
- **Health checks** for all services
- **Vulnerability scanning** with automated reporting
- **SBOM generation** for supply chain security

#### CI/CD Pipeline
- **Dependency-based workflows**: Tests only run after successful builds
- **Automated releases**: Only after successful testing
- **Security monitoring**: Daily scans and automated dependency updates
- **Quality gates**: Comprehensive checks before deployment

#### Configuration Management
- **Environment-based configuration** with validation
- **Secret management** best practices
- **Multi-environment support**: Development, testing, production

### 📦 Dependencies

#### New Development Dependencies
- **Testing**: pytest-cov, pytest-asyncio, httpx for API testing
- **Security**: bandit, safety, semgrep for security scanning
- **Documentation**: mkdocs, mkdocs-material for documentation generation
- **CI/CD**: Actions for automated workflows

#### Updated Core Dependencies
- **Docker**: Updated base images to latest security patches
- **Python**: Support for Python 3.9, 3.10, and 3.11
- **FastAPI**: Latest version with enhanced security features

### 🔍 Quality Assurance

#### Code Quality
- **Automated linting** with flake8, black, and isort
- **Security scanning** with multiple tools
- **License compliance** monitoring
- **Dependency vulnerability** tracking

#### Testing Coverage
- **Multi-platform testing** (linux/amd64, linux/arm64)
- **Cross-version compatibility** testing
- **Service integration** testing with Redis
- **End-to-end workflow** validation

### 📈 Performance

#### Docker Optimization
- **Layer caching** for faster builds
- **Multi-stage builds** for smaller production images
- **Platform-specific optimizations**

#### Workflow Efficiency
- **Parallel job execution** where possible
- **Intelligent caching** strategies
- **Minimal resource usage** optimization

### 🐛 Fixed

#### Workflow Dependencies
- **Proper test gating**: Tests only run after successful builds
- **Release gating**: Releases only after successful tests
- **Error handling**: Comprehensive failure management
- **Artifact management**: Proper cleanup and retention

#### Documentation Issues
- **Mermaid diagram**: Improved readability with black text on light backgrounds
- **Installation clarity**: Step-by-step instructions for all components
- **Configuration examples**: Environment-specific templates

---

## [0.1.0] - 2025-06-11

### 🚀 Major Architecture Refactor

This release represents a complete architectural overhaul of the RAFT Toolkit, transforming it from a monolithic CLI tool into a modern, 12-factor application with dual interfaces.

### ✨ Added

#### New Interfaces
- **🌐 Modern Web UI**: Complete web interface with drag-and-drop file upload
  - Interactive configuration forms with real-time validation
  - Job progress monitoring and status tracking
  - Visual preview of processing estimates
  - Direct dataset download capabilities
  - REST API with auto-generated documentation

- **🖥️ Enhanced CLI**: Improved command-line interface with new features
  - `--preview` mode for processing estimates without execution
  - `--validate` mode for configuration verification
  - Comprehensive help system and error messages
  - Environment variable configuration support

#### Core Architecture
- **📦 Modular Design**: Clean separation of concerns
  - `core/` - Shared business logic and services
  - `cli/` - Command-line interface implementation
  - `web/` - Web interface and REST API
  - `legacy/` - Original implementation files (preserved)

- **⚙️ 12-Factor App Compliance**:
  - Configuration via environment variables
  - Stateless design for horizontal scaling
  - Proper separation of build, release, and run stages
  - Externalized configuration and secrets

#### New Services Architecture
- **`DocumentService`**: Handles file processing and chunking strategies
- **`LLMService`**: Manages question/answer generation with LLMs
- **`DatasetService`**: Handles dataset creation and format conversion
- **`RaftEngine`**: Main orchestration engine coordinating all services

#### Configuration Management
- **Environment-based configuration** following 12-factor principles
- **`.env` file support** with comprehensive example
- **Hierarchical config loading**: Environment → CLI args → defaults
- **Validation system** with clear error messages

#### Container Support
- **🐳 Docker support** with multi-stage builds
- **Docker Compose** orchestration with Redis
- **Health check endpoints** for monitoring
- **Production-ready** NGINX reverse proxy configuration

#### Development Experience
- **Type safety** with comprehensive data models
- **Logging system** with structured output
- **Error handling** with proper exception management
- **Testing support** with mock implementations
- **API documentation** auto-generated from code

### 🔧 Enhanced

#### Processing Features
- **Improved chunking strategies**: Semantic, fixed, and sentence-based
- **Configurable worker threads** for parallel processing
- **Better progress tracking** with real-time updates
- **Enhanced error recovery** and retry mechanisms
- **Memory-efficient processing** for large documents

#### Output Formats
- **Multiple export formats**: HuggingFace, OpenAI completion/chat, evaluation
- **Flexible file types**: JSONL, Parquet support
- **Custom schema support** for different use cases
- **Batch processing capabilities**

#### User Experience
- **Visual configuration** in web interface
- **Real-time feedback** during processing
- **Comprehensive preview** before processing
- **Better error messages** and validation
- **Interactive job management**

### 🏗️ Changed

#### Breaking Changes
- **New entry points**: `run_cli.py` and `run_web.py` replace `raft.py`
- **Configuration format**: Environment variables now use `RAFT_*` prefix
- **API structure**: Completely new REST API design
- **File organization**: Code reorganized into logical modules

#### Migration Path
- **Legacy files preserved** in `legacy/` directory
- **Backward compatibility** maintained for core functionality
- **Migration documentation** provided in `ARCHITECTURE.md`
- **Configuration mapping** from old to new format

### 📦 Dependencies

#### New Dependencies
- **Web Framework**: FastAPI 0.104.1, Uvicorn 0.24.0
- **UI Libraries**: Alpine.js 3.x, Tailwind CSS 2.2.19
- **Type System**: Pydantic 2.x for data validation
- **Container Support**: Redis 5.0.1, Celery 5.3.4

#### Updated Dependencies
- **LangChain**: Updated to latest versions with experimental features
- **OpenAI**: Updated to 1.86.0 with latest API support
- **Datasets**: Updated to 3.6.0 for better performance

### 🔒 Security

- **Environment-based secrets** management
- **Input validation** and sanitization
- **CORS policies** for web interface
- **API rate limiting** capabilities
- **Secure file upload** handling

### 📈 Performance

- **Parallel processing** with configurable workers
- **Efficient chunking** algorithms
- **Memory optimization** for large datasets
- **Background job processing** in web interface
- **Caching strategies** for repeated operations

### 🐛 Fixed

- **Memory leaks** in long-running processes
- **Error handling** improvements throughout
- **Configuration validation** edge cases
- **File processing** race conditions
- **API response** consistency

### 📚 Documentation

#### New Documentation
- **`ARCHITECTURE.md`**: Comprehensive technical documentation
- **API Documentation**: Auto-generated Swagger/OpenAPI docs
- **Docker Guide**: Container deployment instructions
- **Configuration Reference**: Complete environment variable guide

#### Updated Documentation
- **`README.md`**: Updated with new architecture and quick start
- **Installation Guide**: Updated dependency and setup instructions
- **Usage Examples**: Both CLI and web interface examples
- **Troubleshooting**: Common issues and solutions

### 🧪 Development

#### Testing
- **Mock implementations** for demo purposes
- **Health check endpoints** for monitoring
- **Configuration validation** testing
- **API endpoint** testing framework

#### Development Tools
- **Hot reload** for web development
- **Structured logging** for debugging
- **Error tracking** and reporting
- **Performance monitoring** capabilities

### 📋 Migration Guide

For users upgrading from v1.x:

1. **Update entry points**:
   ```bash
   # Old
   python raft.py --datapath doc.pdf --output ./results
   
   # New CLI
   python run_cli.py --datapath doc.pdf --output ./results
   ```

2. **Update configuration**:
   ```bash
   # Create .env file from template
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Try the web interface**:
   ```bash
   python run_web.py
   # Open http://localhost:8000
   ```

### 🙏 Acknowledgments

This major refactor was designed to modernize the RAFT Toolkit while maintaining all existing functionality and improving developer and user experience. The new architecture provides a solid foundation for future enhancements and scaling.

---

## [1.x] - Previous Versions

See `legacy/` directory for the original implementation and its history.