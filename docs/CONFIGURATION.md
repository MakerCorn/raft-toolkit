# ⚙️ RAFT Toolkit Configuration Guide

> **Complete configuration reference for all RAFT Toolkit components**

This guide provides comprehensive information about configuring the RAFT Toolkit for different use cases, environments, and requirements.

---

## 📋 Table of Contents

- [🔧 Environment Variables](#-environment-variables)
- [📝 Template Configuration](#-template-configuration)
- [📄 Configuration Files](#-configuration-files)
- [📂 Input Sources Configuration](#-input-sources-configuration)
- [🌐 API Configuration](#-api-configuration)
- [🖥️ CLI Configuration](#️-cli-configuration)
- [🌍 Web Interface Configuration](#-web-interface-configuration)
- [🛠️ Tools Configuration](#️-tools-configuration)
- [🚦 Rate Limiting Configuration](#-rate-limiting-configuration)
- [🚀 Performance Tuning](#-performance-tuning)
- [🔒 Security Configuration](#-security-configuration)
- [🔍 LangWatch Observability](#-langwatch-observability)
- [📊 Logging Configuration](#-logging-configuration)

---

## 🔧 Environment Variables

### Core Configuration

```bash
# API Keys and Authentication
OPENAI_API_KEY=sk-...                    # OpenAI API key (required)
OPENAI_API_BASE_URL=https://api.openai.com/v1  # OpenAI API base URL
OPENAI_ORG_ID=org-...                    # OpenAI organization ID (optional)

# Azure OpenAI Configuration
AZURE_OPENAI_ENABLED=false              # Enable Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://...        # Azure OpenAI endpoint
AZURE_OPENAI_KEY=...                     # Azure OpenAI API key
AZURE_OPENAI_API_VERSION=2024-02-01     # API version
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4      # Deployment name
AZURE_OPENAI_USE_IDENTITY=false         # Use Azure managed identity

# Default Models
DEFAULT_COMPLETION_MODEL=gpt-4           # Default completion model
DEFAULT_EMBEDDING_MODEL=text-embedding-ada-002  # Default embedding model
DEFAULT_CHAT_MODEL=gpt-4                 # Default chat model

# LangWatch Observability
LANGWATCH_ENABLED=false                 # Enable LangWatch integration
LANGWATCH_API_KEY=...                   # LangWatch API key
LANGWATCH_ENDPOINT=https://api.langwatch.ai  # LangWatch endpoint
LANGWATCH_PROJECT=raft-toolkit          # Project name for organizing traces
LANGWATCH_DEBUG=false                   # Enable debug logging
```

### Web Interface Configuration

```bash
# Server Settings
WEB_HOST=127.0.0.1                      # Web server host
WEB_PORT=8000                           # Web server port
WEB_DEBUG=false                         # Debug mode
WEB_WORKERS=4                           # Number of worker processes
WEB_RELOAD=false                        # Auto-reload on code changes

# Security
CORS_ORIGINS=["http://localhost:3000"]  # CORS allowed origins
API_KEY_REQUIRED=false                  # Require API key for access
API_KEYS=["api-key-1","api-key-2"]      # Valid API keys
SESSION_SECRET=your-secret-key          # Session encryption key

# File Upload
MAX_UPLOAD_SIZE=52428800                # Maximum upload size (50MB)
UPLOAD_TIMEOUT=300                      # Upload timeout (seconds)
ALLOWED_EXTENSIONS=pdf,txt,json,pptx    # Allowed file extensions
UPLOAD_DIR=/tmp/uploads                 # Upload directory
```

### Processing Configuration

```bash
# Worker Configuration
DEFAULT_WORKERS=4                       # Default number of workers
MAX_WORKERS=16                          # Maximum workers allowed
MIN_WORKERS=1                           # Minimum workers allowed

# Job Configuration
JOB_TIMEOUT=3600                        # Job timeout (1 hour)
JOB_CLEANUP_INTERVAL=3600               # Cleanup interval (1 hour)
MAX_CONCURRENT_JOBS=10                  # Maximum concurrent jobs

# Processing Limits
MAX_CHUNK_SIZE=2048                     # Maximum chunk size (tokens)
MIN_CHUNK_SIZE=100                      # Minimum chunk size (tokens)
MAX_QUESTIONS_PER_CHUNK=20              # Maximum questions per chunk
MAX_DISTRACTORS=10                      # Maximum distractor documents

# Rate Limiting
RAFT_RATE_LIMIT_ENABLED=false           # Enable rate limiting
RAFT_RATE_LIMIT_STRATEGY=fixed_window   # Rate limiting strategy (fixed_window, sliding_window, token_bucket, adaptive)
RAFT_RATE_LIMIT_PRESET=gpt-4            # Preset configuration (gpt-4, gpt-3.5-turbo, azure-openai, anthropic-claude)
RAFT_RATE_LIMIT_REQUESTS_PER_MINUTE=60  # Custom requests per minute limit
RAFT_RATE_LIMIT_TOKENS_PER_MINUTE=90000 # Custom tokens per minute limit
RAFT_RATE_LIMIT_MAX_BURST=10            # Maximum burst requests allowed
RAFT_RATE_LIMIT_MAX_RETRIES=5           # Maximum retry attempts
RAFT_RATE_LIMIT_BASE_DELAY=1.0          # Base delay between retries (seconds)
RAFT_RATE_LIMIT_MAX_DELAY=60.0          # Maximum delay between retries (seconds)
RAFT_RATE_LIMIT_BURST_WINDOW=60         # Burst window in seconds
RAFT_RATE_LIMIT_EXPONENTIAL_BACKOFF=true # Use exponential backoff for retries
RAFT_RATE_LIMIT_JITTER=true             # Add jitter to retry delays
```

### Storage Configuration

```bash
# File Storage
DATA_DIR=/app/data                      # Data directory
OUTPUT_DIR=/app/outputs                 # Output directory
TEMP_DIR=/tmp                           # Temporary directory
LOG_DIR=/app/logs                       # Log directory

# Database/Cache
REDIS_URL=redis://localhost:6379        # Redis connection string
DATABASE_URL=sqlite:///app/data/raft.db # Database connection string
CACHE_TTL=3600                          # Cache TTL (1 hour)

# Cloud Storage (Optional)
AWS_S3_BUCKET=raft-toolkit-data         # S3 bucket name
AWS_S3_REGION=us-west-2                 # S3 region
AZURE_STORAGE_ACCOUNT=raftstorage       # Azure storage account
GCS_BUCKET=raft-toolkit-data            # Google Cloud Storage bucket
```

### Input Source Configuration

```bash
# Input Source Type
RAFT_SOURCE_TYPE=local                  # Input source type (local, s3, sharepoint)
RAFT_SOURCE_URI=/path/to/documents      # Source URI or path
RAFT_DATAPATH=/path/to/documents        # Legacy local path (for backward compatibility)

# Source Filtering
RAFT_SOURCE_INCLUDE_PATTERNS='["**/*.pdf", "**/*.txt"]'  # Include patterns (JSON array)
RAFT_SOURCE_EXCLUDE_PATTERNS='["**/temp/**"]'           # Exclude patterns (JSON array)
RAFT_SOURCE_MAX_FILE_SIZE=52428800      # Maximum file size in bytes (50MB)
RAFT_SOURCE_BATCH_SIZE=100              # Batch size for processing

# S3 Configuration
AWS_ACCESS_KEY_ID=AKIA...               # AWS access key
AWS_SECRET_ACCESS_KEY=...               # AWS secret key
AWS_DEFAULT_REGION=us-east-1            # AWS region
AWS_SESSION_TOKEN=...                   # Session token (for temporary credentials)

# SharePoint Configuration
RAFT_SOURCE_CREDENTIALS='{              # SharePoint credentials (JSON)
  "auth_method": "client_credentials",
  "client_id": "app_id",
  "client_secret": "secret",
  "tenant_id": "tenant_id"
}'
```

### Logging Configuration

```bash
# Log Levels
LOG_LEVEL=INFO                          # Log level (DEBUG, INFO, WARNING, ERROR)
ROOT_LOG_LEVEL=WARNING                  # Root logger level
THIRD_PARTY_LOG_LEVEL=WARNING           # Third-party library log level

# Log Format
LOG_FORMAT=detailed                     # Log format (simple, detailed, json)
LOG_DATE_FORMAT=%Y-%m-%d %H:%M:%S       # Date format
LOG_FILE_MAX_SIZE=10485760              # Max log file size (10MB)
LOG_FILE_BACKUP_COUNT=5                 # Number of backup files

# Structured Logging
ENABLE_STRUCTURED_LOGGING=false         # Enable structured logging
LOG_JSON_INDENT=2                       # JSON log indentation
LOG_INCLUDE_TIMESTAMP=true              # Include timestamp in logs
```

---

## 📂 Input Sources Configuration

The RAFT Toolkit supports multiple input sources for document processing. Configure your preferred source using environment variables or CLI arguments.

### 📁 Local Files (Default)

```bash
# Using traditional datapath
RAFT_DATAPATH=/path/to/documents

# Or using new source configuration  
RAFT_SOURCE_TYPE=local
RAFT_SOURCE_URI=/path/to/documents
```

### ☁️ Amazon S3

Configure S3 access using AWS credentials:

```bash
# Source configuration
RAFT_SOURCE_TYPE=s3
RAFT_SOURCE_URI=s3://bucket-name/prefix/

# AWS credentials (choose one method)
# Method 1: Environment variables
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_DEFAULT_REGION=us-east-1

# Method 2: Inline credentials (not recommended for production)
RAFT_SOURCE_CREDENTIALS='{
  "aws_access_key_id": "AKIA...",
  "aws_secret_access_key": "...",
  "region_name": "us-east-1"
}'

# Method 3: Use IAM roles (when running on AWS)
# No additional configuration needed
```

### 🏢 SharePoint Online

Configure SharePoint access using Azure AD app registration:

```bash
# Source configuration
RAFT_SOURCE_TYPE=sharepoint
RAFT_SOURCE_URI="https://company.sharepoint.com/sites/mysite/Shared Documents"

# Authentication methods
# Method 1: Client credentials (recommended for production)
RAFT_SOURCE_CREDENTIALS='{
  "auth_method": "client_credentials",
  "client_id": "your-app-id",
  "client_secret": "your-app-secret", 
  "tenant_id": "your-tenant-id"
}'

# Method 2: Device code flow (interactive)
RAFT_SOURCE_CREDENTIALS='{
  "auth_method": "device_code",
  "client_id": "your-app-id",
  "tenant_id": "your-tenant-id"
}'
```

### 🎯 Advanced Filtering

Control which files are processed:

```bash
# Include specific file patterns
RAFT_SOURCE_INCLUDE_PATTERNS='["**/*.pdf", "**/reports/*.txt", "**/2024/**"]'

# Exclude specific patterns
RAFT_SOURCE_EXCLUDE_PATTERNS='["**/temp/**", "**/.DS_Store", "**/draft*"]'

# File size limits
RAFT_SOURCE_MAX_FILE_SIZE=52428800  # 50MB in bytes

# Processing batch size
RAFT_SOURCE_BATCH_SIZE=100
```

### 📋 Source Configuration Examples

#### Complete S3 Example
```bash
export RAFT_SOURCE_TYPE=s3
export RAFT_SOURCE_URI=s3://my-docs-bucket/technical-docs/
export AWS_ACCESS_KEY_ID=AKIA...
export AWS_SECRET_ACCESS_KEY=...
export AWS_DEFAULT_REGION=us-west-2
export RAFT_SOURCE_INCLUDE_PATTERNS='["**/*.pdf", "**/*.md"]'
export RAFT_SOURCE_EXCLUDE_PATTERNS='["**/drafts/**"]'
export RAFT_SOURCE_MAX_FILE_SIZE=104857600  # 100MB

python raft.py --output ./s3-dataset
```

#### Complete SharePoint Example
```bash
export RAFT_SOURCE_TYPE=sharepoint
export RAFT_SOURCE_URI="https://company.sharepoint.com/sites/engineering/Shared Documents/API Docs"
export RAFT_SOURCE_CREDENTIALS='{
  "auth_method": "client_credentials",
  "client_id": "12345678-1234-1234-1234-123456789012",
  "client_secret": "your-secret-here",
  "tenant_id": "87654321-4321-4321-4321-210987654321"
}'
export RAFT_SOURCE_INCLUDE_PATTERNS='["**/*.docx", "**/*.pdf"]'

python raft.py --doctype pdf --output ./sharepoint-dataset
```

For detailed setup instructions, see [INPUT_SOURCES.md](INPUT_SOURCES.md).

---

## 📝 Template Configuration

The RAFT Toolkit supports custom prompt templates for embeddings and Q&A generation, allowing you to optimize for specific domains or use cases.

### Template Types

#### Embedding Templates

Embedding templates control how documents are embedded for semantic chunking and retrieval:

```bash
# Environment variable
RAFT_EMBEDDING_PROMPT_TEMPLATE=./templates/custom_embedding.txt

# CLI argument
--embedding-prompt-template ./templates/custom_embedding.txt
```

**Example embedding template:**
```
Generate an embedding for the following content:

Document Type: {document_type}
Content: {content}

Focus on key concepts, entities, and relationships in the content.
```

#### QA Generation Templates

QA templates control how questions are generated from document chunks:

```bash
# Environment variable
RAFT_QA_PROMPT_TEMPLATE=./templates/custom_qa.txt

# CLI argument
--qa-prompt-template ./templates/custom_qa.txt
```

**Example QA template:**
```
Generate {num_questions} questions based on the following context.
The questions should be specific to the content and require understanding of the text.

Context: {context}

Questions:
```

#### Answer Generation Templates

Answer templates control how answers are generated for questions:

```bash
# Environment variable
RAFT_ANSWER_PROMPT_TEMPLATE=./templates/custom_answer.txt

# CLI argument
--answer-prompt-template ./templates/custom_answer.txt
```

**Example answer template:**
```
Question: {question}
Context: {context}

Provide a concise and accurate answer based only on the information in the context.
Answer:
```

### Domain-Specific Templates

#### Medical Domain

```bash
# Medical embedding template
export RAFT_EMBEDDING_PROMPT_TEMPLATE=./templates/medical_embedding.txt

# Medical QA template
export RAFT_QA_PROMPT_TEMPLATE=./templates/medical_qa.txt
```

#### Legal Domain

```bash
# Legal embedding template
export RAFT_EMBEDDING_PROMPT_TEMPLATE=./templates/legal_embedding.txt

# Legal QA template
export RAFT_QA_PROMPT_TEMPLATE=./templates/legal_qa.txt
```

#### Technical Documentation

```bash
# Technical embedding template
export RAFT_EMBEDDING_PROMPT_TEMPLATE=./templates/technical_embedding.txt

# Technical QA template
export RAFT_QA_PROMPT_TEMPLATE=./templates/technical_qa.txt
```

### Template Variables

The following variables are available in templates:

**Embedding Templates:**
- `{content}` - The document content
- `{document_type}` - The type of document (pdf, txt, json, etc.)
- `{metadata}` - Additional metadata about the document
- `{chunk_index}` - Index of the chunk within the document
- `{chunking_strategy}` - Strategy used for chunking

**QA Templates:**
- `{context}` - The document chunk content
- `{num_questions}` - Number of questions to generate
- `{document_type}` - The type of document
- `{metadata}` - Additional metadata

**Answer Templates:**
- `{question}` - The question to answer
- `{context}` - The context for answering
- `{document_type}` - The type of document

## 📄 Configuration Files

### Main Configuration File

**config.yaml**:
```yaml
# Core Configuration
api:
  openai:
    api_key: ${OPENAI_API_KEY}
    base_url: ${OPENAI_API_BASE_URL:https://api.openai.com/v1}
    org_id: ${OPENAI_ORG_ID:}
    timeout: 60
    max_retries: 3
    retry_delay: 1.0
  
  azure_openai:
    enabled: ${AZURE_OPENAI_ENABLED:false}
    endpoint: ${AZURE_OPENAI_ENDPOINT:}
    api_key: ${AZURE_OPENAI_KEY:}
    api_version: ${AZURE_OPENAI_API_VERSION:2024-02-01}

# Default Models
models:
  completion: ${DEFAULT_COMPLETION_MODEL:gpt-4}
  embedding: ${DEFAULT_EMBEDDING_MODEL:text-embedding-ada-002}
  chat: ${DEFAULT_CHAT_MODEL:gpt-4}

# Processing Defaults
processing:
  chunk_size: 512
  questions_per_chunk: 5
  distractors: 1
  oracle_probability: 1.0
  chunking_strategy: semantic
  workers: 4
  
# Output Configuration
output:
  format: hf
  type: jsonl
  directory: ${OUTPUT_DIR:/app/outputs}
  
# Web Interface
web:
  host: ${WEB_HOST:127.0.0.1}
  port: ${WEB_PORT:8000}
  debug: ${WEB_DEBUG:false}
  workers: ${WEB_WORKERS:4}
  cors_origins: ${CORS_ORIGINS:["*"]}
  
# Security
security:
  api_key_required: ${API_KEY_REQUIRED:false}
  session_secret: ${SESSION_SECRET:}
  allowed_hosts: ["*"]
  
# File Upload
upload:
  max_size: ${MAX_UPLOAD_SIZE:52428800}
  timeout: ${UPLOAD_TIMEOUT:300}
  allowed_extensions: ${ALLOWED_EXTENSIONS:pdf,txt,json,pptx}
  directory: ${UPLOAD_DIR:/tmp/uploads}
  
# Storage
storage:
  data_dir: ${DATA_DIR:/app/data}
  temp_dir: ${TEMP_DIR:/tmp}
  redis_url: ${REDIS_URL:redis://localhost:6379}
  
# Logging
logging:
  level: ${LOG_LEVEL:INFO}
  format: ${LOG_FORMAT:detailed}
  file:
    enabled: true
    path: ${LOG_DIR:/app/logs}/raft.log
    max_size: ${LOG_FILE_MAX_SIZE:10485760}
    backup_count: ${LOG_FILE_BACKUP_COUNT:5}
```

### Environment-Specific Configs

**config.development.yaml**:
```yaml
web:
  debug: true
  reload: true
  workers: 1
  
processing:
  workers: 2
  
logging:
  level: DEBUG
  format: detailed
```

**config.production.yaml**:
```yaml
web:
  debug: false
  reload: false
  workers: 4
  
processing:
  workers: 8
  
logging:
  level: INFO
  format: json
  
security:
  api_key_required: true
  allowed_hosts: ["yourdomain.com", "*.yourdomain.com"]
```

### Docker Configuration

**docker-compose.override.yml** (for development):
```yaml
version: '3.8'

services:
  raft-toolkit:
    build:
      context: .
      target: development
    volumes:
      - .:/app
      - /app/__pycache__
    environment:
      - WEB_DEBUG=true
      - WEB_RELOAD=true
      - LOG_LEVEL=DEBUG
    ports:
      - "8000:8000"
      - "5678:5678"  # debugpy port
```

---

## 🌐 API Configuration

### OpenAI API Configuration

```python
# Configuration class
class OpenAIConfig:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("OPENAI_API_BASE_URL", "https://api.openai.com/v1")
        self.org_id = os.getenv("OPENAI_ORG_ID")
        self.timeout = int(os.getenv("OPENAI_TIMEOUT", "60"))
        self.max_retries = int(os.getenv("OPENAI_MAX_RETRIES", "3"))
        self.retry_delay = float(os.getenv("OPENAI_RETRY_DELAY", "1.0"))

# Client initialization
def create_openai_client(config: OpenAIConfig):
    return OpenAI(
        api_key=config.api_key,
        base_url=config.base_url,
        organization=config.org_id,
        timeout=config.timeout,
        max_retries=config.max_retries
    )
```

### Azure OpenAI Configuration

```python
class AzureOpenAIConfig:
    def __init__(self):
        self.enabled = os.getenv("AZURE_OPENAI_ENABLED", "false").lower() == "true"
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_key = os.getenv("AZURE_OPENAI_KEY")
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

def create_azure_client(config: AzureOpenAIConfig):
    return AzureOpenAI(
        api_key=config.api_key,
        api_version=config.api_version,
        azure_endpoint=config.endpoint
    )
```

### Custom API Endpoints

```bash
# Ollama (Local)
export OPENAI_API_BASE_URL="http://localhost:11434/v1"
export OPENAI_API_KEY="ollama-anything"

# OpenRouter
export OPENAI_API_BASE_URL="https://openrouter.ai/api/v1"
export OPENAI_API_KEY="sk-or-..."

# Together AI
export OPENAI_API_BASE_URL="https://api.together.xyz/v1"
export OPENAI_API_KEY="..."

# Anthropic (via proxy)
export OPENAI_API_BASE_URL="https://api.anthropic.com/v1"
export OPENAI_API_KEY="sk-ant-..."
```

---

## 🖥️ CLI Configuration

### Command Line Arguments

```bash
# Core arguments
--datapath         # Input document path
--output          # Output directory
--config          # Configuration file path
--env-file        # Environment file path

# Processing options
--doctype         # Document type (pdf, txt, json, pptx)
--chunk-size      # Chunk size in tokens
--questions       # Questions per chunk
--distractors     # Number of distractor documents
--workers         # Number of worker threads

# Model options
--completion-model    # Completion model name
--embedding-model     # Embedding model name
--openai-key         # OpenAI API key override

# Output options
--output-format      # Output format (hf, completion, chat)
--output-type        # Output type (jsonl, parquet)

# Advanced options
--chunking-strategy  # Chunking strategy (semantic, fixed, sentence)
--chunking-params    # JSON string of chunking parameters
--p                  # Oracle probability
--pace              # Enable pacing

# Input source options
--source-type        # Input source type (local, s3, sharepoint)
--source-uri         # Source URI (paths, S3 URLs, SharePoint URLs)
--source-credentials # JSON credentials for cloud authentication
--source-include-patterns # Include file patterns (JSON array)
--source-exclude-patterns # Exclude file patterns (JSON array)
--source-max-file-size    # Maximum file size in bytes
--source-batch-size       # Batch size for processing

# Rate limiting options
--rate-limit        # Enable/disable rate limiting
--rate-limit-strategy # Rate limiting strategy
--rate-limit-preset   # Use preset configurations
--rate-limit-requests-per-minute # Custom rate limits
--rate-limit-tokens-per-minute   # Token-based rate limits
--rate-limit-max-burst # Burst configuration
--rate-limit-max-retries # Retry configuration

# Template options
--embedding-prompt-template # Custom embedding template
--qa-prompt-template        # Custom Q&A generation template
--answer-prompt-template    # Custom answer generation template
--templates                 # Custom templates directory

# LangWatch options
--langwatch-enabled  # Enable LangWatch observability
--langwatch-api-key  # Set LangWatch API key
--langwatch-endpoint # Set custom LangWatch endpoint
--langwatch-project  # Set project name
--langwatch-debug    # Enable debug mode

# Utility options
--preview           # Preview mode (no processing)
--validate          # Validate configuration only
--verbose           # Verbose output
--quiet             # Quiet output
```

### Configuration Priority

The CLI uses the following configuration priority (highest to lowest):

1. **Command line arguments**
2. **Environment variables**
3. **Configuration file** (specified with `--config`)
4. **Default configuration file** (`config.yaml`)
5. **Built-in defaults**

### Examples

**Basic usage**:
```bash
python raft.py \
  --datapath document.pdf \
  --output ./output \
  --questions 5 \
  --workers 4
```

**With configuration file**:
```bash
python raft.py \
  --config production.yaml \
  --datapath document.pdf \
  --output ./output
```

**Environment override**:
```bash
WORKERS=8 CHUNK_SIZE=1024 python raft.py \
  --datapath document.pdf \
  --output ./output
```

**With cloud input source**:
```bash
python raft.py \
  --source-type s3 \
  --source-uri s3://my-bucket/documents/ \
  --source-include-patterns '["**/*.pdf", "**/*.txt"]' \
  --output ./output
```

**With rate limiting**:
```bash
python raft.py \
  --datapath document.pdf \
  --output ./output \
  --rate-limit \
  --rate-limit-preset gpt-4 \
  --workers 8
```

**With custom templates**:
```bash
python raft.py \
  --datapath document.pdf \
  --output ./output \
  --embedding-prompt-template ./templates/custom_embedding.txt \
  --qa-prompt-template ./templates/custom_qa.txt
```

**With LangWatch integration**:
```bash
python raft.py \
  --datapath document.pdf \
  --output ./output \
  --langwatch-enabled \
  --langwatch-project my-project
```

**With cloud input source**:
```bash
python raft.py \
  --source-type s3 \
  --source-uri s3://my-bucket/documents/ \
  --source-include-patterns '["**/*.pdf", "**/*.txt"]' \
  --output ./output
```

**With rate limiting**:
```bash
python raft.py \
  --datapath document.pdf \
  --output ./output \
  --rate-limit \
  --rate-limit-preset gpt-4 \
  --workers 8
```

**With custom templates**:
```bash
python raft.py \
  --datapath document.pdf \
  --output ./output \
  --embedding-prompt-template ./templates/custom_embedding.txt \
  --qa-prompt-template ./templates/custom_qa.txt
```

**With LangWatch integration**:
```bash
python raft.py \
  --datapath document.pdf \
  --output ./output \
  --langwatch-enabled \
  --langwatch-project my-project
```

---

## 🌍 Web Interface Configuration

### Server Configuration

```python
# FastAPI configuration
app_config = {
    "title": "RAFT Toolkit API",
    "description": "Retrieval Augmentation Fine-Tuning Toolkit",
    "version": "1.0.0",
    "docs_url": "/docs",
    "redoc_url": "/redoc",
    "openapi_url": "/openapi.json",
    "lifespan": lifespan_context
}

# Uvicorn configuration
uvicorn_config = {
    "host": os.getenv("WEB_HOST", "127.0.0.1"),
    "port": int(os.getenv("WEB_PORT", "8000")),
    "workers": int(os.getenv("WEB_WORKERS", "4")),
    "reload": os.getenv("WEB_RELOAD", "false").lower() == "true",
    "log_level": os.getenv("LOG_LEVEL", "info").lower(),
    "access_log": True,
    "use_colors": True
}
```

### Middleware Configuration

```python
# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Rate limiting middleware
app.add_middleware(
    SlowAPIMiddleware,
    algorithm=GCRAAlgorithm,
    rate_limiter=RateLimiter(
        times=int(os.getenv("RATE_LIMIT_REQUESTS", "100")),
        seconds=int(os.getenv("RATE_LIMIT_PERIOD", "60"))
    )
)

# Request size middleware
app.add_middleware(
    RequestSizeLimitMiddleware,
    max_request_size=int(os.getenv("MAX_REQUEST_SIZE", "52428800"))
)

# Security headers middleware
app.add_middleware(
    SecurityHeadersMiddleware,
    content_security_policy={
        "default-src": "'self'",
        "script-src": "'self' 'unsafe-inline'",
        "style-src": "'self' 'unsafe-inline'",
        "img-src": "'self' data:",
    },
    x_frame_options="DENY",
    x_content_type_options="nosniff",
    referrer_policy="strict-origin-when-cross-origin"
)
```

### Static File Configuration

```python
# Static files
app.mount("/static", StaticFiles(directory="web/static"), name="static")

# File upload configuration
UPLOAD_CONFIG = {
    "max_size": int(os.getenv("MAX_UPLOAD_SIZE", "52428800")),
    "allowed_extensions": os.getenv("ALLOWED_EXTENSIONS", "pdf,txt,json,pptx").split(","),
    "upload_dir": os.getenv("UPLOAD_DIR", "/tmp/uploads"),
    "timeout": int(os.getenv("UPLOAD_TIMEOUT", "300"))
}
```

### Service Configuration

```python
# Template service configuration
TEMPLATE_CONFIG = {
    "templates_dir": os.getenv("TEMPLATES_DIR", "templates"),
    "embedding_template": os.getenv("RAFT_EMBEDDING_PROMPT_TEMPLATE"),
    "qa_template": os.getenv("RAFT_QA_PROMPT_TEMPLATE"),
    "answer_template": os.getenv("RAFT_ANSWER_PROMPT_TEMPLATE"),
}

# Rate limiting configuration
RATE_LIMIT_CONFIG = {
    "enabled": os.getenv("RAFT_RATE_LIMIT_ENABLED", "false").lower() == "true",
    "strategy": os.getenv("RAFT_RATE_LIMIT_STRATEGY", "fixed_window"),
    "preset": os.getenv("RAFT_RATE_LIMIT_PRESET"),
    "requests_per_minute": int(os.getenv("RAFT_RATE_LIMIT_REQUESTS_PER_MINUTE", "60")),
    "tokens_per_minute": int(os.getenv("RAFT_RATE_LIMIT_TOKENS_PER_MINUTE", "90000")),
}

# LangWatch configuration
LANGWATCH_CONFIG = {
    "enabled": os.getenv("LANGWATCH_ENABLED", "false").lower() == "true",
    "api_key": os.getenv("LANGWATCH_API_KEY"),
    "endpoint": os.getenv("LANGWATCH_ENDPOINT", "https://api.langwatch.ai"),
    "project": os.getenv("LANGWATCH_PROJECT", "raft-toolkit"),
    "debug": os.getenv("LANGWATCH_DEBUG", "false").lower() == "true",
}
```

### Service Configuration

```python
# Template service configuration
TEMPLATE_CONFIG = {
    "templates_dir": os.getenv("TEMPLATES_DIR", "templates"),
    "embedding_template": os.getenv("RAFT_EMBEDDING_PROMPT_TEMPLATE"),
    "qa_template": os.getenv("RAFT_QA_PROMPT_TEMPLATE"),
    "answer_template": os.getenv("RAFT_ANSWER_PROMPT_TEMPLATE"),
}

# Rate limiting configuration
RATE_LIMIT_CONFIG = {
    "enabled": os.getenv("RAFT_RATE_LIMIT_ENABLED", "false").lower() == "true",
    "strategy": os.getenv("RAFT_RATE_LIMIT_STRATEGY", "fixed_window"),
    "preset": os.getenv("RAFT_RATE_LIMIT_PRESET"),
    "requests_per_minute": int(os.getenv("RAFT_RATE_LIMIT_REQUESTS_PER_MINUTE", "60")),
    "tokens_per_minute": int(os.getenv("RAFT_RATE_LIMIT_TOKENS_PER_MINUTE", "90000")),
}

# LangWatch configuration
LANGWATCH_CONFIG = {
    "enabled": os.getenv("LANGWATCH_ENABLED", "false").lower() == "true",
    "api_key": os.getenv("LANGWATCH_API_KEY"),
    "endpoint": os.getenv("LANGWATCH_ENDPOINT", "https://api.langwatch.ai"),
    "project": os.getenv("LANGWATCH_PROJECT", "raft-toolkit"),
    "debug": os.getenv("LANGWATCH_DEBUG", "false").lower() == "true",
}
```

---

## 🛠️ Tools Configuration

### Evaluation Tools Configuration

**eval.py configuration**:
```bash
# Environment variables for eval.py
EVAL_MODEL=gpt-4                        # Evaluation model
EVAL_WORKERS=4                          # Number of workers
EVAL_BATCH_SIZE=10                      # Batch size for processing
EVAL_TIMEOUT=300                        # Request timeout
EVAL_MAX_RETRIES=3                      # Maximum retries
EVAL_RETRY_DELAY=2                      # Delay between retries
EVAL_INPUT_KEY=instruction              # Input column name
EVAL_OUTPUT_KEY=answer                  # Output column name

# Rate limiting configuration
EVAL_RATE_LIMIT_ENABLED=true            # Enable rate limiting
EVAL_RATE_LIMIT_STRATEGY=adaptive       # Rate limiting strategy
EVAL_RATE_LIMIT_PRESET=gpt-4            # Preset configuration
EVAL_RATE_LIMIT_REQUESTS_PER_MINUTE=60  # Custom requests per minute

# Template configuration
EVAL_TEMPLATE_PATH=./templates/eval_template.txt  # Custom evaluation template

# LangWatch configuration
EVAL_LANGWATCH_ENABLED=false            # Enable LangWatch integration
EVAL_LANGWATCH_PROJECT=raft-eval        # Project name for organizing traces
```

**answer.py configuration**:
```bash
# Environment variables for answer.py
ANSWER_MODEL=gpt-4                      # Answer generation model
ANSWER_WORKERS=4                        # Number of workers
ANSWER_TEMPERATURE=0.02                 # Generation temperature
ANSWER_MAX_TOKENS=8192                  # Maximum tokens per response
ANSWER_TIMEOUT=300                      # Request timeout

# Rate limiting configuration
ANSWER_RATE_LIMIT_ENABLED=true          # Enable rate limiting
ANSWER_RATE_LIMIT_STRATEGY=adaptive     # Rate limiting strategy
ANSWER_RATE_LIMIT_PRESET=gpt-4          # Preset configuration
ANSWER_RATE_LIMIT_REQUESTS_PER_MINUTE=60 # Custom requests per minute

# Template configuration
ANSWER_TEMPLATE_PATH=./templates/answer_template.txt  # Custom answer template

# LangWatch configuration
ANSWER_LANGWATCH_ENABLED=false          # Enable LangWatch integration
ANSWER_LANGWATCH_PROJECT=raft-answer    # Project name for organizing traces
```

### PromptFlow Configuration

```bash
# Azure PromptFlow configuration
SCORE_AZURE_OPENAI_ENDPOINT=https://...
SCORE_AZURE_OPENAI_API_KEY=...
SCORE_OPENAI_API_VERSION=2024-02-01
SCORE_AZURE_OPENAI_DEPLOYMENT=gpt-4

# Azure AI Project configuration
GROUNDEDNESS_SUB_ID=subscription-id
GROUNDEDNESS_GROUP=resource-group
GROUNDEDNESS_PROJECT_NAME=project-name

REPORT_SUB_ID=subscription-id
REPORT_GROUP=resource-group
REPORT_PROJECT_NAME=project-name

# Evaluation configuration
PF_EVAL_MODE=local                      # local or remote
PF_WORKERS=2                            # Number of workers
PF_TIMEOUT=600                          # Evaluation timeout

# Rate limiting for evaluation
PF_RATE_LIMIT_ENABLED=true
PF_RATE_LIMIT_STRATEGY=adaptive
PF_RATE_LIMIT_PRESET=gpt-4

# LangWatch integration
PF_LANGWATCH_ENABLED=false
PF_LANGWATCH_PROJECT=promptflow-eval
```

### Tool-specific Configuration Files

**tools/config.yaml**:
```yaml
evaluation:
  default_model: gpt-4
  workers: 4
  batch_size: 10
  timeout: 300
  max_retries: 3
  
answer_generation:
  default_model: gpt-4
  workers: 4
  temperature: 0.02
  max_tokens: 8192
  
promptflow:
  mode: local
  workers: 2
  timeout: 600
  evaluators:
    - relevance
    - groundedness
    - fluency
    - coherence
    - similarity

templates:
  embedding_template: templates/embedding_prompt_template.txt
  qa_template: templates/qa_prompt_template.txt
  answer_template: templates/answer_prompt_template.txt
  
rate_limiting:
  enabled: true
  strategy: adaptive
  preset: gpt-4
  requests_per_minute: 60
  tokens_per_minute: 90000
  
langwatch:
  enabled: false
  project: raft-toolkit
  debug: false
```

---

## 🚦 Rate Limiting Configuration

The RAFT Toolkit includes a comprehensive rate limiting system to manage API usage and prevent rate limit errors when working with cloud-based AI services.

### Rate Limiting Strategies

```bash
# Fixed Window Strategy
export RAFT_RATE_LIMIT_ENABLED=true
export RAFT_RATE_LIMIT_STRATEGY=fixed_window
export RAFT_RATE_LIMIT_REQUESTS_PER_MINUTE=60

# Sliding Window Strategy
export RAFT_RATE_LIMIT_ENABLED=true
export RAFT_RATE_LIMIT_STRATEGY=sliding_window
export RAFT_RATE_LIMIT_REQUESTS_PER_MINUTE=60
export RAFT_RATE_LIMIT_BURST_WINDOW=60

# Token Bucket Strategy
export RAFT_RATE_LIMIT_ENABLED=true
export RAFT_RATE_LIMIT_STRATEGY=token_bucket
export RAFT_RATE_LIMIT_REQUESTS_PER_MINUTE=60
export RAFT_RATE_LIMIT_MAX_BURST=10

# Adaptive Strategy
export RAFT_RATE_LIMIT_ENABLED=true
export RAFT_RATE_LIMIT_STRATEGY=adaptive
export RAFT_RATE_LIMIT_REQUESTS_PER_MINUTE=60
export RAFT_RATE_LIMIT_TOKENS_PER_MINUTE=90000
```

### Preset Configurations

```bash
# GPT-4 Preset
export RAFT_RATE_LIMIT_ENABLED=true
export RAFT_RATE_LIMIT_PRESET=gpt-4
# Sets appropriate limits for GPT-4 API

# GPT-3.5 Turbo Preset
export RAFT_RATE_LIMIT_ENABLED=true
export RAFT_RATE_LIMIT_PRESET=gpt-3.5-turbo
# Sets appropriate limits for GPT-3.5 Turbo API

# Azure OpenAI Preset
export RAFT_RATE_LIMIT_ENABLED=true
export RAFT_RATE_LIMIT_PRESET=azure-openai
# Sets appropriate limits for Azure OpenAI service

# Anthropic Claude Preset
export RAFT_RATE_LIMIT_ENABLED=true
export RAFT_RATE_LIMIT_PRESET=anthropic-claude
# Sets appropriate limits for Anthropic Claude API
```

### Retry Configuration

```bash
# Basic retry configuration
export RAFT_RATE_LIMIT_MAX_RETRIES=5
export RAFT_RATE_LIMIT_BASE_DELAY=1.0

# Advanced retry configuration
export RAFT_RATE_LIMIT_EXPONENTIAL_BACKOFF=true
export RAFT_RATE_LIMIT_JITTER=true
export RAFT_RATE_LIMIT_MAX_DELAY=60.0
```

### CLI Configuration

```bash
# Enable rate limiting with strategy
python raft.py \
  --rate-limit \
  --rate-limit-strategy adaptive \
  [other options]

# Use preset configuration
python raft.py \
  --rate-limit \
  --rate-limit-preset gpt-4 \
  [other options]

# Custom rate limits
python raft.py \
  --rate-limit \
  --rate-limit-requests-per-minute 60 \
  --rate-limit-tokens-per-minute 90000 \
  [other options]
```

### Rate Limiting Statistics

The RAFT Toolkit provides real-time statistics on rate limiting performance:

- **Request counts**: Total requests processed
- **Wait times**: Time spent waiting due to rate limits
- **Rate limit hits**: Number of rate limit errors encountered
- **Current effective rate**: Actual requests per minute being processed
- **Adaptive adjustments**: Rate adjustments for adaptive strategy

## 🚦 Rate Limiting Configuration

The RAFT Toolkit includes a comprehensive rate limiting system to manage API usage and prevent rate limit errors when working with cloud-based AI services.

### Rate Limiting Strategies

```bash
# Fixed Window Strategy
export RAFT_RATE_LIMIT_ENABLED=true
export RAFT_RATE_LIMIT_STRATEGY=fixed_window
export RAFT_RATE_LIMIT_REQUESTS_PER_MINUTE=60

# Sliding Window Strategy
export RAFT_RATE_LIMIT_ENABLED=true
export RAFT_RATE_LIMIT_STRATEGY=sliding_window
export RAFT_RATE_LIMIT_REQUESTS_PER_MINUTE=60
export RAFT_RATE_LIMIT_BURST_WINDOW=60

# Token Bucket Strategy
export RAFT_RATE_LIMIT_ENABLED=true
export RAFT_RATE_LIMIT_STRATEGY=token_bucket
export RAFT_RATE_LIMIT_REQUESTS_PER_MINUTE=60
export RAFT_RATE_LIMIT_MAX_BURST=10

# Adaptive Strategy
export RAFT_RATE_LIMIT_ENABLED=true
export RAFT_RATE_LIMIT_STRATEGY=adaptive
export RAFT_RATE_LIMIT_REQUESTS_PER_MINUTE=60
export RAFT_RATE_LIMIT_TOKENS_PER_MINUTE=90000
```

### Preset Configurations

```bash
# GPT-4 Preset
export RAFT_RATE_LIMIT_ENABLED=true
export RAFT_RATE_LIMIT_PRESET=gpt-4
# Sets appropriate limits for GPT-4 API

# GPT-3.5 Turbo Preset
export RAFT_RATE_LIMIT_ENABLED=true
export RAFT_RATE_LIMIT_PRESET=gpt-3.5-turbo
# Sets appropriate limits for GPT-3.5 Turbo API

# Azure OpenAI Preset
export RAFT_RATE_LIMIT_ENABLED=true
export RAFT_RATE_LIMIT_PRESET=azure-openai
# Sets appropriate limits for Azure OpenAI service

# Anthropic Claude Preset
export RAFT_RATE_LIMIT_ENABLED=true
export RAFT_RATE_LIMIT_PRESET=anthropic-claude
# Sets appropriate limits for Anthropic Claude API
```

### Retry Configuration

```bash
# Basic retry configuration
export RAFT_RATE_LIMIT_MAX_RETRIES=5
export RAFT_RATE_LIMIT_BASE_DELAY=1.0

# Advanced retry configuration
export RAFT_RATE_LIMIT_EXPONENTIAL_BACKOFF=true
export RAFT_RATE_LIMIT_JITTER=true
export RAFT_RATE_LIMIT_MAX_DELAY=60.0
```

### CLI Configuration

```bash
# Enable rate limiting with strategy
python raft.py \
  --rate-limit \
  --rate-limit-strategy adaptive \
  [other options]

# Use preset configuration
python raft.py \
  --rate-limit \
  --rate-limit-preset gpt-4 \
  [other options]

# Custom rate limits
python raft.py \
  --rate-limit \
  --rate-limit-requests-per-minute 60 \
  --rate-limit-tokens-per-minute 90000 \
  [other options]
```

### Rate Limiting Statistics

The RAFT Toolkit provides real-time statistics on rate limiting performance:

- **Request counts**: Total requests processed
- **Wait times**: Time spent waiting due to rate limits
- **Rate limit hits**: Number of rate limit errors encountered
- **Current effective rate**: Actual requests per minute being processed
- **Adaptive adjustments**: Rate adjustments for adaptive strategy

## 🚀 Performance Tuning

### Worker Configuration

```bash
# Optimal worker counts for different scenarios

# CPU-intensive tasks (local processing)
export WORKERS=$(nproc)                 # Use all CPU cores

# API-intensive tasks (OpenAI calls)
export WORKERS=4                        # Conservative for rate limits

# Memory-intensive tasks (large documents)
export WORKERS=2                        # Reduce for memory constraints

# High-throughput scenarios
export WORKERS=8                        # Increase for throughput
export BATCH_SIZE=20                    # Larger batches
```

### Memory Configuration

```bash
# Memory optimization
export CHUNK_SIZE=512                   # Smaller chunks = less memory
export BATCH_SIZE=5                     # Smaller batches = less memory
export MAX_CONCURRENT_JOBS=3            # Limit concurrent processing

# Large document handling
export STREAMING_MODE=true              # Stream processing
export TEMP_DIR=/fast/ssd/temp          # Use fast storage for temp files
```

### Caching Configuration

```python
# Redis caching configuration
CACHE_CONFIG = {
    "enabled": os.getenv("CACHE_ENABLED", "true").lower() == "true",
    "url": os.getenv("REDIS_URL", "redis://localhost:6379"),
    "ttl": int(os.getenv("CACHE_TTL", "3600")),
    "max_connections": int(os.getenv("CACHE_MAX_CONNECTIONS", "10")),
    "retry_on_timeout": True,
    "socket_keepalive": True,
    "socket_keepalive_options": {}
}

# Cache keys
CACHE_KEYS = {
    "embeddings": "embeddings:{hash}",
    "chunks": "chunks:{document_id}",
    "qa_pairs": "qa:{chunk_id}",
    "models": "models:{model_name}"
}
```

### Database Configuration

```python
# SQLite configuration for development
DATABASE_URL = "sqlite:///data/raft.db"

# PostgreSQL configuration for production
DATABASE_URL = "postgresql://user:pass@localhost/raftdb"

# Connection pool settings
DB_POOL_CONFIG = {
    "pool_size": int(os.getenv("DB_POOL_SIZE", "5")),
    "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "10")),
    "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),
    "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "3600"))
}
```

---

## 🔒 Security Configuration

### API Key Management

```bash
# Multiple API key support
API_KEYS=["key1","key2","key3"]         # Array of valid keys
API_KEY_ROTATION_INTERVAL=86400         # 24 hours

# Key validation
API_KEY_MIN_LENGTH=32                   # Minimum key length
API_KEY_REQUIRED_ENDPOINTS=["/api/"]    # Endpoints requiring keys
```

### Access Control

```python
# IP whitelist configuration
ALLOWED_IPS = os.getenv("ALLOWED_IPS", "").split(",") if os.getenv("ALLOWED_IPS") else []

# User authentication
AUTH_CONFIG = {
    "enabled": os.getenv("AUTH_ENABLED", "false").lower() == "true",
    "provider": os.getenv("AUTH_PROVIDER", "local"),  # local, oauth, ldap
    "session_timeout": int(os.getenv("SESSION_TIMEOUT", "3600")),
    "max_sessions_per_user": int(os.getenv("MAX_SESSIONS_PER_USER", "5"))
}

# OAuth configuration
OAUTH_CONFIG = {
    "client_id": os.getenv("OAUTH_CLIENT_ID"),
    "client_secret": os.getenv("OAUTH_CLIENT_SECRET"),
    "authorize_url": os.getenv("OAUTH_AUTHORIZE_URL"),
    "token_url": os.getenv("OAUTH_TOKEN_URL"),
    "userinfo_url": os.getenv("OAUTH_USERINFO_URL"),
    "scopes": os.getenv("OAUTH_SCOPES", "openid profile email").split()
}
```

### HTTPS Configuration

```nginx
# Nginx SSL configuration
server {
    listen 443 ssl http2;
    server_name raft.yourdomain.com;
    
    ssl_certificate /etc/ssl/certs/raft.crt;
    ssl_certificate_key /etc/ssl/private/raft.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    
    location / {
        proxy_pass http://raft-backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 🔍 LangWatch Observability

The RAFT Toolkit integrates with LangWatch for comprehensive LLM call tracking and performance monitoring.

### Basic Configuration

```bash
# Enable LangWatch integration
LANGWATCH_ENABLED=true

# Set your LangWatch API key
LANGWATCH_API_KEY=your-api-key

# Set project name for organizing traces
LANGWATCH_PROJECT=raft-toolkit

# Enable debug mode for detailed logging
LANGWATCH_DEBUG=false

# Set custom endpoint for self-hosted instances
LANGWATCH_ENDPOINT=https://api.langwatch.ai
```

### CLI Configuration

```bash
# Enable LangWatch via CLI
python raft.py \
  --langwatch-enabled \
  --langwatch-api-key your-api-key \
  --langwatch-project my-project \
  [other options]
```

### Tracked Operations

LangWatch integration tracks the following operations:

1. **Question Generation**: Tracks prompt, response, and performance metrics
2. **Answer Generation**: Tracks context, question, answer, and timing
3. **Embedding Generation**: Tracks model and timing information
4. **QA Dataset Generation**: Tracks comprehensive statistics

### Web Interface Integration

The web interface includes LangWatch configuration options:

1. **Enable/Disable**: Toggle LangWatch integration
2. **Project Name**: Set project for trace organization
3. **Debug Mode**: Enable detailed logging
4. **Custom Endpoint**: Configure for self-hosted instances

### Viewing Traces

Access your traces through the LangWatch dashboard:

1. Go to [LangWatch Dashboard](https://app.langwatch.ai)
2. Select your project
3. View traces, metrics, and performance data
4. Analyze prompt effectiveness and response quality

## 📊 Logging Configuration

### Log Levels and Formats

```python
# Logging configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "%(levelname)s - %(message)s"
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "json": {
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "detailed",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "json",
            "filename": "/app/logs/raft.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5
        }
    },
    "loggers": {
        "raft": {
            "level": "DEBUG",
            "handlers": ["console", "file"],
            "propagate": False
        },
        "uvicorn": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False
        }
    },
    "root": {
        "level": "WARNING",
        "handlers": ["console"]
    }
}
```

### Structured Logging

```python
import structlog

# Structured logging configuration
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# Usage
logger = structlog.get_logger()
logger.info("Processing started", 
           job_id="job-123", 
           file_name="document.pdf", 
           user_id="user-456")
```

### Log Aggregation

**Fluentd configuration** (fluent.conf):
```conf
<source>
  @type tail
  path /app/logs/raft.log
  pos_file /var/log/fluentd/raft.log.pos
  tag raft.application
  format json
</source>

<filter raft.**>
  @type record_transformer
  <record>
    hostname ${hostname}
    environment "#{ENV['ENVIRONMENT']}"
  </record>
</filter>

<match raft.**>
  @type elasticsearch
  host elasticsearch
  port 9200
  index_name raft-logs
  type_name application
</match>
```

---

## 🔍 Configuration Validation

### Configuration Schema

```python
from pydantic import BaseModel, Field
from typing import Optional, List

class APIConfig(BaseModel):
    openai_api_key: str = Field(..., min_length=1)
    openai_base_url: str = "https://api.openai.com/v1"
    openai_org_id: Optional[str] = None
    timeout: int = Field(60, ge=1, le=600)

class ProcessingConfig(BaseModel):
    workers: int = Field(4, ge=1, le=32)
    chunk_size: int = Field(512, ge=100, le=2048)
    questions_per_chunk: int = Field(5, ge=1, le=20)
    distractors: int = Field(1, ge=0, le=10)

class WebConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = Field(8000, ge=1, le=65535)
    debug: bool = False
    workers: int = Field(4, ge=1, le=16)

class RaftConfig(BaseModel):
    api: APIConfig
    processing: ProcessingConfig
    web: WebConfig
```

### Configuration Validation Script

```python
#!/usr/bin/env python3
"""Configuration validation script"""

import os
import sys
from pathlib import Path
import yaml
from pydantic import ValidationError

def validate_config(config_path: str = "config.yaml"):
    """Validate configuration file"""
    try:
        # Load configuration
        with open(config_path) as f:
            config_data = yaml.safe_load(f)
        
        # Validate with Pydantic
        config = RaftConfig(**config_data)
        
        # Additional validation
        validate_api_key(config.api.openai_api_key)
        validate_directories(config)
        validate_models(config)
        
        print("✅ Configuration is valid")
        return True
        
    except FileNotFoundError:
        print(f"❌ Configuration file not found: {config_path}")
        return False
    except ValidationError as e:
        print(f"❌ Configuration validation failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def validate_api_key(api_key: str):
    """Validate API key format"""
    if not api_key.startswith("sk-"):
        raise ValueError("OpenAI API key must start with 'sk-'")
    if len(api_key) < 40:
        raise ValueError("OpenAI API key appears to be too short")

def validate_directories(config):
    """Validate directory permissions"""
    dirs = [
        config.web.upload_dir,
        config.storage.data_dir,
        config.storage.output_dir,
        config.storage.temp_dir
    ]
    
    for dir_path in dirs:
        if not os.access(dir_path, os.W_OK):
            raise ValueError(f"Directory not writable: {dir_path}")

if __name__ == "__main__":
    config_file = sys.argv[1] if len(sys.argv) > 1 else "config.yaml"
    if validate_config(config_file):
        sys.exit(0)
    else:
        sys.exit(1)
```

---

## 📚 Configuration Examples

### Development Environment

**.env.development**:
```bash
# Development settings
WEB_DEBUG=true
WEB_RELOAD=true
WEB_WORKERS=1
LOG_LEVEL=DEBUG
WORKERS=2

# Development API (if using Ollama)
OPENAI_API_BASE_URL=http://localhost:11434/v1
OPENAI_API_KEY=ollama-anything

# Development storage
DATA_DIR=./dev-data
OUTPUT_DIR=./dev-outputs
UPLOAD_DIR=./dev-uploads
```

### Production Environment

**.env.production**:
```bash
# Production settings
WEB_DEBUG=false
WEB_RELOAD=false
WEB_WORKERS=4
LOG_LEVEL=INFO
WORKERS=8

# Production API
OPENAI_API_KEY=sk-real-production-key

# Production security
API_KEY_REQUIRED=true
CORS_ORIGINS=["https://yourdomain.com"]
ALLOWED_IPS=["10.0.0.0/8","172.16.0.0/12"]

# Production storage
DATA_DIR=/app/data
OUTPUT_DIR=/app/outputs
UPLOAD_DIR=/tmp/uploads
REDIS_URL=redis://redis:6379/0
```

### Testing Environment

**.env.testing**:
```bash
# Testing settings
WEB_DEBUG=true
LOG_LEVEL=DEBUG
WORKERS=1

# Testing API (mock)
OPENAI_API_KEY=test-key
USE_MOCK_API=true

# Testing storage
DATA_DIR=./test-data
OUTPUT_DIR=./test-outputs
UPLOAD_DIR=./test-uploads

# Testing database
DATABASE_URL=sqlite:///:memory:
REDIS_URL=redis://localhost:6379/1
```

---

For more configuration examples and templates, see the `config/` directory in the repository.