# RAFT Toolkit - CLI Quick Reference Card

## Essential Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `raft --datapath ./docs --output ./dataset` | Basic dataset generation | Creates RAFT dataset from documents |
| `raft --preview --datapath ./docs` | Preview without processing | Validates configuration and shows plan |
| `raft --validate --datapath ./docs` | Validate inputs only | Checks files and configuration |
| `raft-web --port 8000` | Start web interface | Launches web UI on port 8000 |

## Core Parameters Quick Reference

### Input/Output
| Parameter | Default | Description |
|-----------|---------|-------------|
| `--datapath PATH` | Required | Input documents directory |
| `--output PATH` | `./raft_output` | Output dataset directory |
| `--output-format FORMAT` | `hf` | `hf`, `completion`, `chat`, `eval` |
| `--output-type TYPE` | `jsonl` | `jsonl`, `parquet` |
| `--doctype TYPE` | `pdf` | `pdf`, `txt`, `json`, `api`, `pptx` |

### Processing
| Parameter | Default | Description |
|-----------|---------|-------------|
| `--questions INT` | `5` | Questions per document chunk |
| `--distractors INT` | `1` | Distractor documents per question |
| `--chunk_size INT` | `512` | Chunk size in tokens |
| `--chunking-strategy STR` | `semantic` | `semantic`, `fixed`, `sentence` |
| `--p FLOAT` | `1.0` | Oracle document inclusion probability |

### AI Models
| Parameter | Default | Description |
|-----------|---------|-------------|
| `--openai_key STR` | Required | OpenAI API key |
| `--completion_model STR` | `llama3.2` | Model for Q&A generation |
| `--embedding_model STR` | `nomic-embed-text` | Model for embeddings |
| `--system-prompt-key STR` | `gpt` | Prompt template to use |

### Performance
| Parameter | Default | Description |
|-----------|---------|-------------|
| `--workers INT` | `1` | Worker threads for Q&A |
| `--embed-workers INT` | `1` | Worker threads for embedding |
| `--rate-limit-preset STR` | None | `openai_gpt4`, `openai_gpt35_turbo`, etc. |
| `--pace` | `True` | Pace API calls for rate limits |

## Model Recommendations

### Quality vs Cost Matrix
| Use Case | Completion Model | Embedding Model | Cost Level |
|----------|-----------------|-----------------|------------|
| **Premium** | `gpt-4-turbo` | `text-embedding-3-large` | High |
| **Balanced** | `gpt-3.5-turbo` | `text-embedding-3-small` | Medium |
| **Budget** | `llama3.2` | `nomic-embed-text` | Low |

### Performance Presets
| Dataset Size | Workers | Embed Workers | Rate Limit | Expected Time |
|-------------|---------|---------------|-------------|---------------|
| Small (<100 docs) | 2-4 | 1-2 | `openai_gpt35_turbo` | 10-30 min |
| Medium (100-1000) | 4-8 | 2-4 | `openai_gpt4` | 1-3 hours |
| Large (>1000) | 8-16 | 4-8 | `conservative` | 3-8 hours |

## Common Use Cases

### 1. Quick Prototype Dataset
```bash
raft --datapath ./docs --questions 3 --workers 2 --output ./prototype
```

### 2. High-Quality Training Dataset
```bash
raft --datapath ./docs --completion_model gpt-4-turbo \
     --questions 10 --distractors 3 --workers 4 \
     --rate-limit-preset openai_gpt4 --output ./premium
```

### 3. Chat Model Fine-tuning
```bash
raft --datapath ./docs --output-format chat \
     --output-chat-system-prompt "You are a helpful assistant" \
     --questions 8 --output ./chat_dataset
```

### 4. Evaluation Dataset
```bash
raft --datapath ./docs --output-format eval \
     --questions 15 --chunk_size 1024 --output ./eval_set
```

### 5. Batch Processing with Monitoring
```bash
raft --datapath ./docs --workers 8 --langwatch-enabled \
     --rate-limit-preset openai_gpt4 --auto-clean-checkpoints
```

## Output Formats Explained

### HuggingFace Format (`hf`)
```json
{
  "id": "doc1_chunk1_q1",
  "context": "Document content...",
  "question": "What is...?",
  "answer": "The answer is...",
  "oracle_context": "Relevant content..."
}
```

### Completion Format (`completion`)
```json
{
  "prompt": "Context: ...\nQuestion: What is...?",
  "completion": "The answer is..."
}
```

### Chat Format (`chat`)
```json
{
  "messages": [
    {"role": "system", "content": "You are a helpful assistant"},
    {"role": "user", "content": "What is...?"},
    {"role": "assistant", "content": "The answer is..."}
  ]
}
```

### Evaluation Format (`eval`)
```json
{
  "question": "What is...?",
  "answer": "The answer is...",
  "context": "Document content...",
  "metadata": {"source": "doc1.pdf", "chunk_id": 1}
}
```

## Rate Limiting Presets

| Preset | Requests/Min | Tokens/Min | Burst | Best For |
|--------|-------------|------------|-------|----------|
| `openai_gpt4` | 500 | 150,000 | 10 | GPT-4 API |
| `openai_gpt35_turbo` | 3,500 | 900,000 | 50 | GPT-3.5 Turbo |
| `azure_openai_standard` | 240 | 240,000 | 5 | Azure OpenAI |
| `conservative` | 60 | 60,000 | 3 | Avoiding rate limits |
| `aggressive` | 5,000 | 1,000,000 | 100 | Maximum speed |

## Troubleshooting Quick Fixes

| Problem | Solution | Command |
|---------|----------|---------|
| **Rate limit errors** | Use preset + pacing | `--rate-limit-preset openai_gpt4 --pace` |
| **Memory issues** | Reduce workers/batch | `--workers 1 --source-batch-size 10` |
| **Slow processing** | Increase workers | `--workers 8 --embed-workers 4` |
| **API key errors** | Validate first | `--validate --preview` |
| **Quality issues** | Better model + context | `--completion_model gpt-4 --chunk_size 1024` |
| **Large files** | Set size limit | `--source-max-file-size 104857600` |

## Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `OPENAI_API_KEY` | OpenAI authentication | `export OPENAI_API_KEY=sk-...` |
| `RAFT_WORKERS` | Default worker count | `export RAFT_WORKERS=4` |
| `RAFT_OUTPUT` | Default output path | `export RAFT_OUTPUT=./datasets` |
| `LANGWATCH_API_KEY` | Monitoring service | `export LANGWATCH_API_KEY=lw_...` |

## File Type Support

| Extension | Type | Chunking Strategy | Notes |
|-----------|------|------------------|-------|
| `.pdf` | PDF documents | Semantic/Fixed | Best for most documents |
| `.txt` | Plain text | Sentence/Fixed | Simple text processing |
| `.json` | JSON data | Custom | Structured data handling |
| `.pptx` | PowerPoint | Slide-based | Presentation content |
| `.docx` | Word documents | Semantic | Rich text documents |

---

**💡 Pro Tips:**
- Always use `--preview` first to validate your configuration
- Start with small datasets and scale up gradually  
- Use environment variables for API keys and common settings
- Monitor costs with `--langwatch-enabled` for production runs
- Use `--auto-clean-checkpoints` for large batch processing

**🔗 Full Documentation:** See `CLI-Reference.md` for complete parameter details.