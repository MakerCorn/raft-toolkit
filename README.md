# RAFT Toolkit

> **Retrieval Augmentation Fine-Tuning Toolkit**  

## 🚀 Overview

### What is RAFT?

**RAFT (Retrieval Augmentation Fine-Tuning)** is a technique that trains language models to better utilize retrieved documents when answering questions. Unlike traditional RAG systems that rely on frozen pre-trained models, RAFT fine-tunes models specifically for document-based reasoning tasks.

The RAFT Toolkit automates the creation of training datasets by generating `{question, answer, documents}` triplets from your documents, enabling you to fine-tune models that excel at retrieval-augmented generation tasks.

#### RAFT Training Process Flow

```mermaid
graph TD
    A[📄 Input Sources<br/>Local, S3, SharePoint] --> B{🔧 RAFT Toolkit<br/>CLI or Web UI}
    
    B --> C[📑 Document Chunking<br/>Semantic/Fixed/Sentence]
    C --> D[❓ Question Generation<br/>LLM-powered Q&A creation]
    D --> E[📝 Answer Generation<br/>Context-based responses]
    E --> F[🎭 Distractor Addition<br/>Irrelevant docs for robustness]
    F --> G[📊 Training Dataset<br/>JSONL/Parquet format]
    
    G --> H[🤖 Model Fine-tuning<br/>OpenAI/HuggingFace/Azure]
    H --> I[🎯 Fine-tuned Model<br/>Domain-optimized LLM]
    
    G --> J{🛠️ Analysis Tools}
    J --> K[📈 Dataset Evaluation<br/>eval.py]
    J --> L[💬 Answer Generation<br/>answer.py]  
    J --> M[🔍 PromptFlow Analysis<br/>pfeval_*.py]
    
    K --> N[📊 Performance Metrics]
    L --> O[🔄 Model Comparison]
    M --> P[📋 Quality Assessment]
    
    N --> Q[✨ Production Model<br/>Optimized for RAG tasks]
    O --> Q
    P --> Q
    
    style B fill:#e1f5fe,color:#000000
    style J fill:#f3e5f5,color:#000000
    style Q fill:#e8f5e8,color:#000000
```

**🔧 Toolkit Components:**
- **Core Engine**: Document processing and dataset generation
- **Analysis Tools**: Six evaluation and comparison utilities  
- **Web Interface**: Visual workflow management and monitoring
- **CLI Tools**: Scriptable automation and batch processing

### RAFT vs Traditional RAG: Key Differences

| Aspect | Traditional RAG | RAFT Fine-Tuning |
|--------|-----------------|-------------------|
| **Model Training** | Uses frozen pre-trained models | Fine-tunes models on domain-specific data |
| **Document Utilization** | May ignore or misuse retrieved documents | Learns to effectively use retrieved information |
| **Performance** | Depends on base model's retrieval reasoning | Optimized for specific document types/domains |
| **Latency** | Requires runtime retrieval + inference | Faster inference with better document integration |
| **Setup Complexity** | Lower initial setup | Higher setup (requires training data generation) |
| **Customization** | Limited to prompt engineering | Deep customization through fine-tuning |

### Advantages of RAFT Fine-Tuning

**✅ Performance Benefits:**
- **Improved Document Reasoning**: Models learn to better understand and utilize retrieved documents
- **Domain Adaptation**: Optimized for specific document types (legal, medical, technical, etc.)
- **Reduced Hallucination**: Better grounding in provided context through training
- **Enhanced Factual Accuracy**: Explicit training on document-based question answering

**✅ Operational Benefits:**
- **Faster Inference**: No need for complex retrieval orchestration at runtime
- **Consistent Quality**: Predictable performance across similar document types
- **Cost Efficiency**: Smaller fine-tuned models can outperform larger general models

### When to Use RAFT vs Traditional RAG

**Use RAFT Fine-Tuning When:**
- You have consistent document types/formats
- Performance on document reasoning is critical
- You can invest time in data generation and training
- You need predictable, high-quality outputs
- Latency optimization is important

**Use Traditional RAG When:**
- Working with diverse, changing document types
- Quick prototyping or proof-of-concept needed
- Limited resources for training data generation
- Documents change frequently
- General-purpose question answering is sufficient

### The RAFT Fine-Tuning Process

#### 1. **Training Data Generation** (This Toolkit)
```bash
# Generate RAFT training dataset
python raft.py --datapath documents/ --output training_data/
```
- **Document Chunking**: Split documents into semantic chunks
- **Question Generation**: Create relevant questions for each chunk  
- **Answer Generation**: Generate accurate answers using the source chunk
- **Distractor Addition**: Include irrelevant documents to improve robustness
- **Format Conversion**: Export in format suitable for fine-tuning platforms

#### Chunking Strategies & Configuration

Effective chunking is critical for RAFT success. Choose your strategy based on document type and use case:

##### **📏 Chunk Size Guidelines**

| **Document Type** | **Recommended Chunk Size** | **Reasoning** |
|------------------|---------------------------|----------------|
| **Technical Documentation** | 300-512 tokens | Preserves complete concepts and code examples |
| **Legal Documents** | 512-768 tokens | Maintains clause/section coherence |
| **Medical Literature** | 256-512 tokens | Balances detail with focused topics |
| **Research Papers** | 512-1024 tokens | Captures complete paragraphs and findings |
| **FAQ/Knowledge Base** | 128-256 tokens | Each chunk = one question/topic |
| **News Articles** | 256-512 tokens | Preserves story coherence |

##### **🔄 Overlap Strategy**

| **Overlap %** | **Use Case** | **Trade-offs** |
|--------------|-------------|----------------|
| **0%** | Distinct topics, FAQ | Clean separation, no redundancy |
| **10-20%** | Technical docs | Minimal context preservation |
| **20-40%** | Narrative content | Good context flow, some redundancy |
| **40-60%** | Complex topics | Maximum context, high redundancy |

```bash
# Low overlap for distinct topics
--chunking-params '{"overlap": 0}'

# Medium overlap for connected content  
--chunking-params '{"overlap": 100}'  # ~20% of 512 tokens

# High overlap for complex documents
--chunking-params '{"overlap": 200}'  # ~40% of 512 tokens
```

##### **❓ Questions Per Chunk**

| **Questions/Chunk** | **Use Case** | **Quality vs Quantity** |
|-------------------|-------------|------------------------|
| **1-2** | High-quality, focused datasets | Maximum quality, minimal redundancy |
| **3-5** | Balanced approach (recommended) | Good quality, reasonable coverage |
| **6-10** | Comprehensive coverage | Risk of lower quality questions |

```bash
# Focused, high-quality
--questions 2 --chunk_size 512

# Balanced approach (recommended)
--questions 5 --chunk_size 384

# Comprehensive coverage
--questions 8 --chunk_size 256
```

##### **🎭 Distractor Configuration**

| **Distractors** | **Training Benefit** | **Dataset Size Impact** |
|----------------|---------------------|------------------------|
| **2-3** | Basic robustness | Moderate increase |
| **4-6** | Strong robustness (recommended) | 5-7x dataset size |
| **7-10** | Maximum robustness | 8-11x dataset size |

```bash
# Recommended configuration
--distractors 4 --questions 5 --chunk_size 512

# Resource-constrained
--distractors 2 --questions 3 --chunk_size 384

# Maximum robustness
--distractors 6 --questions 3 --chunk_size 256
```

##### **⚙️ Strategy-Specific Recommendations**

**🧠 Semantic Chunking** (Recommended)
```bash
--chunking-strategy semantic --chunk_size 512 \
--chunking-params '{"overlap": 50, "min_chunk_size": 200}'
```
- **Best for**: Most document types, preserves meaning
- **Overlap**: 50-100 tokens for context preservation
- **Min size**: 200 tokens to ensure meaningful chunks

**📐 Fixed Chunking**
```bash
--chunking-strategy fixed --chunk_size 384 \
--chunking-params '{"overlap": 75}'
```
- **Best for**: Consistent processing, structured documents
- **Overlap**: 15-25% of chunk size
- **Use when**: Semantic understanding less critical

**📝 Sentence Chunking**
```bash
--chunking-strategy sentence --chunk_size 256 \
--chunking-params '{"overlap": 0}'
```
- **Best for**: Natural language, narrative content
- **Overlap**: Usually 0 (sentence boundaries are natural breaks)
- **Chunk size**: Maximum tokens per chunk (actual size varies)

#### 2. **Model Fine-Tuning**
```bash
# Example with OpenAI fine-tuning
openai api fine_tunes.create \
  -t training_data.jsonl \
  -m gpt-3.5-turbo \
  --suffix "raft-medical-docs"
```
- **Platform Selection**: Choose fine-tuning platform (OpenAI, HuggingFace, etc.)
- **Model Selection**: Start with instruction-tuned base models
- **Training Configuration**: Set learning rate, epochs, batch size
- **Validation**: Monitor training metrics and validation performance

#### 3. **Evaluation & Iteration**
```bash
# Evaluate fine-tuned model
python tools/eval.py --model ft:gpt-3.5-turbo:suffix --question-file eval.jsonl
```
- **Performance Testing**: Compare against baseline models
- **Error Analysis**: Identify common failure patterns
- **Data Augmentation**: Generate additional training examples for weak areas
- **Iterative Improvement**: Refine dataset and retrain

### Best Practices for RAFT Training Data

#### Document Preparation
- **Quality Over Quantity**: Use high-quality, authoritative documents
- **Consistent Format**: Maintain consistent document structure and formatting
- **Domain Relevance**: Focus on documents representative of target use cases
- **Optimal Length**: Use documents of 1,000-10,000 tokens for best chunking results

#### Question Generation
- **Diverse Question Types**: Include factual, analytical, and inferential questions
- **Appropriate Difficulty**: Match question complexity to intended use case
- **Natural Language**: Generate questions that users would realistically ask
- **Coverage**: Ensure questions cover all important document sections

#### Dataset Composition
- **Distractor Ratio**: Use 3-5 distractor documents per training example
- **Oracle Probability**: Include source document 80-100% of the time
- **Balanced Difficulty**: Mix easy, medium, and hard questions
- **Size Guidelines**: Aim for 1,000-10,000 training examples minimum

#### Quality Assurance
- **Manual Review**: Sample and manually verify question-answer pairs
- **Consistency Checks**: Ensure answers are actually derivable from context
- **Bias Detection**: Check for dataset biases and systematic errors
- **Evaluation Split**: Reserve 10-20% of data for evaluation

RAFT takes an input document and creates a dataset of `{question, answer, documents}` triplets for fine-tuning LLMs on retrieval-augmented tasks. Now available with both **CLI** and **Web UI** interfaces plus comprehensive **evaluation tools**!

**Features:**
- 📊 **Dual Interface**: Command-line tool and modern web interface
- 🛠️ **Analysis Tools Suite**: Evaluation, answer generation, and PromptFlow analysis
- 🏗️ **12-Factor Architecture**: Cloud-native, scalable design
- 📄 **Multi-Format Support**: PDF, TXT, JSON, PPTX, and API documentation
- ☁️ **Multiple Input Sources**: Local files, Amazon S3, SharePoint Online
- 🔐 **Enterprise Authentication**: AWS credentials, Azure AD, SharePoint integration
- 🎯 **Flexible Output**: HuggingFace, OpenAI completion/chat, and evaluation formats
- ⚡ **Parallel Processing**: Configurable workers for optimal performance
- 📋 **Enhanced Logging**: Production-ready logging with progress tracking, external service integration (Sentry, DataDog), and structured output
- 🧪 **Comprehensive Testing**: Unit, integration, API, and CLI test suites
- 🐳 **Container Ready**: Docker support for easy deployment
- 🚀 **Kubernetes Ready**: Complete Kubernetes deployment configurations

## 📦 Installation

### Prerequisites

- Python 3.9+ (3.11 recommended)
- OpenAI API key (or Azure OpenAI credentials)
- Optional: AWS credentials for S3 input sources
- Optional: Azure AD app registration for SharePoint input sources
- Optional: Docker & Docker Compose for containerized deployment

### 🚀 Quick Start (Recommended)

```bash
# Clone the repository
git clone https://github.com/your-repo/raft-toolkit.git
cd raft-toolkit

# Set up environment
cp .env.example .env
# Edit .env with your OpenAI API key

# Install core dependencies
pip install -r requirements.txt

# Optional: Install cloud storage dependencies
pip install -r requirements-k8s.txt  # For S3 and enhanced cloud features

# Optional: Install for development
pip install -e ".[all]"  # Install all optional dependencies

# Test installation
python run_tests.py --unit --fast

# Start web interface
python run_web.py
# Open http://localhost:8000
```

### 🐳 Docker Installation

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

### 📋 Detailed Installation

#### Core Dependencies
```bash
# Essential packages for basic functionality
pip install -r requirements.txt
```

#### Web Interface (Optional)
```bash
# For full web UI experience
pip install -r requirements-web.txt
```

#### Development & Testing (Optional)
```bash
# For contributors and advanced users
pip install -r requirements-test.txt

# Run full test suite
python run_tests.py --coverage --output-dir ./test-results
```

#### Multi-Target Docker Builds
```bash
# Production deployment
docker build --target production -t raft-toolkit:prod .

# Development with debugging
docker build --target development -t raft-toolkit:dev .

# CLI-only lightweight image
docker build --target cli -t raft-toolkit:cli .

# Testing environment
docker build --target testing -t raft-toolkit:test .
```

### Environment Setup

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
```

### 🌐 Kubernetes Deployment

For production deployments, RAFT Toolkit supports Kubernetes across major cloud providers:

```bash
# Azure Kubernetes Service (AKS)
export OPENAI_API_KEY="your-openai-api-key"
./k8s/scripts/deploy-aks.sh

# Amazon Elastic Kubernetes Service (EKS)  
export OPENAI_API_KEY="your-openai-api-key"
./k8s/scripts/deploy-eks.sh

# Google Kubernetes Engine (GKE)
export OPENAI_API_KEY="your-openai-api-key"
export PROJECT_ID="your-gcp-project-id"
./k8s/scripts/deploy-gks.sh
```

**Kubernetes Features:**
- **🔄 Auto-scaling**: Horizontal and vertical pod autoscaling
- **🛡️ Security**: Non-root containers, network policies, RBAC
- **📊 Monitoring**: Health checks, Prometheus metrics, logging
- **💾 Storage**: Persistent volumes for input/output data
- **🌐 Ingress**: Load balancing and SSL termination
- **🔧 Configuration**: Environment-based config management

See the complete [Kubernetes Deployment Guide](docs/KUBERNETES.md) for detailed instructions.

## ⚙️ Main Arguments

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

### 🚦 Rate Limiting Arguments

- **`--rate-limit`**: Enable rate limiting for API requests (default: disabled)
- **`--rate-limit-strategy`**: Rate limiting strategy (`fixed_window`, `sliding_window` [default], `token_bucket`, `adaptive`)
- **`--rate-limit-preset`**: Use preset configuration (`openai_gpt4`, `openai_gpt35_turbo`, `azure_openai_standard`, `anthropic_claude`, `conservative`, `aggressive`)
- **`--rate-limit-requests-per-minute`**: Maximum requests per minute (overrides preset)
- **`--rate-limit-tokens-per-minute`**: Maximum tokens per minute (overrides preset)
- **`--rate-limit-max-burst`**: Maximum burst requests allowed (overrides preset)
- **`--rate-limit-max-retries`**: Maximum retries on rate limit errors (default: 3)

## 🚦 Rate Limiting for Cloud AI Services

The RAFT Toolkit includes comprehensive rate limiting to handle the constraints imposed by cloud-based AI services. Rate limiting is **disabled by default** to maintain backward compatibility, but is highly recommended for production use to avoid hitting API limits and reduce costs.

### Why Rate Limiting Matters

**Common Issues Without Rate Limiting:**
- API rate limit errors (HTTP 429) causing processing failures
- Unexpected costs from burst API usage
- Inconsistent processing times due to throttling
- Failed batches requiring expensive reprocessing

**Benefits of Rate Limiting:**
- **Predictable Costs**: Control API spending with token and request limits
- **Reliable Processing**: Avoid rate limit errors through intelligent throttling
- **Optimized Performance**: Adaptive strategies adjust to service response times
- **Better Monitoring**: Detailed statistics on API usage and throttling

### Quick Start Examples

#### Using Preset Configurations
```bash
# OpenAI GPT-4 with recommended limits
python raft.py --datapath docs/ --output training_data/ \
  --rate-limit --rate-limit-preset openai_gpt4

# Azure OpenAI with conservative limits  
python raft.py --datapath docs/ --output training_data/ \
  --rate-limit --rate-limit-preset azure_openai_standard

# Anthropic Claude with aggressive processing
python raft.py --datapath docs/ --output training_data/ \
  --rate-limit --rate-limit-preset anthropic_claude
```

#### Custom Rate Limiting
```bash
# Custom limits for your specific API tier
python raft.py --datapath docs/ --output training_data/ \
  --rate-limit \
  --rate-limit-strategy sliding_window \
  --rate-limit-requests-per-minute 100 \
  --rate-limit-tokens-per-minute 5000 \
  --rate-limit-max-burst 20

# Adaptive rate limiting (adjusts based on response times)
python raft.py --datapath docs/ --output training_data/ \
  --rate-limit --rate-limit-strategy adaptive \
  --rate-limit-requests-per-minute 200
```

### Rate Limiting Strategies

#### 1. **Sliding Window** (Recommended)
- **Best for**: Most production use cases
- **How it works**: Tracks requests over a rolling time window
- **Advantages**: Smooth rate distribution, handles bursts well
```bash
--rate-limit-strategy sliding_window
```

#### 2. **Fixed Window**
- **Best for**: Simple rate limiting scenarios
- **How it works**: Resets limits at fixed intervals (every minute)
- **Advantages**: Simple to understand, predictable behavior
```bash
--rate-limit-strategy fixed_window
```

#### 3. **Token Bucket**
- **Best for**: Bursty workloads with occasional high throughput needs
- **How it works**: Accumulates "tokens" over time, consumes them for requests
- **Advantages**: Allows controlled bursts above average rate
```bash
--rate-limit-strategy token_bucket
```

#### 4. **Adaptive**
- **Best for**: Unknown or variable API performance
- **How it works**: Automatically adjusts rate based on response times
- **Advantages**: Self-tuning, optimizes for service performance
```bash
--rate-limit-strategy adaptive
```

### Available Presets

| Preset | Service | Requests/min | Tokens/min | Burst | Use Case |
|--------|---------|--------------|------------|-------|----------|
| `openai_gpt4` | OpenAI GPT-4 | 500 | 10,000 | 50 | Production GPT-4 |
| `openai_gpt35_turbo` | OpenAI GPT-3.5 Turbo | 3,500 | 90,000 | 100 | High-throughput GPT-3.5 |
| `azure_openai_standard` | Azure OpenAI | 120 | 6,000 | 20 | Standard Azure tier |
| `anthropic_claude` | Anthropic Claude | 1,000 | 100,000 | 50 | Claude API |
| `conservative` | Any service | 60 | 2,000 | 10 | Safe/cautious processing |
| `aggressive` | Any service | 1,000 | 50,000 | 100 | Fast processing |

### Environment Configuration

Set rate limiting via environment variables for consistent configuration across deployments:

```bash
# Enable rate limiting
export RAFT_RATE_LIMIT_ENABLED=true
export RAFT_RATE_LIMIT_PRESET=openai_gpt4

# Custom configuration
export RAFT_RATE_LIMIT_ENABLED=true
export RAFT_RATE_LIMIT_STRATEGY=sliding_window
export RAFT_RATE_LIMIT_REQUESTS_PER_MINUTE=200
export RAFT_RATE_LIMIT_TOKENS_PER_MINUTE=8000
export RAFT_RATE_LIMIT_MAX_BURST=30
export RAFT_RATE_LIMIT_MAX_RETRIES=5
```

### Rate Limiting Statistics

When rate limiting is enabled, the toolkit provides detailed statistics:

```
Rate Limiting Statistics:
  Strategy: sliding_window
  Total Wait Time: 45.2s
  Rate Limit Hits: 12
  Average Response Time: 1.85s
  Current Rate Limit: 450.0 req/min
```

**Understanding the Statistics:**
- **Total Wait Time**: Time spent waiting due to rate limiting
- **Rate Limit Hits**: Number of times rate limiting delayed requests
- **Average Response Time**: Mean API response time (for adaptive tuning)
- **Current Rate Limit**: Effective rate limit (may adapt based on performance)

### Advanced Configuration

#### Fine-Tuning Retry Behavior
```bash
# Aggressive retry with exponential backoff
python raft.py --datapath docs/ --output training_data/ \
  --rate-limit --rate-limit-preset openai_gpt4 \
  --rate-limit-max-retries 5

# Conservative approach (default: 3 retries)
python raft.py --datapath docs/ --output training_data/ \
  --rate-limit --rate-limit-preset conservative
```

#### Token-Aware Rate Limiting
The toolkit automatically estimates token usage for more accurate rate limiting:
- **Question generation**: ~15 tokens per question + context size
- **Answer generation**: ~150 tokens output + question + context
- **Adaptive estimation**: Learns from actual usage patterns

### Best Practices

#### Production Deployments
1. **Always enable rate limiting**: `--rate-limit` or `RAFT_RATE_LIMIT_ENABLED=true`
2. **Start with presets**: Use service-specific presets then fine-tune
3. **Monitor statistics**: Watch for high wait times or frequent rate limit hits
4. **Use adaptive strategy**: For unknown or variable service performance

#### Development and Testing
1. **Use conservative preset**: Avoid accidental high usage during development
2. **Test with rate limiting**: Ensure your workflows work with production settings
3. **Monitor costs**: Track token usage with rate limiting statistics

#### Cost Optimization
```bash
# Very conservative for cost control
python raft.py --datapath docs/ --output training_data/ \
  --rate-limit --rate-limit-preset conservative \
  --questions 3 --workers 1

# Balanced approach for production
python raft.py --datapath docs/ --output training_data/ \
  --rate-limit --rate-limit-preset openai_gpt4 \
  --workers 2
```

## 🧪 Testing & Release Infrastructure

### Recent Major Improvements (v1.0.1)

The RAFT Toolkit now includes a robust, fully-automated testing and release infrastructure:

#### ✅ Complete Test Suite Reliability
- **43/43 unit tests passing**: All unit test failures have been resolved
- **Fixed critical test issues**: Mock paths, environment isolation, token caching
- **Cross-platform testing**: Linux, macOS, and Windows support
- **Multi-Python version testing**: Python 3.9, 3.10, and 3.11

#### 🚀 Automated Release Pipeline
- **Tag-triggered releases**: Create releases by pushing version tags
- **Build system fixes**: Resolved package discovery and build configuration issues
- **GitHub Actions integration**: Automated building, testing, and publishing
- **Release tools**: Interactive release script for safe version management

#### 🛠️ Enhanced Developer Experience
- **Release script**: `./scripts/create_release.sh` for guided release creation
- **Build validation**: Local testing before CI/CD deployment
- **Comprehensive documentation**: Step-by-step guides for releases and testing

#### 📦 Improved Build System
- **Fixed package discovery**: Resolved "Multiple top-level packages" setuptools error
- **Modern pyproject.toml**: Complete build configuration with proper dependencies
- **Package optimization**: Smaller builds excluding unnecessary files (tests, docs, notebooks)
- **Entry points**: Proper CLI script configuration for `raft` and `raft-web` commands

#### Example: Creating a Release
```bash
# Interactive release creation (recommended)
./scripts/create_release.sh

# Manual tag creation (advanced)
git tag -a v1.0.2 -m "Release v1.0.2"
git push origin v1.0.2
```

See [`docs/RELEASES.md`](docs/RELEASES.md) for the complete release management guide.

#### 🔧 Testing Improvements Details

**Unit Test Fixes (13 tests resolved):**
- **Import path corrections**: Fixed LangChain embeddings mock paths
- **Attribute alignment**: Corrected `completion_count` → `calls` mismatches  
- **Environment isolation**: Proper cleanup between tests
- **File handling**: Temporary file creation for validation tests
- **Token caching**: Global cache clearing for authentication tests

**Build Configuration Fixes:**
- **Package inclusion**: Explicit control over what gets built (`core`, `cli`, `web`, `tools`)
- **Dependency management**: Proper setuptools configuration
- **Entry point registration**: Automated CLI script installation
- **Metadata compliance**: Modern SPDX license format

**Release Workflow Fixes:**
- **Permission handling**: Proper GitHub token usage
- **Tag validation**: Verify tags exist before release creation
- **Trigger logic**: Only create releases for actual version tags
- **Error handling**: Better debugging and validation messages

**CI/CD Pipeline Reliability:**
- **Build → Test → Release**: Proper dependency chain prevents broken releases
- **Multi-platform support**: Testing across different OS and Python versions
- **Artifact generation**: Automated Docker images, Python packages, and documentation
- **Quality gates**: All tests must pass before any release is created

### Test Runner

The RAFT Toolkit includes a comprehensive test suite with configurable directories:

```bash
# Run all tests
python run_tests.py

# Run specific test types
python run_tests.py --unit              # Unit tests only
python run_tests.py --integration       # Integration tests
python run_tests.py --api              # API tests
python run_tests.py --cli              # CLI tests

# With coverage reporting
python run_tests.py --coverage --output-dir ./test-results

# Fast tests (skip slow ones)
python run_tests.py --fast

# Parallel execution
python run_tests.py --parallel 4
```

### Configurable Test Directories

Configure test directories via CLI arguments or environment variables:

```bash
# Custom directories via CLI
python run_tests.py --integration \
  --output-dir ./ci-results \
  --temp-dir /tmp/fast-ssd \
  --coverage-dir ./coverage

# Via environment variables
export TEST_OUTPUT_DIR=./my-results
export TEST_TEMP_DIR=/tmp/my-temp
export TEST_COVERAGE_DIR=./coverage
python run_tests.py --coverage

# Docker testing with custom directories
export HOST_TEST_RESULTS_DIR=/shared/test-results
docker compose -f docker-compose.test.yml up
```

See [`docs/TEST_DIRECTORIES.md`](docs/TEST_DIRECTORIES.md) for complete configuration guide.

### Dependency Troubleshooting

If you encounter dependency conflicts during installation:

```bash
# Run dependency checker
python scripts/check_dependencies.py

# Check for conflicts
pip check

# Clean installation
pip install -r requirements.txt --force-reinstall
```

See [`docs/DEPENDENCY_TROUBLESHOOTING.md`](docs/DEPENDENCY_TROUBLESHOOTING.md) for comprehensive troubleshooting guide.

### Docker Testing

```bash
# Run tests in Docker environment
docker compose -f docker-compose.test.yml up --abort-on-container-exit

# Specific test suites
docker compose -f docker-compose.test.yml run raft-test-unit
docker compose -f docker-compose.test.yml run raft-test-integration
```

### Code Quality

```bash
# Install code quality tools
pip install -r requirements-test.txt

# Run linting
flake8 .
black --check .
isort --check-only .
mypy .

# Auto-format code
black .
isort .
```

### Security Scanning

```bash
# Install security tools
pip install bandit safety

# Run security scans
bandit -r . -f json -o security-report.json
safety scan -r requirements.txt
```

## 🚀 CI/CD Integration

### GitHub Actions Workflows

The project includes comprehensive CI/CD pipelines:

**Build Pipeline** (`Build → Test → Release`):
- 🔍 **Code Quality**: Linting with flake8, black, isort
- 🏗️ **Multi-Target Builds**: Production, development, CLI, testing images
- 🔒 **Security Scanning**: Bandit, Safety, Trivy vulnerability scans
- 📦 **Container Registry**: Automatic publishing to GitHub Container Registry

**Test Pipeline**:
- 🧪 **Comprehensive Testing**: Unit, integration, API, CLI, Docker tests
- 📊 **Coverage Reporting**: Codecov integration with detailed metrics
- 🐍 **Multi-Python Support**: Testing on Python 3.9, 3.10, 3.11
- ⚡ **Parallel Execution**: Optimized test execution with dependency management

**Security Pipeline**:
- 🛡️ **Dependency Scanning**: Daily automated vulnerability checks
- 📋 **License Compliance**: Automated license compatibility verification
- 🔄 **Auto-Updates**: Automated dependency update PRs

### Environment Variables for CI/CD

```bash
# Test configuration
TEST_OUTPUT_DIR=/workspace/test-results
TEST_TEMP_DIR=/workspace/temp
TEST_COVERAGE_DIR=/workspace/coverage

# Docker configuration
HOST_TEST_RESULTS_DIR=/tmp/ci-results
HOST_COVERAGE_DIR=/tmp/ci-coverage
HOST_TEMP_DIR=/tmp/ci-temp

# Security scanning
ENABLE_SECURITY_SCANS=true
UPLOAD_SARIF=true
```

### Pipeline Configuration Examples

**GitLab CI**:
```yaml
test:
  script:
    - pip install -r requirements-test.txt
    - python run_tests.py --coverage --output-dir ./test-results
  artifacts:
    reports:
      junit: test-results/junit.xml
      coverage_report:
        coverage_format: cobertura
        path: test-results/coverage.xml
```

**Jenkins**:
```groovy
pipeline {
    agent any
    environment {
        TEST_OUTPUT_DIR = "${WORKSPACE}/test-results"
        TEST_TEMP_DIR = "/tmp/jenkins-${BUILD_ID}"
    }
    stages {
        stage('Test') {
            steps {
                sh 'python run_tests.py --coverage'
                publishTestResults testResultsPattern: 'test-results/junit.xml'
                publishCoverage adapters: [coberturaAdapter('test-results/coverage.xml')]
            }
        }
    }
}
```

## 📝 Azure OpenAI Support

To enable Azure OpenAI support, set the environment variable `AZURE_OPENAI_ENABLED=1` (or `true`).

You must also set the appropriate Azure OpenAI environment variables (e.g., `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_KEY`, etc.) as required by your deployment.

Example for zsh:

```zsh
export AZURE_OPENAI_ENABLED=1
export AZURE_OPENAI_ENDPOINT="https://your-azure-endpoint.openai.azure.com/"
export AZURE_OPENAI_KEY="your-azure-api-key"
```

If `AZURE_OPENAI_ENABLED` is not set or is set to `0`/`false`, the toolkit will use standard OpenAI API endpoints and keys.

## ⚡ Quick Start

### 🖥️ Command Line Interface

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

### 🌐 Web Interface

```bash
# Start the web server
python run_web.py

# Or with custom configuration
python run_web.py --host 0.0.0.0 --port 8080 --debug

# Open http://localhost:8000 in your browser
```

**Web UI Features:**
- 📤 **Dataset Generation**: Drag & drop file upload with visual configuration
- 🛠️ **Analysis Tools**: Six powerful evaluation and analysis tools
- ⚙️ **Visual Configuration**: Interactive forms for all settings
- 👀 **Live Preview**: See processing estimates before running
- 📊 **Job Management**: Track multiple processing jobs with real-time updates
- 📥 **Download Results**: Direct download of generated datasets and analysis results
- 📈 **Results Visualization**: Comprehensive display of metrics and statistics

**Analysis Tools Available:**
- **Dataset Evaluation**: Evaluate model performance with configurable metrics
- **Answer Generation**: Generate high-quality answers using various LLMs
- **PromptFlow Analysis**: Multi-dimensional evaluation (relevance, groundedness, fluency, coherence)
- **Dataset Analysis**: Statistical analysis and quality metrics
- **Model Comparison**: Side-by-side performance comparison
- **Batch Processing**: Automated workflows for multiple datasets

### 🛠️ Standalone Tools (CLI)

The `tools/` directory contains powerful standalone evaluation utilities:

```bash
# Navigate to tools directory
cd tools/

# Install tool dependencies
pip install -r requirements.txt

# Run dataset evaluation
python eval.py --question-file dataset.jsonl --answer-file answers.jsonl

# Generate answers for evaluation
python answer.py --input questions.jsonl --output answers.jsonl --workers 8

# Run PromptFlow evaluation
python pfeval_chat.py --input dataset.jsonl --output evaluation.json
```

See the [tools/README.md](tools/README.md) for comprehensive documentation on all available tools.

## 🧩 Chunking Options

- **Semantic** (default): Embedding-based, best for context preservation.
- **Fixed**: Splits by token count (`--chunk_size`).
- **Sentence**: Splits by sentence boundaries, each chunk ≤ `--chunk_size` tokens.

**Extra parameters for semantic chunking** (via `--chunking-params`):

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

## 📊 Enhanced CLI Logging

The RAFT Toolkit features a comprehensive logging system designed for production use, debugging, and integration with external monitoring tools.

### 🎯 **Logging Features**

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

### 🚀 **Quick Start - Enhanced Logging**

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

### 🔧 **Progress Tracking**

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

### 🔍 **Distributed Tracing**

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

### 📈 **Contextual Logging**

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

### 🛠️ **Optional Dependencies**

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
```

**Note:** All dependencies are optional. The system gracefully falls back to:
- Standard Python logging if enhanced libraries aren't installed
- UUID-based trace IDs if OpenTelemetry isn't available
- Basic formatters if coloredlogs/structlog aren't available

### 📁 **Log Files and Rotation**

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

### 🚀 **Production Deployment**

**Docker with Enhanced Logging:**
```yaml
# docker-compose.yml
version: '3.8'
services:
  raft-toolkit:
    environment:
      RAFT_LOG_LEVEL: INFO
      RAFT_LOG_FORMAT: json
      RAFT_LOG_OUTPUT: both
      RAFT_SENTRY_DSN: ${SENTRY_DSN}
    volumes:
      - ./logs:/app/logs
```

**Kubernetes ConfigMap:**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: raft-logging-config
data:
  RAFT_LOG_LEVEL: "INFO"
  RAFT_LOG_FORMAT: "json"
  RAFT_LOG_OUTPUT: "both"
  RAFT_LOG_STRUCTURED: "true"
```

### 📋 **Log Analysis Examples**

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

## 📝 Workflow

1. **Chunk Generation**: Document is split into chunks (see options above).
2. **QA Generation**: LLM generates N questions and answers per chunk.
3. **Distractor Appending**: Random chunks are added as distractors for each QA pair.
4. **Dataset Export**: Data is saved in the specified format for fine-tuning.

## 💡 Tips

- You can use a `.env` file for OpenAI/Azure keys.
- For Azure, set deployment names with `--completion-model` and `--embedding-model`.
- Use `--chunking-strategy` and `--chunking-params` for best results on your data.

## 📚 File Utilities

- **Split large JSONL files:**

  ```python
  from core.utils.file_utils import split_jsonl_file
  split_jsonl_file('yourfile.jsonl', max_size=50_000_000)
  ```

- **Extract random rows:**

  ```python
  from core.utils.file_utils import extract_random_jsonl_rows
  extract_random_jsonl_rows('yourfile.jsonl', 100, 'sampled_output.jsonl')
  ```

## 🏗️ Architecture

This toolkit follows **12-factor app principles** with a modular architecture:

```
raft-toolkit/
├── core/                    # Shared business logic
│   ├── config.py           # Configuration management
│   ├── models.py           # Data models
│   ├── raft_engine.py      # Main orchestration
│   └── services/           # Business services
├── cli/                    # Command-line interface
├── web/                    # Web interface & API
├── run_cli.py             # CLI entry point
├── run_web.py             # Web entry point
└── docker-compose.yml     # Container orchestration
```

**Benefits:**
- ✅ **Separation of Concerns**: UI and business logic decoupled
- ✅ **Environment Parity**: Same code for dev/prod
- ✅ **Configuration via Environment**: 12-factor compliance
- ✅ **Horizontal Scaling**: Stateless design
- ✅ **Container Ready**: Docker & Kubernetes support

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed technical documentation.

## 🧪 Testing

The toolkit includes a comprehensive test suite covering unit tests, integration tests, API tests, and CLI tests.

### Run Tests

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests
python run_tests.py

# Run specific test categories
python run_tests.py --unit           # Unit tests only
python run_tests.py --integration    # Integration tests only
python run_tests.py --api            # API tests only
python run_tests.py --cli            # CLI tests only

# Run with coverage
python run_tests.py --coverage

# Run with verbose output
python run_tests.py --verbose
```

**Test Categories:**
- **Unit Tests**: Core functionality and business logic
- **Integration Tests**: Service interactions and data flow
- **API Tests**: Web interface endpoints and responses
- **CLI Tests**: Command-line interface validation

See [TESTING.md](TESTING.md) for detailed testing documentation.

## 🚀 Deployment

### Local Development

```bash
# Development mode with auto-reload
python run_web.py --debug

# Production mode
python run_web.py --host 0.0.0.0 --port 8000
```

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Scale workers
docker-compose up -d --scale worker=3

# View logs
docker-compose logs -f
```

### Cloud Deployment

The toolkit is designed for cloud deployment with:
- **Environment-based configuration**
- **Stateless architecture**
- **Horizontal scaling support**
- **Health check endpoints**

See deployment guides for specific platforms:
- See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for comprehensive deployment guides including AWS, Azure, Google Cloud, and Kubernetes

## 🛠️ Fine-tuning & Evaluation

### Model Fine-tuning

- See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for Azure AI Studio fine-tuning guidance
- Use generated datasets with popular fine-tuning frameworks:
  - HuggingFace Transformers
  - OpenAI Fine-tuning API
  - Azure AI Studio
  - Local training with LoRA/QLoRA

### Comprehensive Evaluation

The toolkit provides multiple evaluation approaches:

**1. Basic Evaluation:**
```bash
python tools/eval.py --question-file YOUR_EVAL_FILE.jsonl --answer-file YOUR_ANSWER_FILE
```

**2. PromptFlow Multi-dimensional Evaluation:**
```bash
# Chat format evaluation
python tools/pfeval_chat.py --input dataset.jsonl --output results.json

# Completion format evaluation  
python tools/pfeval_completion.py --input dataset.jsonl --output results.json

# Local evaluation (no API calls)
python tools/pfeval_local.py --input dataset.jsonl --output results.json --mode local
```

**3. Web Interface Evaluation:**
- Use the Analysis Tools tab in the web interface
- Upload datasets and configure evaluation parameters
- Download comprehensive evaluation reports

**4. Model Comparison:**
```bash
# Generate answers from different models
python tools/answer.py --input questions.jsonl --output gpt4_answers.jsonl --model gpt-4
python tools/answer.py --input questions.jsonl --output gpt35_answers.jsonl --model gpt-3.5-turbo

# Compare results using web interface Model Comparison tool
```

**Evaluation Metrics:**
- **Relevance**: How relevant is the answer to the question?
- **Groundedness**: Is the answer grounded in the provided context?
- **Fluency**: How fluent and natural is the language?
- **Coherence**: How coherent and logical is the response?
- **Similarity**: How similar is the answer to reference answers?

## 🦙 Using Ollama as the OpenAI Model Service

You can use [Ollama](https://ollama.com/) as a local OpenAI-compatible API for running models like Llama 3, Mistral, and others. This allows you to run RAFT without cloud API keys.

**1. Start Ollama with your desired model:**

```bash
ollama run llama3
```

**2. Set the OpenAI-compatible endpoint in your environment:**

```bash
export OPENAI_API_BASE_URL="http://localhost:11434/v1"
export OPENAI_API_KEY="ollama-anything"  # Any non-empty string
```

Or add these to your `.env` file:

```env
OPENAI_API_BASE_URL=http://localhost:11434/v1
OPENAI_API_KEY=ollama-anything
```

**3. Run RAFT as usual:**

```bash
python3 raft.py \
  --datapath sample_data/United_States_PDF.pdf \
  --output ./sample_ds4 \
  --distractors 4 \
  --doctype pdf \
  --chunk_size 512 \
  --questions 5 \
  --openai_key $OPENAI_API_KEY
```

**Note:**

- Ollama's API is compatible with the OpenAI API, but some advanced features may not be supported.
- You can specify different models by running `ollama run <model_name>` and setting the appropriate model in your RAFT command if needed.

## 🏗️ Project Structure

```
raft-toolkit/
├── 📁 core/                      # Core business logic
│   ├── clients/                  # External API clients
│   ├── config.py                 # Configuration management
│   ├── formatters/               # Dataset format converters
│   ├── models.py                 # Data models and schemas
│   ├── raft_engine.py           # Main orchestration engine
│   ├── security.py              # Security utilities
│   └── services/                 # Business services
│       ├── dataset_service.py    # Dataset operations
│       ├── document_service.py   # Document processing
│       └── llm_service.py       # LLM interactions
├── 📁 cli/                       # Command-line interface
│   └── main.py                   # CLI entry point
├── 📁 web/                       # Web interface
│   ├── app.py                    # FastAPI application
│   └── static/                   # Frontend assets
├── 📁 tools/                     # Standalone evaluation tools
│   ├── eval.py                   # Dataset evaluation
│   ├── answer.py                 # Answer generation
│   └── pfeval_*.py              # PromptFlow evaluations
├── 📁 tests/                     # Comprehensive test suite
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   ├── api/                      # API tests
│   └── cli/                      # CLI tests
├── 📁 docs/                      # Documentation
│   ├── WEB_INTERFACE.md          # Web UI guide
│   ├── DEPLOYMENT.md             # Deployment instructions
│   ├── CONFIGURATION.md          # Configuration reference
│   └── TEST_DIRECTORIES.md      # Test configuration guide
├── 📁 .github/                   # CI/CD workflows
│   └── workflows/
│       ├── build.yml             # Build & code quality
│       ├── test.yml              # Comprehensive testing
│       ├── release.yml           # Release automation
│       └── security.yml          # Security scanning
├── 🐳 docker-compose.yml         # Multi-service orchestration
├── 🐳 docker-compose.test.yml    # Testing environment
├── 🐳 Dockerfile                 # Multi-stage container builds
├── 🔧 requirements*.txt          # Python dependencies
├── ⚙️ .env.example              # Environment template
├── ⚙️ .env.test.example         # Test configuration template
├── 🧪 run_tests.py              # Test runner with configurable directories
├── 🌐 run_web.py                # Web server launcher
├── 📋 raft.py                   # Legacy CLI entry point
└── 📖 README.md                 # This documentation
```

## 🚀 Deployment

### 🐳 Docker Deployment

**Production Deployment:**
```bash
# Build production image
docker build --target production -t raft-toolkit:latest .

# Run with environment file
docker run -d \
  --name raft-toolkit \
  --env-file .env \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/outputs:/app/outputs \
  raft-toolkit:latest
```

**Docker Compose (Recommended):**
```bash
# Production stack with Redis and monitoring
docker compose -f docker-compose.yml up -d

# Development with hot reload
docker compose -f docker-compose.dev.yml up -d

# Testing environment
docker compose -f docker-compose.test.yml up
```

### ☁️ Cloud Deployment

**Kubernetes:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: raft-toolkit
spec:
  replicas: 3
  selector:
    matchLabels:
      app: raft-toolkit
  template:
    metadata:
      labels:
        app: raft-toolkit
    spec:
      containers:
      - name: raft-toolkit
        image: ghcr.io/your-org/raft-toolkit:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: raft-secrets
              key: openai-api-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
```

**Helm Chart** (Advanced users):
```bash
# Add repository (when available)
helm repo add raft-toolkit https://charts.raft-toolkit.com
helm repo update

# Install with custom values
helm install raft-toolkit raft-toolkit/raft-toolkit \
  --set openai.apiKey="your-api-key" \
  --set scaling.replicas=3 \
  --set persistence.enabled=true
```

### 🔧 Environment Configuration

**Production `.env`:**
```bash
# Core Configuration
OPENAI_API_KEY=your_production_api_key
RAFT_ENV=production
LOG_LEVEL=INFO

# Web Server
WEB_HOST=0.0.0.0
WEB_PORT=8000
WEB_WORKERS=4

# Database
REDIS_URL=redis://redis:6379

# Security
CORS_ORIGINS=https://your-domain.com
ENABLE_AUTH=true
JWT_SECRET=your_jwt_secret

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090

# Storage
UPLOAD_PATH=/app/uploads
OUTPUT_PATH=/app/outputs
MAX_FILE_SIZE=100MB
```

### 📊 Monitoring & Observability

**Health Checks:**
```bash
# Application health
curl http://localhost:8000/health

# Detailed metrics
curl http://localhost:8000/metrics

# System status
docker compose exec raft-toolkit python -c "
import sys
from core.config import RaftConfig
config = RaftConfig()
print(f'Status: OK')
print(f'Version: {config.version}')
print(f'Environment: {config.env}')
"
```

**Log Aggregation:**
```yaml
# docker-compose.override.yml
version: '3.8'
services:
  raft-toolkit:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        labels: "service=raft-toolkit,environment=production"
```

### 🔒 Security Best Practices

**Container Security:**
```bash
# Run security scan
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  -v $(pwd):/code aquasec/trivy fs /code

# Check for vulnerabilities in image
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image raft-toolkit:latest
```

**Network Security:**
```yaml
# docker-compose.security.yml
version: '3.8'
networks:
  raft-network:
    driver: bridge
    internal: true
  web-network:
    driver: bridge

services:
  raft-toolkit:
    networks:
      - raft-network
      - web-network
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

**Development Setup:**
```bash
# Clone and setup
git clone https://github.com/your-org/raft-toolkit.git
cd raft-toolkit

# Install development dependencies
pip install -r requirements-test.txt

# Run tests
python run_tests.py --coverage

# Run code quality checks
flake8 .
black --check .
isort --check-only .

# Pre-commit hooks (optional)
pre-commit install
```

## 📄 License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).
