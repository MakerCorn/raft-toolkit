# Dependency Troubleshooting Guide

This guide helps resolve common dependency issues in the RAFT Toolkit.

## Quick Diagnosis

Run the dependency checker to identify issues:

```bash
python scripts/check_dependencies.py
```

## Common Issues & Solutions

### 1. FastAPI Version Conflict

**Error:**
```
promptflow-core 1.18.0 requires fastapi<1.0.0,>=0.109.0, but you have fastapi 0.104.1 which is incompatible.
```

**Solution:**
```bash
# Update FastAPI to compatible version
pip install "fastapi>=0.109.0,<1.0.0"

# Or reinstall all web dependencies
pip install -r requirements-web.txt --upgrade
```

### 2. OpenAI Version Conflicts

**Error:**
```
langchain-openai requires openai>=1.68.2, but you have openai 1.30.1
```

**Solution:**
```bash
# Update OpenAI client
pip install "openai>=1.68.2,<2.0.0"

# Or reinstall all dependencies
pip install -r requirements.txt --upgrade
```

### 3. LangChain Experimental Security Issue

**Error:**
```
Safety scan shows CVE-2024-46946 in langchain-experimental
```

**Solution:**
```bash
# Install the specific safe version
pip install "langchain-experimental==0.3.4"
```

**Note:** This vulnerability only affects `LLMSymbolicMathChain`, which RAFT Toolkit doesn't use. We use `SemanticChunker` which is safe.

### 4. Azure AI Evaluation Import Errors

**Error:**
```
ImportError: cannot import name 'evaluate' from 'azure.ai.evaluation'
```

**Solution:**
```bash
# Ensure you have the correct version
pip install "azure-ai-evaluation>=1.8.0,<2.0.0"

# If still failing, try clean install
pip uninstall azure-ai-evaluation promptflow-core
pip install "azure-ai-evaluation>=1.8.0,<2.0.0"
```

### 5. PromptFlow Core Issues

**Error:**
```
ImportError: No module named 'promptflow.eval'
```

**Solution:**
The `promptflow.eval` package has been deprecated. Use Azure AI Evaluation instead:

```bash
# Install the new package
pip install "azure-ai-evaluation>=1.8.0,<2.0.0"
pip install "promptflow-core>=1.18.0,<2.0.0"
```

## Clean Installation Process

If you have persistent conflicts, try a clean installation:

### Option 1: Virtual Environment (Recommended)

```bash
# Create fresh virtual environment
python -m venv raft-toolkit-env
source raft-toolkit-env/bin/activate  # Linux/Mac
# or
raft-toolkit-env\Scripts\activate     # Windows

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-web.txt
pip install -r requirements-test.txt

# Verify installation
python scripts/check_dependencies.py
```

### Option 2: Force Reinstall

```bash
# Uninstall problematic packages
pip uninstall fastapi promptflow-core azure-ai-evaluation langchain-experimental openai -y

# Reinstall with correct versions
pip install -r requirements.txt --force-reinstall
pip install -r requirements-web.txt --force-reinstall

# Check for conflicts
pip check
```

### Option 3: Docker (Isolation)

```bash
# Build with fresh dependencies
docker build --no-cache --target dependencies -t raft-toolkit:deps .

# Run dependency checker in container
docker run --rm raft-toolkit:deps python scripts/check_dependencies.py
```

## Version Constraints Reference

### Current Version Requirements

| Package | Version Constraint | Reason |
|---------|-------------------|---------|
| `fastapi` | `>=0.109.0,<1.0.0` | Required by promptflow-core 1.18.0 |
| `openai` | `>=1.68.2,<2.0.0` | Compatible with langchain-openai |
| `langchain-experimental` | `==0.3.4` | Security fix for CVE-2024-46946 |
| `promptflow-core` | `>=1.18.0,<2.0.0` | Latest stable with Azure AI Evaluation |
| `azure-ai-evaluation` | `>=1.8.0,<2.0.0` | Replacement for promptflow.eval |
| `transformers` | `>=4.44.0,<5.0.0` | Security fixes for multiple CVEs |
| `pypdf` | `>=4.0.0,<5.0.0` | Replacement for deprecated PyPDF2 |

### Development Dependencies

| Package | Version Constraint | Purpose |
|---------|-------------------|---------|
| `uvicorn` | `>=0.25.0,<1.0.0` | ASGI server for web interface |
| `redis` | `>=5.0.1,<6.0.0` | Cache and task queue backend |
| `celery` | `>=5.3.4,<6.0.0` | Distributed task processing |

## Advanced Troubleshooting

### Check Installed Versions

```bash
# Show all installed packages
pip list

# Show specific package versions
pip show fastapi promptflow-core azure-ai-evaluation langchain-experimental

# Check for conflicts
pip check
```

### Environment Debugging

```bash
# Python environment info
python -c "
import sys
print(f'Python: {sys.version}')
print(f'Executable: {sys.executable}')
print(f'Path: {sys.path}')
"

# Package installation locations
python -c "
import fastapi, promptflow_core
print(f'FastAPI: {fastapi.__file__}')
print(f'PromptFlow: {promptflow_core.__file__}')
"
```

### Docker Build Debugging

```bash
# Build with verbose output
docker build --no-cache --progress=plain -t raft-toolkit:debug .

# Run intermediate stage for debugging
docker build --target dependencies -t raft-toolkit:deps .
docker run -it raft-toolkit:deps bash

# Inside container:
pip check
python scripts/check_dependencies.py
```

## Prevention

### 1. Use Version Bounds

Always specify version ranges instead of exact versions:

```txt
# Good
fastapi>=0.109.0,<1.0.0

# Avoid (too restrictive)
fastapi==0.109.0
```

### 2. Regular Dependency Audits

```bash
# Weekly dependency check
python scripts/check_dependencies.py

# Security scan
safety scan -r requirements.txt

# Update check
pip list --outdated
```

### 3. Use Dependency Lock Files

Consider using `pip-tools` for reproducible builds:

```bash
# Install pip-tools
pip install pip-tools

# Generate lock file
pip-compile requirements.in

# Install from lock file
pip-sync requirements.txt
```

## Getting Help

If you're still experiencing issues:

1. **Run the diagnostic script:**
   ```bash
   python scripts/check_dependencies.py > dependency-report.txt
   ```

2. **Check the logs:**
   ```bash
   pip install -r requirements.txt -v > install-log.txt 2>&1
   ```

3. **Report the issue** with:
   - Python version (`python --version`)
   - Operating system
   - Virtual environment details
   - Output from dependency checker
   - Installation logs

4. **Temporary workarounds:**
   - Use Docker for isolated environment
   - Use specific Python version (3.11 recommended)
   - Install in fresh virtual environment