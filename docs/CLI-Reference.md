# RAFT Toolkit - Command Line Interface Reference

This document provides comprehensive documentation for all command-line parameters available in the RAFT Toolkit. Parameters are organized by functional groups for easy navigation and reference.

## Table of Contents

1. [Main RAFT CLI](#main-raft-cli)
2. [Input/Output Parameters](#inputoutput-parameters)
3. [Data Source Configuration](#data-source-configuration)
4. [Processing Configuration](#processing-configuration)
5. [AI Model Configuration](#ai-model-configuration)
6. [Performance and Rate Limiting](#performance-and-rate-limiting)
7. [Templates and Prompts](#templates-and-prompts)
8. [Observability and Monitoring](#observability-and-monitoring)
9. [Utility and Debug Options](#utility-and-debug-options)
10. [Tool-Specific Parameters](#tool-specific-parameters)
11. [Environment Variables](#environment-variables)

---

## Main RAFT CLI

The primary entry point for RAFT Toolkit processing: `raft`, `raft-cli`

### Entry Points

| Command | Description | Module |
|---------|-------------|---------|
| `raft` | Main CLI interface | `cli.main:main` |
| `raft-cli` | Alternative CLI interface | `cli.main:main` |
| `raft-web` | Web interface server | `web.app:run_server` |

---

## Input/Output Parameters

Parameters for configuring input sources and output destinations.

| Parameter | Type | Default | Required | Description | Example | Effect on Processing |
|-----------|------|---------|----------|-------------|---------|---------------------|
| `--datapath` | Path | None | Yes | Path to input document or directory | `--datapath ./documents/` | Defines the source data for processing |
| `--output` | str | `./raft_output` | No | Output directory for generated dataset | `--output ./training_data/` | Controls where processed data is saved |
| `--output-format` | str | `hf` | No | Output dataset format | `--output-format completion` | Determines the structure of output data |
| `--output-type` | str | `jsonl` | No | File format for export | `--output-type parquet` | Controls the physical file format |
| `--doctype` | str | `pdf` | No | Input document type | `--doctype txt` | Affects document parsing strategy |

### Output Format Options

| Format | Description | Use Case | Generated Structure |
|--------|-------------|----------|-------------------|
| `hf` | HuggingFace dataset format | Training transformer models | Standard dataset with context, question, answer |
| `completion` | Text completion format | Fine-tuning completion models | Prompt-completion pairs |
| `chat` | Chat/conversation format | Training chat models | System, user, assistant message format |
| `eval` | Evaluation dataset format | Model evaluation | Question-answer pairs with metadata |

### Output Type Options

| Type | Description | Performance | Compatibility |
|------|-------------|-------------|---------------|
| `jsonl` | JSON Lines format | Fast loading, human-readable | Universal compatibility |
| `parquet` | Columnar storage format | Efficient for large datasets | Pandas, Spark, analytical tools |

---

## Data Source Configuration

Parameters for configuring different data source types and access patterns.

| Parameter | Type | Default | Required | Description | Example | Effect on Processing |
|-----------|------|---------|----------|-------------|---------|---------------------|
| `--source-type` | str | `local` | No | Type of input source | `--source-type s3` | Determines data access method |
| `--source-uri` | str | None | No | URI for remote sources | `--source-uri s3://bucket/data/` | Specifies remote data location |
| `--source-credentials` | str | None | No | JSON credentials for source | `--source-credentials '{"key":"value"}'` | Enables authenticated access |
| `--source-include-patterns` | str | None | No | Glob patterns to include | `--source-include-patterns '["*.pdf"]'` | Filters files for processing |
| `--source-exclude-patterns` | str | None | No | Glob patterns to exclude | `--source-exclude-patterns '["temp*"]'` | Excludes unwanted files |
| `--source-max-file-size` | int | 50MB | No | Maximum file size in bytes | `--source-max-file-size 104857600` | Prevents processing oversized files |
| `--source-batch-size` | int | 100 | No | Files processed per batch | `--source-batch-size 50` | Controls memory usage and throughput |

### Source Type Configuration

| Source Type | Description | Required Parameters | Authentication |
|-------------|-------------|-------------------|----------------|
| `local` | Local filesystem | `--datapath` | None |
| `s3` | Amazon S3 storage | `--source-uri`, `--source-credentials` | AWS credentials |
| `sharepoint` | Microsoft SharePoint | `--source-uri`, `--source-credentials` | Azure credentials |

---

## Processing Configuration

Core parameters that control how documents are processed and datasets are generated.

| Parameter | Type | Default | Required | Description | Example | Effect on Processing |
|-----------|------|---------|----------|-------------|---------|---------------------|
| `--questions` | int | 5 | No | Questions per document chunk | `--questions 10` | More questions = larger dataset |
| `--distractors` | int | 1 | No | Distractor documents per question | `--distractors 3` | More distractors = better retrieval training |
| `--p` | float | 1.0 | No | Probability of including oracle document | `--p 0.8` | Controls answer accuracy vs. difficulty |
| `--chunk_size` | int | 512 | No | Chunk size in tokens | `--chunk_size 1024` | Larger chunks = more context per question |
| `--chunking-strategy` | str | `semantic` | No | Document chunking method | `--chunking-strategy fixed` | Affects context quality and coherence |
| `--chunking-params` | str | None | No | Extra chunker parameters (JSON) | `--chunking-params '{"overlap":50}'` | Fine-tunes chunking behavior |

### Chunking Strategy Details

| Strategy | Description | Best For | Parameters |
|----------|-------------|----------|------------|
| `semantic` | Meaning-based chunks | Coherent content, Q&A | `similarity_threshold`, `min_chunk_size` |
| `fixed` | Fixed-size chunks | Consistent processing | `chunk_size`, `overlap` |
| `sentence` | Sentence-boundary chunks | Natural language flow | `sentences_per_chunk`, `min_words` |

### Processing Impact Matrix

| Parameter | Dataset Size | Quality | Processing Time | Memory Usage |
|-----------|-------------|---------|----------------|---------------|
| `questions` ↑ | ↑↑ | ↔ | ↑↑ | ↑ |
| `distractors` ↑ | ↔ | ↑ | ↑ | ↑ |
| `chunk_size` ↑ | ↓ | ↑ | ↔ | ↑ |
| `p` ↓ | ↔ | ↓ | ↔ | ↔ |

---

## AI Model Configuration

Parameters for configuring AI models used in processing.

| Parameter | Type | Default | Required | Description | Example | Effect on Processing |
|-----------|------|---------|----------|-------------|---------|---------------------|
| `--openai_key` | str | None | Yes | OpenAI API key | `--openai_key sk-...` | Enables AI model access |
| `--completion_model` | str | `llama3.2` | No | Q&A generation model | `--completion_model gpt-4` | Affects answer quality and cost |
| `--embedding_model` | str | `nomic-embed-text` | No | Text embedding model | `--embedding_model text-embedding-3-large` | Affects chunking and retrieval quality |
| `--system-prompt-key` | str | `gpt` | No | System prompt template | `--system-prompt-key claude` | Controls model behavior and style |
| `--use-azure-identity` | flag | False | No | Use Azure Default Credentials | `--use-azure-identity` | Enables Azure OpenAI access |

### Model Recommendations

| Use Case | Completion Model | Embedding Model | Quality vs Cost |
|----------|-----------------|-----------------|-----------------|
| **High Quality** | `gpt-4-turbo` | `text-embedding-3-large` | High quality, high cost |
| **Balanced** | `gpt-3.5-turbo` | `text-embedding-3-small` | Good quality, moderate cost |
| **Cost-Effective** | `llama3.2` | `nomic-embed-text` | Reasonable quality, low cost |
| **Local/Private** | `ollama/llama3.2` | `sentence-transformers/all-MiniLM-L6-v2` | Variable quality, no API cost |

---

## Performance and Rate Limiting

Parameters for optimizing performance and managing API rate limits.

| Parameter | Type | Default | Required | Description | Example | Effect on Processing |
|-----------|------|---------|----------|-------------|---------|---------------------|
| `--workers` | int | 1 | No | Worker threads for Q&A generation | `--workers 4` | Increases parallel processing |
| `--embed-workers` | int | 1 | No | Worker threads for embedding | `--embed-workers 2` | Parallelizes document chunking |
| `--pace` | flag | True | No | Pace LLM calls for rate limits | `--pace` | Prevents rate limit errors |
| `--auto-clean-checkpoints` | flag | False | No | Clean checkpoints after completion | `--auto-clean-checkpoints` | Saves disk space |

### Rate Limiting Configuration

| Parameter | Type | Default | Description | Example |
|-----------|------|---------|-------------|---------|
| `--rate-limit` | flag | False | Enable rate limiting | `--rate-limit` |
| `--rate-limit-strategy` | str | `sliding_window` | Rate limiting algorithm | `--rate-limit-strategy token_bucket` |
| `--rate-limit-preset` | str | None | Predefined rate limit config | `--rate-limit-preset openai_gpt4` |
| `--rate-limit-requests-per-minute` | int | None | Custom requests per minute | `--rate-limit-requests-per-minute 60` |
| `--rate-limit-tokens-per-minute` | int | None | Custom tokens per minute | `--rate-limit-tokens-per-minute 150000` |
| `--rate-limit-max-burst` | int | None | Maximum burst requests | `--rate-limit-max-burst 10` |
| `--rate-limit-max-retries` | int | 3 | Retry attempts on rate limit | `--rate-limit-max-retries 5` |

### Rate Limit Presets

| Preset | RPM | TPM | Burst | Use Case |
|--------|-----|-----|-------|---------|
| `openai_gpt4` | 500 | 150,000 | 10 | OpenAI GPT-4 API |
| `openai_gpt35_turbo` | 3,500 | 900,000 | 50 | OpenAI GPT-3.5 Turbo |
| `azure_openai_standard` | 240 | 240,000 | 5 | Azure OpenAI Standard |
| `anthropic_claude` | 1,000 | 200,000 | 15 | Anthropic Claude API |
| `conservative` | 60 | 60,000 | 3 | Very safe limits |
| `aggressive` | 5,000 | 1,000,000 | 100 | Maximum throughput |

### Performance Tuning Guidelines

| Scenario | Workers | Embed Workers | Rate Limiting | Expected Speedup |
|----------|---------|---------------|---------------|------------------|
| **Small Dataset (<100 docs)** | 2-4 | 1-2 | Preset | 2-3x |
| **Medium Dataset (100-1000 docs)** | 4-8 | 2-4 | Custom limits | 3-5x |
| **Large Dataset (>1000 docs)** | 8-16 | 4-8 | Conservative + retry | 5-10x |
| **API Rate Limited** | 1-2 | 1 | Aggressive pacing | Stable processing |

---

## Templates and Prompts

Parameters for customizing prompt templates and generation behavior.

| Parameter | Type | Default | Description | Example | Effect on Processing |
|-----------|------|---------|-------------|---------|---------------------|
| `--templates` | str | `./templates/` | Template directory path | `--templates ./custom_prompts/` | Changes prompt source location |
| `--embedding-prompt-template` | str | None | Custom embedding prompt file | `--embedding-prompt-template embed.txt` | Customizes chunking behavior |
| `--qa-prompt-template` | str | None | Custom Q&A generation template | `--qa-prompt-template qa_gen.txt` | Controls question generation style |
| `--answer-prompt-template` | str | None | Custom answer generation template | `--answer-prompt-template answer.txt` | Controls answer generation style |

### Chat Output Configuration

| Parameter | Type | Default | Description | Example |
|-----------|------|---------|-------------|---------|
| `--output-chat-system-prompt` | str | None | System prompt for chat format | `--output-chat-system-prompt "You are a helpful assistant"` |

### Completion Output Configuration

| Parameter | Type | Default | Description | Example |
|-----------|------|---------|-------------|---------|
| `--output-completion-prompt-column` | str | `prompt` | Prompt column name | `--output-completion-prompt-column instruction` |
| `--output-completion-completion-column` | str | `completion` | Completion column name | `--output-completion-completion-column response` |

---

## Observability and Monitoring

Parameters for enabling observability, tracing, and monitoring capabilities.

| Parameter | Type | Default | Required | Description | Example | Effect on Processing |
|-----------|------|---------|----------|-------------|---------|---------------------|
| `--langwatch-enabled` | flag | False | No | Enable LangWatch observability | `--langwatch-enabled` | Adds tracing and monitoring |
| `--langwatch-api-key` | str | None | No | LangWatch API key | `--langwatch-api-key lw_...` | Enables data upload to LangWatch |
| `--langwatch-endpoint` | str | None | No | Custom LangWatch endpoint | `--langwatch-endpoint https://custom.com` | Uses custom monitoring service |
| `--langwatch-project` | str | None | No | LangWatch project name | `--langwatch-project raft-dev` | Organizes traces by project |
| `--langwatch-debug` | flag | False | No | Enable LangWatch debug logging | `--langwatch-debug` | Shows detailed tracing info |

### Observability Benefits

| Feature | Description | Use Case | Performance Impact |
|---------|-------------|----------|-------------------|
| **Request Tracing** | Track all API calls | Debugging, optimization | Minimal (< 1%) |
| **Performance Metrics** | Latency and throughput data | Monitoring, alerting | Minimal (< 1%) |
| **Error Tracking** | Capture and categorize failures | Reliability improvement | None |
| **Cost Monitoring** | Track API usage and costs | Budget management | None |

---

## Utility and Debug Options

Parameters for validation, debugging, and utility operations.

| Parameter | Type | Default | Description | Example | Effect on Processing |
|-----------|------|---------|-------------|---------|---------------------|
| `--preview` | flag | False | Show processing preview without running | `--preview` | Validates config without processing |
| `--validate` | flag | False | Validate configuration and inputs only | `--validate` | Checks inputs and exits |
| `--env-file` | str | None | Path to .env file for configuration | `--env-file .env.prod` | Loads environment variables |

### Debug and Validation Workflow

```bash
# 1. Validate configuration
raft --datapath ./docs --validate

# 2. Preview processing plan  
raft --datapath ./docs --preview

# 3. Run with monitoring
raft --datapath ./docs --langwatch-enabled --langwatch-debug
```

---

## Tool-Specific Parameters

### Answer Generation Tool (`tools/answer.py`)

| Parameter | Type | Default | Description | Example |
|-----------|------|---------|-------------|---------|
| `--input` | str | `input.jsonl` | Input JSONL file | `--input questions.jsonl` |
| `--output` | str | `output.jsonl` | Output JSONL file | `--output answers.jsonl` |
| `--workers` | int | 1 | Number of worker threads | `--workers 4` |
| `--model` | str | `gpt-4` | Model for answer generation | `--model gpt-3.5-turbo` |
| `--deployment` | str | `gpt-4` | Azure deployment name | `--deployment my-gpt4` |
| `--count` | int | -1 | Number of questions to answer (-1 = all) | `--count 100` |

### Evaluation Tool (`tools/eval.py`)

| Parameter | Type | Default | Description | Example |
|-----------|------|---------|-------------|---------|
| `--question-file` | str | Required | Input file with questions | `--question-file eval.jsonl` |
| `--answer-file` | str | `answer.jsonl` | Output file for answers | `--answer-file results.jsonl` |
| `--model` | str | `gpt-4` | Model to evaluate | `--model claude-3` |
| `--input-prompt-key` | str | `instruction` | Input column name | `--input-prompt-key question` |
| `--output-answer-key` | str | `answer` | Output column name | `--output-answer-key response` |

### Dataset Converter Tool (`core/formatters/dataset_converter.py`)

| Parameter | Type | Default | Description | Example |
|-----------|------|---------|-------------|---------|
| `--input` | str | Required | Input dataset file | `--input dataset.arrow` |
| `--input-type` | str | `arrow` | Input format (arrow/jsonl) | `--input-type jsonl` |
| `--output` | str | Required | Output file path | `--output converted.jsonl` |
| `--output-format` | str | Required | Output format | `--output-format completion` |
| `--output-type` | str | `jsonl` | Output file type | `--output-type parquet` |

### Test Runner (`run_tests.py`)

| Parameter | Type | Default | Description | Example |
|-----------|------|---------|-------------|---------|
| `--unit` | flag | False | Run unit tests only | `--unit` |
| `--integration` | flag | False | Run integration tests only | `--integration` |
| `--coverage` | flag | False | Generate coverage report | `--coverage` |
| `--fast` | flag | False | Skip slow tests | `--fast` |
| `--parallel` | int | None | Run tests in parallel | `--parallel 4` |
| `--output-dir` | str | None | Output directory for results | `--output-dir ./test_results` |

---

## Environment Variables

Many CLI parameters can be configured via environment variables with the `RAFT_` prefix.

### Core Environment Variables

| Environment Variable | CLI Parameter | Description | Example |
|---------------------|---------------|-------------|---------|
| `OPENAI_API_KEY` | `--openai_key` | OpenAI API key | `export OPENAI_API_KEY=sk-...` |
| `LANGWATCH_API_KEY` | `--langwatch-api-key` | LangWatch API key | `export LANGWATCH_API_KEY=lw_...` |
| `RAFT_DATAPATH` | `--datapath` | Default input path | `export RAFT_DATAPATH=./data` |
| `RAFT_OUTPUT` | `--output` | Default output path | `export RAFT_OUTPUT=./output` |
| `RAFT_WORKERS` | `--workers` | Default worker count | `export RAFT_WORKERS=4` |
| `RAFT_LOG_LEVEL` | N/A | Logging level | `export RAFT_LOG_LEVEL=DEBUG` |

### Configuration File Support

```bash
# Load configuration from .env file
raft --env-file .env.production --datapath ./docs
```

Example `.env` file:
```bash
OPENAI_API_KEY=sk-your-key-here
RAFT_WORKERS=4
RAFT_OUTPUT=./production_output
LANGWATCH_ENABLED=true
LANGWATCH_PROJECT=raft-production
```

---

## Usage Examples

### Basic Dataset Generation

```bash
# Simple PDF processing
raft --datapath ./documents/ --output ./training_data --questions 5

# With custom models and workers
raft --datapath ./docs --completion_model gpt-4 --workers 4 --questions 10
```

### Advanced Configuration

```bash
# High-quality dataset with monitoring
raft \
  --datapath ./documents \
  --output ./premium_dataset \
  --completion_model gpt-4-turbo \
  --embedding_model text-embedding-3-large \
  --questions 15 \
  --distractors 3 \
  --workers 8 \
  --rate-limit-preset openai_gpt4 \
  --langwatch-enabled \
  --langwatch-project raft-production
```

### Different Output Formats

```bash
# Chat format for conversation training
raft --datapath ./docs --output-format chat --output-chat-system-prompt "You are an expert assistant"

# Completion format for fine-tuning
raft --datapath ./docs --output-format completion --output-type parquet

# Evaluation format for benchmarking
raft --datapath ./docs --output-format eval --questions 20
```

### Cloud and Remote Sources

```bash
# S3 data source
raft \
  --source-type s3 \
  --source-uri s3://my-bucket/documents/ \
  --source-credentials '{"aws_access_key_id":"key","aws_secret_access_key":"secret"}' \
  --output ./s3_dataset

# SharePoint source
raft \
  --source-type sharepoint \
  --source-uri https://company.sharepoint.com/sites/docs \
  --source-credentials '{"client_id":"id","client_secret":"secret","tenant_id":"tenant"}' \
  --output ./sharepoint_dataset
```

---

## Performance Optimization Guide

### Small Datasets (< 100 documents)
```bash
raft --datapath ./docs --workers 2 --embed-workers 1 --questions 5
```

### Medium Datasets (100-1000 documents)
```bash
raft --datapath ./docs --workers 4 --embed-workers 2 --rate-limit-preset openai_gpt35_turbo --questions 8
```

### Large Datasets (> 1000 documents)
```bash
raft --datapath ./docs --workers 8 --embed-workers 4 --rate-limit-preset conservative --auto-clean-checkpoints --questions 10
```

### Memory-Constrained Environments
```bash
raft --datapath ./docs --workers 1 --source-batch-size 25 --chunk_size 256 --questions 3
```

---

## Troubleshooting Common Issues

### Rate Limiting Errors
```bash
# Solution: Use rate limiting presets
raft --datapath ./docs --rate-limit-preset openai_gpt4 --pace
```

### Memory Issues
```bash
# Solution: Reduce batch size and workers
raft --datapath ./docs --workers 1 --source-batch-size 10 --chunk_size 256
```

### API Key Issues
```bash
# Solution: Validate configuration first
raft --datapath ./docs --validate --preview
```

### Quality Issues
```bash
# Solution: Increase model quality and context
raft --datapath ./docs --completion_model gpt-4 --chunk_size 1024 --distractors 3
```

---

*This document is auto-generated and maintained. For the latest parameter information, run `raft --help` or check the source code.*