# 🌐 RAFT Toolkit Web Interface Guide

> **Complete guide to using the RAFT Toolkit's modern web interface for dataset generation and analysis**

The RAFT Toolkit includes a powerful web interface that provides an intuitive, visual way to generate datasets and perform comprehensive evaluations. This guide covers all features and workflows available through the web UI.

---

## 📋 Table of Contents

- [🚀 Getting Started](#-getting-started)
- [🎯 Core Features](#-core-features)
- [📤 Dataset Generation](#-dataset-generation)
- [🛠️ Analysis Tools](#️-analysis-tools)
- [📊 Job Management](#-job-management)
- [⚙️ Configuration](#️-configuration)
- [🔧 Troubleshooting](#-troubleshooting)
- [📚 Examples](#-examples)

---

## 🚀 Getting Started

### Prerequisites

- RAFT Toolkit installed with web dependencies
- OpenAI API key or Azure OpenAI credentials
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Starting the Web Interface

```bash
# From the project root directory
python run_web.py

# Or with custom configuration
python run_web.py --host 0.0.0.0 --port 8080 --debug

# Access at: http://localhost:8000
```

### First Launch Setup

1. **Environment Variables**: Ensure your `.env` file is configured
2. **API Keys**: Verify OpenAI/Azure credentials are set
3. **Browser Access**: Navigate to `http://localhost:8000`
4. **Test Upload**: Try uploading a small document to verify setup

---

## 🎯 Core Features

The web interface consists of three main tabs:

### 📤 Dataset Generation
- **Visual file upload** with drag-and-drop support
- **Interactive configuration** for all RAFT parameters
- **Live preview** of processing estimates
- **Real-time job tracking** with progress updates

### 🛠️ Analysis Tools
- **Six comprehensive evaluation tools** for generated datasets
- **Multi-model comparison** capabilities
- **Batch processing** workflows
- **Visual results display** with download options

### 📊 Job Management
- **Active job monitoring** with real-time updates
- **Job history** and status tracking
- **Result downloads** for completed jobs
- **Resource usage** statistics

---

## 📤 Dataset Generation

### File Upload

The web interface supports multiple file formats with easy upload:

**Supported Formats:**
- **PDF Documents** (.pdf) - Research papers, manuals, reports
- **Text Files** (.txt) - Plain text documents
- **JSON Data** (.json) - Structured data files
- **PowerPoint** (.pptx) - Presentation slides
- **API Documentation** - REST API specifications

**Upload Methods:**
1. **Drag & Drop**: Drag files directly onto the upload area
2. **Click to Browse**: Click the upload area to select files
3. **File Validation**: Automatic format detection and validation

### Configuration Options

#### Core Settings

**Document Type**
- Automatically detected from file extension
- Manual override available for specific processing needs
- Custom handling for each document type

**Questions per Chunk**
- Range: 1-20 questions per text chunk
- Default: 5 questions
- Higher values = more comprehensive datasets

**Chunk Size**
- Range: 100-2048 tokens per chunk
- Default: 512 tokens
- Affects granularity of question generation

#### Processing Settings

**Distractor Documents**
- Range: 0-10 distractors per question
- Purpose: Add challenging context for fine-tuning
- More distractors = harder evaluation

**Oracle Probability**
- Range: 0-1 (0% to 100%)
- Probability of including the source chunk in context
- Higher values = easier questions

**Chunking Strategy**
- **Semantic**: Context-aware chunking (recommended)
- **Fixed**: Equal token-sized chunks
- **Sentence**: Sentence boundary-based chunks

#### Output Settings

**Output Format**
- **HuggingFace**: Standard format for HF datasets
- **OpenAI Completion**: For completion-based fine-tuning
- **OpenAI Chat**: For chat-based fine-tuning
- **Evaluation**: Optimized for evaluation workflows

**Output Type**
- **JSONL**: JSON Lines format (recommended)
- **Parquet**: Columnar format for large datasets

**Worker Threads**
- Range: 1-8 concurrent workers
- More workers = faster processing (API limits apply)

### Advanced Configuration

Click "Advanced Configuration" to access:

**Model Settings**
- **Completion Model**: Model for question/answer generation
- **Embedding Model**: Model for semantic chunking
- **Custom Endpoints**: Support for custom OpenAI-compatible APIs

**Chat-Specific Options**
- **System Prompt**: Custom system prompt for chat format
- **Message Structure**: Define conversation flow

### Live Preview

Before processing, use the "Preview Processing" button to see:
- **Estimated Chunks**: Number of text chunks to be created
- **Estimated QA Points**: Total question-answer pairs
- **Processing Time**: Approximate completion time
- **Token Usage**: Estimated API token consumption

---

## 🛠️ Analysis Tools

The Analysis Tools tab provides six powerful evaluation utilities:

### 1. 📈 Dataset Evaluation

**Purpose**: Evaluate model performance on generated datasets

**Configuration:**
- **Question File**: JSONL file with evaluation questions
- **Model**: Choose evaluation model (GPT-4, GPT-3.5, etc.)
- **Workers**: Parallel processing threads
- **Input Key**: Column name for input text

**Output**: Comprehensive evaluation metrics and performance statistics

### 2. 💬 Answer Generation

**Purpose**: Generate high-quality answers for evaluation datasets

**Configuration:**
- **Input File**: JSONL file with questions
- **Model**: Answer generation model
- **Workers**: Parallel processing threads
- **Output Name**: Custom filename for results

**Output**: Complete dataset with generated answers

### 3. 🔍 PromptFlow Analysis

**Purpose**: Multi-dimensional evaluation using Microsoft PromptFlow

**Configuration:**
- **Dataset File**: JSONL with questions and answers
- **Evaluation Type**: Chat, Completion, or Local
- **Mode**: Local or Remote processing
- **Metrics**: Select evaluation dimensions:
  - **Relevance**: Answer relevance to question
  - **Groundedness**: Factual grounding in context
  - **Fluency**: Language naturalness
  - **Coherence**: Logical consistency

**Output**: Detailed multi-dimensional evaluation scores

### 4. 📊 Dataset Analysis

**Purpose**: Statistical analysis and quality metrics

**Configuration:**
- **Dataset File**: JSONL file to analyze
- **Analysis Types**:
  - **Basic Statistics**: Length, token counts, distributions
  - **Quality Metrics**: Content quality assessments
  - **Length Distribution**: Text length analysis
  - **Sample Examples**: Representative data samples
- **Report Format**: JSON, HTML, or CSV output

**Output**: Comprehensive dataset quality report

### 5. ⚖️ Model Comparison

**Purpose**: Side-by-side performance comparison

**Configuration:**
- **Model A Results**: First model's outputs
- **Model B Results**: Second model's outputs
- **Model Names**: Custom labels for comparison
- **Metrics**: Comparison dimensions:
  - **Response Length**: Text length comparison
  - **Response Speed**: Generation speed analysis
  - **Token Usage**: Efficiency comparison

**Output**: Detailed comparison report with visualizations

### 6. 📦 Batch Processing

**Purpose**: Process multiple datasets with automated workflows

**Configuration:**
- **Multiple Files**: Upload multiple JSONL files
- **Operation Type**: 
  - **Evaluate All**: Run evaluation on all files
  - **Analyze All**: Perform analysis on all files
  - **Generate Answers**: Generate answers for all
  - **Convert Format**: Batch format conversion
- **Parallel Jobs**: Number of simultaneous processes

**Output**: Consolidated results from all processed files

### Using Analysis Tools

**General Workflow:**
1. **Select Tool**: Click on the desired tool card
2. **Upload Files**: Add required input files
3. **Configure Settings**: Adjust parameters as needed
4. **Start Processing**: Click the tool-specific action button
5. **Monitor Progress**: Watch real-time progress indicators
6. **Download Results**: Get comprehensive result files

**File Requirements:**
- All tools accept JSONL format files
- Files should contain properly formatted JSON objects
- Required fields vary by tool (see tool-specific documentation)

---

## 📊 Job Management

The Jobs tab provides comprehensive monitoring and management:

### Job Status Tracking

**Status Types:**
- **Pending**: Job queued for processing
- **Processing**: Currently running with progress bar
- **Completed**: Finished successfully with download option
- **Failed**: Error occurred with details

**Real-time Updates:**
- Progress percentages for active jobs
- Processing time estimates
- Resource usage statistics
- Detailed error messages

### Job Information

Each job displays:
- **Job ID**: Unique identifier (first 8 characters shown)
- **Job Type**: Dataset generation or analysis tool
- **Status**: Current processing state
- **Progress**: Completion percentage for active jobs
- **Statistics**: 
  - QA points generated
  - Processing time
  - Token usage
  - Throughput metrics

### Job Actions

**Download Results**: 
- Available for completed jobs
- Automatic file naming based on job type
- Multiple format support

**Delete Jobs**:
- Remove completed or failed jobs
- Confirmation dialog prevents accidental deletion
- Bulk operations for multiple jobs

**Refresh Status**:
- Manual refresh button
- Automatic updates every 5 seconds
- Real-time progress tracking

---

## ⚙️ Configuration

### Environment Variables

The web interface respects these environment variables:

```bash
# Web Server Configuration
WEB_HOST=0.0.0.0                    # Server host
WEB_PORT=8000                       # Server port
WEB_DEBUG=false                     # Debug mode
WEB_WORKERS=4                       # Uvicorn workers

# File Upload Configuration
MAX_UPLOAD_SIZE=52428800            # 50MB upload limit
ALLOWED_EXTENSIONS=pdf,txt,json,pptx # Supported formats
UPLOAD_TIMEOUT=300                  # Upload timeout (seconds)

# Processing Configuration
DEFAULT_WORKERS=4                   # Default worker threads
MAX_WORKERS=16                      # Maximum concurrent workers
JOB_TIMEOUT=3600                    # Job timeout (1 hour)
CLEANUP_INTERVAL=3600               # Cleanup old jobs (1 hour)

# Security Configuration
CORS_ORIGINS=["http://localhost:3000"] # CORS origins
API_KEY_REQUIRED=false              # Require API key for access
```

### Browser Settings

**Recommended Settings:**
- **JavaScript**: Must be enabled
- **Cookies**: Allow for session management
- **Local Storage**: Used for user preferences
- **File Upload**: Large file support enabled

**Browser Compatibility:**
- Chrome 80+ ✅
- Firefox 75+ ✅
- Safari 13+ ✅
- Edge 80+ ✅

---

## 🔧 Troubleshooting

### Common Issues

#### Upload Problems

**File Too Large**
```
Error: File size exceeds maximum limit
Solution: Reduce file size or increase MAX_UPLOAD_SIZE
```

**Unsupported Format**
```
Error: File format not supported
Solution: Convert to PDF, TXT, JSON, or PPTX
```

**Upload Timeout**
```
Error: Upload timed out
Solution: Check network connection and file size
```

#### Processing Errors

**API Key Issues**
```
Error: Invalid API key
Solution: Check OPENAI_API_KEY in environment variables
```

**Rate Limiting**
```
Error: Rate limit exceeded
Solution: Reduce worker count or add delays
```

**Memory Issues**
```
Error: Out of memory
Solution: Reduce chunk size or worker count
```

#### Job Management

**Jobs Not Updating**
```
Issue: Progress not showing
Solution: Check browser console for errors, refresh page
```

**Download Failures**
```
Issue: Download not starting
Solution: Check popup blockers, try different browser
```

### Debug Mode

Enable debug mode for detailed logging:

```bash
python run_web.py --debug

# Or set environment variable
export WEB_DEBUG=true
python run_web.py
```

Debug mode provides:
- Detailed error messages
- Request/response logging
- Performance metrics
- Stack traces for errors

### Browser Developer Tools

Use browser dev tools for troubleshooting:

1. **Console Tab**: JavaScript errors and logs
2. **Network Tab**: API request/response details
3. **Application Tab**: Local storage and session data
4. **Performance Tab**: Loading and execution timing

---

## 📚 Examples

### Example 1: Research Paper Analysis

**Scenario**: Analyze a research paper and create an evaluation dataset

1. **Upload Document**:
   - Upload `research_paper.pdf`
   - Document type: PDF
   - File size: 2.3 MB

2. **Configure Processing**:
   - Questions per chunk: 3
   - Chunk size: 512 tokens
   - Distractors: 2
   - Chunking strategy: Semantic
   - Output format: HuggingFace

3. **Preview Results**:
   - Estimated chunks: 45
   - Estimated QA points: 135
   - Processing time: ~8 minutes

4. **Start Processing**:
   - Monitor progress in Jobs tab
   - Download results when complete

5. **Evaluate Results**:
   - Switch to Analysis Tools
   - Use Dataset Analysis tool
   - Generate quality report

### Example 2: Multi-Model Comparison

**Scenario**: Compare GPT-4 vs GPT-3.5 performance

1. **Generate Answers with GPT-4**:
   - Upload question dataset
   - Use Answer Generation tool
   - Model: GPT-4
   - Workers: 4

2. **Generate Answers with GPT-3.5**:
   - Same question dataset
   - Model: GPT-3.5-turbo
   - Workers: 8 (faster processing)

3. **Compare Results**:
   - Use Model Comparison tool
   - Upload both result files
   - Configure comparison metrics
   - Generate comparison report

4. **Analysis**:
   - Review length differences
   - Compare response quality
   - Analyze token efficiency

### Example 3: Batch Evaluation Workflow

**Scenario**: Evaluate multiple datasets simultaneously

1. **Prepare Datasets**:
   - Multiple JSONL files with questions/answers
   - Consistent format across all files
   - Various domains/topics

2. **Batch Processing**:
   - Upload all files to Batch Processing tool
   - Operation: Evaluate All
   - Parallel jobs: 3

3. **Monitor Progress**:
   - Track all jobs in Jobs tab
   - Download individual results
   - Generate consolidated report

4. **Comprehensive Analysis**:
   - Use PromptFlow Analysis for detailed metrics
   - Compare performance across domains
   - Generate executive summary

---

## 🚀 Advanced Usage

### Custom API Integration

The web interface supports custom OpenAI-compatible APIs:

```bash
# Set custom endpoint
export OPENAI_API_BASE_URL="https://your-custom-api.com/v1"
export OPENAI_API_KEY="your-custom-key"

# Start web interface
python run_web.py
```

### Automation and Integration

**API Access**: The web interface exposes REST APIs for automation:
- `GET /api/jobs` - List all jobs
- `POST /api/process` - Start processing job
- `GET /api/jobs/{id}/status` - Get job status
- `GET /api/jobs/{id}/download` - Download results

**Example Automation**:
```python
import requests

# Start processing job
response = requests.post('http://localhost:8000/api/process', 
                        files={'file': open('document.pdf', 'rb')},
                        data={'config': json.dumps(config)})

job_id = response.json()['job_id']

# Monitor progress
while True:
    status = requests.get(f'http://localhost:8000/api/jobs/{job_id}/status')
    if status.json()['status'] == 'completed':
        break
    time.sleep(30)

# Download results
results = requests.get(f'http://localhost:8000/api/jobs/{job_id}/download')
```

### Performance Optimization

**Client-Side Optimization**:
- Enable browser caching
- Use compression (gzip)
- Optimize file sizes before upload
- Use modern browsers for best performance

**Server-Side Optimization**:
- Increase worker processes for high load
- Use Redis for job queue (production)
- Enable HTTP/2 for faster connections
- Configure CDN for static assets

---

## 📞 Support

For web interface specific issues:

1. **Check Console**: Browser developer console for JavaScript errors
2. **Server Logs**: Web server logs for backend issues
3. **Network Tab**: Browser network tab for API issues
4. **Documentation**: This guide and main README
5. **Community**: GitHub discussions for questions

**Common Resources**:
- [Main Documentation](../README.md)
- [API Documentation](http://localhost:8000/docs) (when server running)
- [Tools Documentation](../tools/README.md)
- [Testing Guide](TESTING.md)