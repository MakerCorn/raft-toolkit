# RAFT Toolkit Installation Guide

## 📋 Table of Contents

- [RAFT Toolkit Installation Guide](#raft-toolkit-installation-guide)
  - [📋 Table of Contents](#-table-of-contents)
  - [Prerequisites](#prerequisites)
    - [🔧 Core Requirements](#-core-requirements)
    - [☁️ Cloud Integration Requirements (Optional)](#️-cloud-integration-requirements-optional)
    - [🏗️ Infrastructure Requirements (Optional)](#️-infrastructure-requirements-optional)
    - [🔐 Security \& Monitoring (Optional)](#-security--monitoring-optional)
  - [🚀 Quick Start](#-quick-start)
    - [📋 Standard Installation](#-standard-installation)
    - [🌐 Full Installation (All Features)](#-full-installation-all-features)
  - [🐳 Docker Installation](#-docker-installation)
  - [📋 System Requirements Summary](#-system-requirements-summary)
    - [📋 Advanced Installation Options](#-advanced-installation-options)
      - [🎯 Core Dependencies](#-core-dependencies)
      - [🌐 Web Interface Dependencies](#-web-interface-dependencies)
      - [☁️ Cloud Integration Dependencies](#️-cloud-integration-dependencies)
      - [🏗️ Kubernetes \& Infrastructure Dependencies](#️-kubernetes--infrastructure-dependencies)
      - [🔍 Monitoring \& Tracing Dependencies](#-monitoring--tracing-dependencies)
      - [🧪 Development \& Testing Dependencies](#-development--testing-dependencies)
      - [🎛️ Optional Feature Groups](#️-optional-feature-groups)
  - [Environment Setup](#environment-setup)
      - [🎯 **Environment Templates**](#-environment-templates)
    - [📝 Azure OpenAI Support](#-azure-openai-support)
  - [⚡ Usage](#-usage)
    - [🖥️ Command Line Interface](#️-command-line-interface)
      - [⚙️ Main Arguments](#️-main-arguments)
      - [📝 Template Arguments](#-template-arguments)
      - [🚦 Rate Limiting Arguments](#-rate-limiting-arguments)
      - [🧩 Chunking Options](#-chunking-options)
      - [**Extra parameters for semantic chunking** (via `--chunking-params`)](#extra-parameters-for-semantic-chunking-via---chunking-params)
      - [📁 Local Files (Traditional)](#-local-files-traditional)
      - [☁️ Amazon S3 Input Sources](#️-amazon-s3-input-sources)
      - [🏢 SharePoint Online Input Sources](#-sharepoint-online-input-sources)
    - [🔗 **External Service Integration**](#-external-service-integration)
      - [🛠️ **Optional Dependencies**](#️-optional-dependencies)
      - [📁 **Log Files and Rotation**](#-log-files-and-rotation)
      - [🎯 Advanced Filtering \& Configuration](#-advanced-filtering--configuration)
      - [🎯 **Logging Features**](#-logging-features)
      - [🚀 **Enhanced Logging**](#-enhanced-logging)
      - [🔧 **Progress Tracking**](#-progress-tracking)
      - [🔍 **Distributed Tracing**](#-distributed-tracing)
      - [📈 **Contextual Logging**](#-contextual-logging)
      - [📋 **Log Analysis Examples**](#-log-analysis-examples)
    - [🔍 LangWatch Observability](#-langwatch-observability)
      - [Quick Setup](#quick-setup)
      - [Features](#features)
      - [Configuration Options](#configuration-options)

## Prerequisites

### 🔧 Core Requirements

- **Python 3.11 or 3.12** (3.11 recommended for best performance)
- **OpenAI API key** (or Azure OpenAI credentials, or Ollama for local models)
- **4GB+ RAM** (8GB+ recommended for large documents)
- **10GB+ disk space** (for datasets and temporary files)

### ☁️ Cloud Integration Requirements (Optional)

- **AWS credentials** for S3 input sources (IAM role or access keys)
- **Azure AD app registration** for SharePoint Online integration
- **Google Cloud credentials** for GCS storage (service account)

### 🏗️ Infrastructure Requirements (Optional)

- **Docker & Docker Compose** for containerized deployment
- **Redis** for web interface job management and caching
- **Kubernetes cluster** for production scaling and deployment
- **Container registry access** (Docker Hub, GHCR, ACR, ECR, GCR)

### 🔐 Security & Monitoring (Optional)

- **Sentry DSN** for error tracking and performance monitoring
- **DataDog API key** for metrics collection and alerting
- **Jaeger endpoint** for distributed tracing visualization
- **SSL certificates** for HTTPS deployment in production

## 🚀 Quick Start

Choose your installation method based on your use case:

### 📋 Standard Installation
```bash
# Clone the repository
git clone https://github.com/your-repo/raft-toolkit.git
cd raft-toolkit

# Set up environment
cp .env.example .env
# Edit .env with your OpenAI API key

# Install core dependencies (includes basic RAFT functionality)
pip install -r requirements.txt

# Test installation
python run_tests.py --unit --fast

# Run basic CLI
python raft.py --datapath sample_data/sample.pdf --output ./output --preview
```

### 🌐 Full Installation (All Features)
```bash
# Install with all optional features
pip install -e ".[all]"

# Or install specific feature groups as needed:
pip install -e ".[web]"         # Web interface with job management
pip install -e ".[cloud]"       # S3 and SharePoint integration  
pip install -e ".[kubernetes]"  # Kubernetes deployment tools
pip install -e ".[tracing]"     # OpenTelemetry monitoring
pip install -e ".[dev]"         # Development and testing tools

# Start web interface (requires web features)
python run_web.py
# Open http://localhost:8000
```

> **📚 For detailed information about dependency management, version constraints, and advanced installation patterns, see [Requirements Management](REQUIREMENTS.md).**

## 🐳 Docker Installation

```bash
# Clone and configure
git clone https://github.com/your-repo/raft-toolkit.git
cd raft-toolkit
cp .env.example .env
# Edit .env with your configuration

# Run with Docker Compose
docker compose up -d

# Access services
# Web interface: http://localhost:8000
# Redis dashboard: http://localhost:8081
```

## 📋 System Requirements Summary

**Minimum System Requirements:**
- **OS**: Linux, macOS, or Windows with WSL2
- **Python**: 3.11 or 3.12 (3.11+ recommended for optimal performance)  
- **Memory**: 4GB RAM (8GB+ for large document processing)
- **Storage**: 10GB available disk space
- **Network**: Internet access for AI model APIs

**Production System Requirements:**
- **Memory**: 16GB+ RAM for concurrent processing
- **CPU**: 4+ cores for optimal parallel processing
- **Storage**: 100GB+ SSD for large-scale dataset generation
- **Container Runtime**: Docker 20.10+ or containerd 1.6+
- **Orchestration**: Kubernetes 1.24+ for scaled deployments

**Cloud Provider Requirements (Choose One or More):**

| Provider | Service | Purpose | Required Credentials |
|----------|---------|---------|---------------------|
| **OpenAI** | API Platform | AI model access | API key |
| **Azure** | OpenAI Service | Enterprise AI | Endpoint + key |
| **AWS** | S3, EKS | Storage + hosting | Access keys or IAM role |
| **Azure** | Blob, AKS, AD | Storage + hosting + auth | Service principal or managed identity |
| **Google Cloud** | GCS, GKE | Storage + hosting | Service account JSON |
| **SharePoint** | Online | Document source | App registration + client secret |

### 📋 Advanced Installation Options

#### 🎯 Core Dependencies
```bash
# Essential packages for basic RAFT functionality
pip install -r requirements.txt
```
**Includes:** OpenAI integration, document processing (PDF, PPTX, TXT), chunking strategies, dataset generation, Azure services, basic logging, and evaluation tools.

#### 🌐 Web Interface Dependencies
```bash
# For full web UI experience with job management
pip install -r requirements-web.txt
```
**Includes:** FastAPI backend, async job processing, Redis integration, file upload/download, real-time progress tracking, and comprehensive analysis tools.

#### ☁️ Cloud Integration Dependencies
```bash
# For enterprise cloud storage and authentication
pip install -e ".[cloud]"
```
**Includes:** AWS S3 integration, SharePoint Online support, Azure AD authentication, OAuth2 flows, credential management, and cloud storage patterns.

#### 🏗️ Kubernetes & Infrastructure Dependencies
```bash
# For production deployment and scaling
pip install -r requirements-k8s.txt
```
**Includes:** Kubernetes client, multi-cloud deployment tools, Prometheus monitoring, auto-scaling support, and infrastructure management.

#### 🔍 Monitoring & Tracing Dependencies
```bash
# For production observability and debugging
pip install -e ".[tracing]"
```
**Includes:** OpenTelemetry integration, distributed tracing, Sentry error tracking, structured logging, Jaeger export, and performance monitoring.

#### 🧪 Development & Testing Dependencies
```bash
# For contributors and advanced users
pip install -r requirements-test.txt

# Run full test suite with coverage
python run_tests.py --coverage --output-dir ./test-results
```
**Includes:** pytest framework, async testing, API testing, mock libraries, code quality tools (black, flake8, mypy), security scanning, and coverage reporting.

#### 🎛️ Optional Feature Groups

**Complete Feature Matrix:**
```bash
# Install individual feature groups as needed:

# 🌐 Web Interface - Modern web UI with job management
pip install -e ".[web]"
# Required for: Interactive dataset generation, analysis tools, job tracking, file upload/download

# ☁️ Cloud Storage - Enterprise storage integration  
pip install -e ".[cloud]"
# Required for: S3 input sources, SharePoint Online, Azure Blob Storage, multi-cloud support

# 🏗️ Kubernetes - Production deployment tools
pip install -e ".[kubernetes]"  
# Required for: K8s deployment, auto-scaling, multi-cloud clusters, container orchestration

# 🔍 Monitoring - Observability and tracing
pip install -e ".[tracing]"
# Required for: Distributed tracing, error tracking, performance monitoring, structured logging

# 🧪 Development - Testing and quality tools
pip install -e ".[dev]"
# Required for: Unit testing, code quality, security scanning, contribution workflow

# 🚀 All Features - Complete installation
pip install -e ".[all]"
# Includes: web + cloud + kubernetes + tracing + dev
```

**Minimal vs Full Installation Comparison:**

| Feature | Minimal Install | Full Install |
|---------|----------------|--------------|
| **Core RAFT Generation** | ✅ Basic CLI | ✅ CLI + Web UI |
| **Document Processing** | ✅ PDF, TXT, JSON | ✅ + PPTX, API docs |
| **Cloud Storage** | ❌ Local only | ✅ S3, SharePoint, Azure |
| **Kubernetes Deployment** | ❌ Docker only | ✅ Multi-cloud K8s |
| **Monitoring & Tracing** | ❌ Basic logs | ✅ Full observability |
| **Web Interface** | ❌ CLI only | ✅ Modern web UI |
| **Analysis Tools** | ❌ Basic eval | ✅ 6 analysis tools |
| **Rate Limiting** | ❌ No protection | ✅ Advanced rate control |
| **Authentication** | ❌ API keys only | ✅ Enterprise auth |

## Environment Setup

Create a `.env` file in the project root:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_API_BASE_URL=https://api.openai.com/v1

# Azure OpenAI Configuration (optional)
AZURE_OPENAI_ENABLED=false
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=your_azure_openai_key
AZURE_OPENAI_API_VERSION=2024-02-01

# Web Interface Configuration
WEB_HOST=0.0.0.0
WEB_PORT=8000
WEB_DEBUG=false

# Evaluation Configuration
EVAL_MODEL=gpt-4
EVAL_WORKERS=4

# Rate Limiting Configuration (optional)
RAFT_RATE_LIMIT_ENABLED=false
RAFT_RATE_LIMIT_STRATEGY=sliding_window
RAFT_RATE_LIMIT_PRESET=openai_gpt4
RAFT_RATE_LIMIT_REQUESTS_PER_MINUTE=500
RAFT_RATE_LIMIT_TOKENS_PER_MINUTE=10000
RAFT_RATE_LIMIT_MAX_BURST=50
RAFT_RATE_LIMIT_MAX_RETRIES=3

# 🌐 Cloud Storage Configuration (optional)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_DEFAULT_REGION=us-east-1

# 🏢 SharePoint Configuration (optional)
SHAREPOINT_CLIENT_ID=your_sharepoint_app_id
SHAREPOINT_CLIENT_SECRET=your_sharepoint_app_secret
SHAREPOINT_TENANT_ID=your_azure_tenant_id

# 📊 Monitoring and Observability (optional)
RAFT_LOG_LEVEL=INFO
RAFT_LOG_FORMAT=colored
RAFT_LOG_OUTPUT=console
RAFT_TRACING_ENABLED=true
SENTRY_DSN=your_sentry_dsn_for_error_tracking
DATADOG_API_KEY=your_datadog_api_key

# 🔴 Redis Configuration (for web interface)
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=your_redis_password

# 🔒 Security Configuration (production)
CORS_ORIGINS=https://your-domain.com
ENABLE_AUTH=false
JWT_SECRET=your_jwt_secret_for_production
```

#### 🎯 **Environment Templates**

<details>
<summary><strong>📝 Development Environment (.env.dev)</strong></summary>

```bash
# 🛠️ Minimal development setup
OPENAI_API_KEY=your_development_api_key
RAFT_LOG_LEVEL=DEBUG
RAFT_LOG_FORMAT=colored
WEB_DEBUG=true
RAFT_RATE_LIMIT_ENABLED=false
```
</details>

<details>
<summary><strong>🚀 Production Environment (.env.prod)</strong></summary>

```bash
# 🏭 Production deployment configuration
OPENAI_API_KEY=your_production_api_key
RAFT_ENV=production
RAFT_LOG_LEVEL=INFO
RAFT_LOG_FORMAT=json
RAFT_LOG_OUTPUT=both
RAFT_TRACING_ENABLED=true
RAFT_RATE_LIMIT_ENABLED=true
RAFT_RATE_LIMIT_PRESET=openai_gpt4
SENTRY_DSN=your_sentry_dsn
ENABLE_AUTH=true
CORS_ORIGINS=https://your-production-domain.com
```

</details>

<details>
<summary><strong>🧪 Testing Environment (.env.test)</strong></summary>

```bash
# 🔬 Testing configuration
OPENAI_API_KEY=test_key_placeholder
RAFT_LOG_LEVEL=WARNING
RAFT_ENV=testing
TEST_OUTPUT_DIR=./test-results
TEST_TEMP_DIR=/tmp/raft-tests
TEST_COVERAGE_DIR=./coverage
```

</details>

### 📝 Azure OpenAI Support

To enable Azure OpenAI support, set the environment variable `AZURE_OPENAI_ENABLED=1` (or `true`).

You must also set the appropriate Azure OpenAI environment variables (e.g., `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_KEY`, etc.) as required by your deployment.

Example for zsh:

```zsh
export AZURE_OPENAI_ENABLED=1
export AZURE_OPENAI_ENDPOINT="https://your-azure-endpoint.openai.azure.com/"
export AZURE_OPENAI_KEY="your-azure-api-key"
```

If `AZURE_OPENAI_ENABLED` is not set or is set to `0`/`false`, the toolkit will use standard OpenAI API endpoints and keys.

## ⚡ Usage

### 🖥️ Command Line Interface

#### ⚙️ Main Arguments

- **`--datapath`**: Path to the input document
- **`--output`**: Path to save the generated dataset
- **`--output-format`**: Output format (`hf` [default], `completion`, `chat`)
- **`--output-type`**: Output file type (`jsonl` [default], `parquet`)
- **`--output-chat-system-prompt`**: System prompt for chat output (optional)
- **`--distractors`**: Number of distractor documents per data point
- **`--doctype`**: Document type (`pdf`, `txt`, `json`, `api`, `pptx`)
- **`--p`**: Percentage of including the oracle document in context
- **`--chunk_size`**: Size of each chunk (in tokens)
- **`--questions`**: Number of QA pairs to generate per chunk
- **`--workers`**: Number of workers for QA generation
- **`--embed-workers`**: Number of workers for chunking/embedding
- **`--openai_key`**: OpenAI API key
- **`--embedding-model`**: Embedding model (default: `text-embedding-ada-002`)
- **`--completion-model`**: Model for QA generation (default: `gpt-4`)
- **`--use-azure-identity`**: Use Azure Default Credentials for token retrieval
- **`--chunking-strategy`**: Chunking algorithm (`semantic` [default], `fixed`, `sentence`)
- **`--chunking-params`**: JSON string of extra chunker params (e.g. `'{"overlap": 50, "min_chunk_size": 200}'`)

#### 📝 Template Arguments

- **`--templates`**: Directory containing prompt templates (default: `./templates/`)
- **`--embedding-prompt-template`**: Path to custom embedding prompt template file
- **`--qa-prompt-template`**: Path to custom Q&A generation prompt template file
- **`--answer-prompt-template`**: Path to custom answer generation prompt template file

#### 🚦 Rate Limiting Arguments

- **`--rate-limit`**: Enable rate limiting for API requests (default: disabled)
- **`--rate-limit-strategy`**: Rate limiting strategy (`fixed_window`, `sliding_window` [default], `token_bucket`, `adaptive`)
- **`--rate-limit-preset`**: Use preset configuration (`openai_gpt4`, `openai_gpt35_turbo`, `azure_openai_standard`, `anthropic_claude`, `conservative`, `aggressive`)
- **`--rate-limit-requests-per-minute`**: Maximum requests per minute (overrides preset)
- **`--rate-limit-tokens-per-minute`**: Maximum tokens per minute (overrides preset)
- **`--rate-limit-max-burst`**: Maximum burst requests allowed (overrides preset)
- **`--rate-limit-max-retries`**: Maximum retries on rate limit errors (default: 3)

#### 🧩 Chunking Options

- **Semantic** (default): Embedding-based, best for context preservation.
- **Fixed**: Splits by token count (`--chunk_size`).
- **Sentence**: Splits by sentence boundaries, each chunk ≤ `--chunk_size` tokens.

#### **Extra parameters for semantic chunking** (via `--chunking-params`)

- `overlap`: Tokens to overlap between chunks (default: 0)
- `min_chunk_size`: Minimum chunk size (default: 0)
- `number_of_chunks`: Override number of chunks (default: auto)

**Example:**

```bash
python3 raft.py --datapath sample_data/United_States_PDF.pdf \
  --output ./sample_ds4 \
  --distractors 4 \
  --doctype pdf \
  --chunk_size 512 \
  --questions 5 \
  --openai_key OPENAI_KEY \
  --chunking-strategy semantic \
  --chunking-params '{"overlap": 50, "min_chunk_size": 200}'
```

#### 📁 Local Files (Traditional)

```bash
# Set up environment variables
export OPENAI_API_KEY="your_api_key_here"

# Run CLI tool with local files
python raft.py \
  --datapath sample_data/United_States_PDF.pdf \
  --output ./sample_output \
  --distractors 4 \
  --doctype pdf \
  --chunk_size 512 \
  --questions 5

# Preview mode (no processing)
python raft.py --datapath sample.pdf --preview

# Validate configuration only
python raft.py --datapath sample.pdf --validate
```

#### ☁️ Amazon S3 Input Sources

> 📚 **See also**: [Input Sources Guide](docs/INPUT_SOURCES.md) for comprehensive documentation on all input source types and authentication methods.

```bash
# Using environment variables for AWS credentials
export AWS_ACCESS_KEY_ID="your_access_key"
export AWS_SECRET_ACCESS_KEY="your_secret_key"
export AWS_DEFAULT_REGION="us-east-1"

# Process documents from S3 bucket
python raft.py \
  --source-type s3 \
  --source-uri "s3://my-bucket/documents/" \
  --doctype pdf \
  --output ./s3_output \
  --questions 3

# Using credentials in command line
python raft.py \
  --source-type s3 \
  --source-uri "s3://my-bucket/documents/" \
  --source-credentials '{"aws_access_key_id":"key","aws_secret_access_key":"secret","region_name":"us-east-1"}' \
  --output ./s3_output

# Preview S3 source before processing
python raft.py \
  --source-type s3 \
  --source-uri "s3://my-bucket/documents/" \
  --preview
```

#### 🏢 SharePoint Online Input Sources

```bash
# Using client credentials (app registration)
python raft.py \
  --source-type sharepoint \
  --source-uri "https://company.sharepoint.com/sites/mysite/Shared Documents" \
  --source-credentials '{"auth_method":"client_credentials","client_id":"app_id","client_secret":"secret","tenant_id":"tenant_id"}' \
  --output ./sharepoint_output

# Using device code flow (interactive login)
python raft.py \
  --source-type sharepoint \
  --source-uri "https://company.sharepoint.com/sites/mysite/Documents" \
  --source-credentials '{"auth_method":"device_code","client_id":"app_id","tenant_id":"tenant_id"}' \
  --output ./sharepoint_output

# Validate SharePoint configuration
python raft.py \
  --source-type sharepoint \
  --source-uri "https://company.sharepoint.com/sites/mysite/Shared Documents" \
  --source-credentials '{"auth_method":"client_credentials","client_id":"app_id","client_secret":"secret","tenant_id":"tenant_id"}' \
  --validate
```

### 🔗 **External Service Integration**

**Sentry Error Tracking:**

```bash
# Set environment variables
export RAFT_SENTRY_DSN="https://your-sentry-dsn@sentry.io/project"
export RAFT_SENTRY_ENVIRONMENT="production"

# Automatic error tracking and performance monitoring
python raft.py --datapath docs.pdf --output ./results
```

**DataDog Metrics:**

```bash
# Set environment variables  
export RAFT_DATADOG_API_KEY="your-datadog-api-key"
export RAFT_DATADOG_SERVICE="raft-toolkit"

# Automatic metrics collection
python raft.py --datapath docs.pdf --output ./results
```

**Custom Integration:**

```python
from core.logging.setup import setup_external_logging

def custom_handler(log_entry, record):
    # Send to your logging service
    your_service.send_log(log_entry)

setup_external_logging(custom_handler)
```

#### 🛠️ **Optional Dependencies**

Enhanced logging works with optional libraries for improved features:

```bash
# Enhanced colored output
pip install coloredlogs

# Structured logging with processors
pip install structlog  

# YAML configuration support
pip install pyyaml

# Distributed tracing (OpenTelemetry)
pip install opentelemetry-api opentelemetry-sdk
pip install opentelemetry-exporter-jaeger
pip install opentelemetry-instrumentation-logging

# External service integrations
pip install sentry-sdk datadog

# LangWatch observability (optional)
pip install langwatch
```

**Note:** All dependencies are optional. The system gracefully falls back to:

- Standard Python logging if enhanced libraries aren't installed
- UUID-based trace IDs if OpenTelemetry isn't available
- Basic formatters if coloredlogs/structlog aren't available

#### 📁 **Log Files and Rotation**

**File Output Configuration:**

```bash
# Enable file logging
RAFT_LOG_OUTPUT=both  # console and file
RAFT_LOG_DIR=./logs   # custom log directory

# Automatic log rotation (production)
RAFT_LOG_ROTATION=true
RAFT_LOG_MAX_SIZE=10MB
RAFT_LOG_BACKUP_COUNT=5
```

**Log File Formats:**

- `logs/raft.log` - Standard formatted logs  
- `logs/raft.json` - JSON structured logs
- `logs/raft_rotating.log` - Rotated logs for production

#### 🎯 Advanced Filtering & Configuration

```bash
# Filter specific file types and patterns
python raft.py \
  --source-type s3 \
  --source-uri "s3://my-bucket/docs/" \
  --source-include-patterns '["**/*.pdf", "**/reports/*.txt"]' \
  --source-exclude-patterns '["**/temp/**", "**/.DS_Store"]' \
  --source-max-file-size 10485760 \
  --output ./filtered_output

# Environment variable configuration
export RAFT_SOURCE_TYPE=s3
export RAFT_SOURCE_URI=s3://my-bucket/documents/
export RAFT_SOURCE_CREDENTIALS='{"region_name":"us-west-2"}'
export RAFT_SOURCE_MAX_FILE_SIZE=52428800

python raft.py --output ./env_output
```

#### 🎯 **Logging Features**

**Default Open Source Integration:**

- **Colored console output** with timestamps and log levels
- **Progress tracking** with visual indicators for operation phases
- **JSON structured logging** for external analysis tools
- **Multiple output formats** (colored, standard, minimal, JSON)
- **Environment-based configuration** for easy deployment
- **Optional enhanced libraries** with graceful fallbacks

**Distributed Tracing (Default):**

- **OpenTelemetry integration** for distributed tracing with fallback support
- **Automatic trace correlation** with unique trace IDs in all log messages
- **Operation tracking** with start/end spans and custom attributes
- **Jaeger export support** for trace visualization and analysis
- **UUID fallback traces** when OpenTelemetry is not available
- **Trace-aware logging** for complete operation correlation

**External Service Integration:**

- **Sentry integration** for error tracking and performance monitoring
- **DataDog integration** for metrics and logging aggregation
- **Custom handlers** for other logging services
- **Structured data export** compatible with log analysis platforms

#### 🚀 **Enhanced Logging**

**Basic Usage:**

```bash
# Enhanced colored logging (default)
python raft.py --datapath docs.pdf --output ./results

# JSON structured logging for external tools
RAFT_LOG_FORMAT=json python raft.py --datapath docs.pdf --output ./results

# Debug level with file output
RAFT_LOG_LEVEL=DEBUG RAFT_LOG_OUTPUT=both python raft.py --datapath docs.pdf --output ./results
```

**Environment Configuration:**

```bash
# Set in .env file or environment
RAFT_LOG_LEVEL=INFO           # DEBUG, INFO, WARNING, ERROR, CRITICAL
RAFT_LOG_FORMAT=colored       # colored, standard, json, minimal
RAFT_LOG_OUTPUT=console       # console, file, both
RAFT_LOG_STRUCTURED=false     # Enable structured logging with structlog
RAFT_LOG_DIR=./logs          # Directory for log files

# Tracing Configuration
RAFT_TRACING_ENABLED=true     # Enable distributed tracing (default: true)
RAFT_TRACE_SERVICE_NAME=raft-toolkit  # Service name for traces
RAFT_TRACE_SAMPLING_RATE=1.0  # Sampling rate (0.0 to 1.0)
RAFT_JAEGER_ENDPOINT=         # Jaeger collector endpoint (optional)
RAFT_TRACE_CONSOLE=false      # Export traces to console
```

#### 🔧 **Progress Tracking**

The enhanced logging system provides visual progress indicators throughout RAFT operations:

```bash
2025-06-12 22:16:12     INFO [INIT] raft_cli: Loading configuration
2025-06-12 22:16:12     INFO [INIT] raft_cli: Initializing RAFT engine
2025-06-12 22:16:13     INFO [PROC] raft_cli: Beginning dataset generation
2025-06-12 22:18:45     INFO [DONE] raft_cli: RAFT dataset generation completed successfully
```

**Progress States:**

- `INIT` - Initialization and configuration loading
- `VALD` - Validation of inputs and configuration
- `PREV` - Preview generation
- `PROC` - Main processing and dataset generation
- `DONE` - Successful completion
- `FAIL` - Error occurred
- `STOP` - User interruption

#### 🔍 **Distributed Tracing**

The enhanced logging system includes built-in distributed tracing capabilities:

```bash
# Tracing with automatic trace IDs
2025-06-12 22:16:12     INFO [trace:a1b2c3d4] [INIT] raft_cli: Loading configuration
2025-06-12 22:16:13     INFO [trace:a1b2c3d4] [PROC] raft_cli: Beginning dataset generation
2025-06-12 22:18:45     INFO [trace:a1b2c3d4] [DONE] raft_cli: RAFT dataset generation completed
```

**Tracing Features:**

- **Automatic trace correlation** across all operations
- **Unique trace IDs** for debugging and monitoring
- **Operation spans** with start/end tracking
- **Custom attributes** for processing metadata
- **Jaeger integration** for trace visualization

**Jaeger Integration:**

```bash
# Start Jaeger (Docker)
docker run -d --name jaeger \
  -p 16686:16686 \
  -p 14268:14268 \
  jaegertracing/all-in-one:latest

# Configure RAFT to use Jaeger
export RAFT_JAEGER_ENDPOINT="http://localhost:14268/api/traces"
export RAFT_TRACE_CONSOLE=true

# Run with tracing
python raft.py --datapath docs.pdf --output ./results

# View traces at http://localhost:16686
```

#### 📈 **Contextual Logging**

Enhanced logging includes operation metadata and tracing information for better debugging and monitoring:

```json
{
  "timestamp": "2025-06-12T22:16:32.329519",
  "level": "INFO",
  "logger": "raft_cli",
  "message": "Beginning dataset generation",
  "progress": "PROC",
  "trace_id": "a1b2c3d4",
  "span_id": "e5f6g7h8",
  "operation_id": "raft_dataset_generation",
  "context": {
    "input_path": "/path/to/document.pdf",
    "output_path": "./results",
    "doctype": "pdf",
    "chunk_strategy": "semantic",
    "model": "gpt-4",
    "workers": 4
  }
}
```

#### 📋 **Log Analysis Examples**

**Query JSON logs with jq:**
```bash
# Filter by log level
cat logs/raft.json | jq 'select(.level == "ERROR")'

# Extract processing statistics
cat logs/raft.json | jq 'select(.context.total_time) | .context'

# Monitor progress states
cat logs/raft.json | jq 'select(.progress) | {timestamp, progress, message}'

# Trace correlation - find all logs for specific operation
cat logs/raft.json | jq 'select(.trace_id == "a1b2c3d4")'

# Extract trace timing information
cat logs/raft.json | jq 'select(.trace_id) | {timestamp, trace_id, operation_id, progress, message}'

# Monitor operation performance by trace
cat logs/raft.json | jq 'group_by(.trace_id) | map({trace_id: .[0].trace_id, count: length, operation: .[0].operation_id})'
```

### 🔍 LangWatch Observability

LangWatch provides comprehensive observability for LLM operations, offering insights into model performance, costs, and usage patterns.

#### Quick Setup

**Environment Variables:**

```bash
# Enable LangWatch integration
export LANGWATCH_ENABLED=true
export LANGWATCH_API_KEY="your-langwatch-api-key"
export LANGWATCH_PROJECT="raft-toolkit"
export LANGWATCH_DEBUG=false  # Set to true for verbose logging
```

**CLI Usage:**

```bash
# Enable LangWatch tracing for all operations
python raft.py --datapath docs/ --output training_data/ \
  --langwatch-enabled \
  --langwatch-api-key "your-api-key" \
  --langwatch-project "my-raft-project"

# Debug mode for troubleshooting
python raft.py --datapath docs/ --output training_data/ \
  --langwatch-enabled \
  --langwatch-debug
```

#### Features

**Automatic Tracking:**

- 🎯 Question generation operations
- 📝 Answer generation operations
- 🔄 Batch processing workflows
- 📊 Embedding generation
- 💾 Dataset creation statistics

**Performance Insights:**

- ⏱️ Processing time per operation
- 💰 Token usage and costs
- 📈 Throughput metrics
- ❌ Error rates and failures

**Integration Benefits:**

- 🔍 Zero-code instrumentation of OpenAI calls
- 📊 Real-time dashboards and alerts
- 🎯 Performance optimization insights
- 🔧 A/B testing for different prompts/models

#### Configuration Options

```python
# Programmatic configuration
config = RaftConfig(
    langwatch_enabled=True,
    langwatch_api_key="your-api-key",
    langwatch_project="my-project",
    langwatch_endpoint="https://app.langwatch.ai",  # Optional custom endpoint
    langwatch_debug=False
)
```

**Note:** LangWatch integration is completely optional and gracefully degrades if the SDK is not installed.

**Integration with Log Aggregation:**

```bash
# Filebeat configuration
filebeat.inputs:
- type: log
  paths:
    - /app/logs/raft.json
  json.keys_under_root: true
  json.add_error_key: true
  fields:
    service: raft-toolkit
    environment: production
```

---

For environment setup, advanced configuration, and troubleshooting, see the other guides in the `docs/` folder.
