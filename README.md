# RAFT Toolkit

> **Retrieval Augmentation Fine-Tuning Toolkit**  

## 🚀 Overview

### What is RAFT?

**RAFT (Retrieval Augmentation Fine-Tuning)** is a technique that trains language models to better utilize retrieved documents when answering questions. Unlike traditional RAG systems that rely on frozen pre-trained models, RAFT fine-tunes models specifically for document-based reasoning tasks.

The RAFT Toolkit automates the creation of training datasets by generating `{question, answer, documents}` triplets from your documents, enabling you to fine-tune models that excel at retrieval-augmented generation tasks.

#### RAFT Training Process Flow

```mermaid
graph TD
    A[📄 Input Documents<br/>PDF, TXT, JSON, PPTX] --> B{🔧 RAFT Toolkit<br/>CLI or Web UI}
    
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
- 🎯 **Flexible Output**: HuggingFace, OpenAI completion/chat, and evaluation formats
- ⚡ **Parallel Processing**: Configurable workers for optimal performance
- 🧪 **Comprehensive Testing**: Unit, integration, API, and CLI test suites
- 🐳 **Container Ready**: Docker support for easy deployment

## 📦 Installation

### Prerequisites

- Python 3.8+ 
- OpenAI API key (or Azure OpenAI credentials)
- Optional: Docker for containerized deployment

### Basic Installation

```bash
# Clone the repository
git clone <repository-url>
cd raft-toolkit

# Install core dependencies
pip install -r requirements.txt

# For web interface (optional)
pip install -r requirements-web.txt

# For evaluation tools (optional)
pip install -r tools/requirements.txt

# For testing (optional)
pip install -r requirements-test.txt
```

### Docker Installation

```bash
# Clone and set up environment
cp .env.example .env
# Edit .env with your configuration

# Run with Docker Compose
docker-compose up -d

# Access web interface at http://localhost:8000
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
```

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

```bash
# Set up environment variables
export OPENAI_API_KEY="your_api_key_here"

# Run CLI tool
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
- [AWS Deployment](docs/deployment/aws.md)
- [Azure Deployment](docs/deployment/azure.md)
- [Google Cloud Deployment](docs/deployment/gcp.md)
- [Kubernetes Deployment](docs/deployment/kubernetes.md)

## 🛠️ Fine-tuning & Evaluation

### Model Fine-tuning

- See [azure-ai-studio-ft/howto.md](azure-ai-studio-ft/howto.md) for Azure fine-tuning
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

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](https://opensource.org/licenses/MIT) file or the OSI page for full terms.
