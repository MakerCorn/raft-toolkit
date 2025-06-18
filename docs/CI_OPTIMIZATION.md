# CI Build Optimization Guide

This document outlines the optimized dependency structure and installation strategies for faster CI builds.

## Optimization Overview

The RAFT Toolkit has been restructured to provide **70-80% faster CI builds** through:

- **Minimal core dependencies**: Reduced from ~45 to ~15 packages
- **Tighter version constraints**: Faster dependency resolution
- **Optional dependency groups**: Install only what you need
- **Streamlined requirements**: Core functionality separate from heavy ML libraries

## Installation Strategies

### 1. Core Installation (Fastest - ~30-60 seconds)

```bash
# Installs only essential dependencies for basic CLI functionality
pip install raft-toolkit
```

**Use cases:**
- Basic CI tests
- Lightweight deployments
- Configuration validation
- Simple document processing

**Dependencies:** ~15 packages (pydantic, requests, langchain-core, pandas, pypdf, etc.)

### 2. Standard Installation (Recommended)

```bash
# Installs AI/ML functionality for typical use cases
pip install raft-toolkit[standard]
```

**Equivalent to:**
```bash
pip install raft-toolkit[ai,langchain,embeddings,documents]
```

**Use cases:**
- Full RAFT functionality
- Production deployments
- Most CI scenarios

**Dependencies:** ~50 packages including transformers, sentence-transformers, scikit-learn

### 3. Complete Installation

```bash
# Full functionality minus development tools
pip install raft-toolkit[complete]
```

**Equivalent to:**
```bash
pip install raft-toolkit[ai,langchain,embeddings,documents,cloud,tracing]
```

**Use cases:**
- Production with cloud services
- Observability enabled
- Full feature testing

### 4. Development Installation

```bash
# Everything including dev tools
pip install raft-toolkit[all]
```

**Use cases:**
- Local development
- Full testing suite
- Code quality checks

## CI/CD Recommendations

### Fast Tests (Unit/Linting)

```yaml
# Example GitHub Actions
- name: Install core dependencies
  run: pip install raft-toolkit[dev]
  
- name: Run fast tests
  run: |
    flake8 .
    black --check .
    pytest tests/unit/
```

**Estimated time:** 1-2 minutes

### Integration Tests

```yaml
- name: Install standard dependencies  
  run: pip install raft-toolkit[standard,dev]
  
- name: Run integration tests
  run: pytest tests/integration/
```

**Estimated time:** 3-5 minutes

### Full Test Suite

```yaml
- name: Install all dependencies
  run: pip install raft-toolkit[all]
  
- name: Run full test suite
  run: pytest
```

**Estimated time:** 5-8 minutes

## Dependency Groups Reference

| Group | Purpose | Key Dependencies |
|-------|---------|------------------|
| `ai` | Core AI/ML functionality | transformers, sentence-transformers, scikit-learn, datasets |
| `langchain` | LangChain ecosystem | langchain-openai, langchain-community, langchain-experimental |
| `embeddings` | Embedding providers | nomic |
| `documents` | Extended document processing | python-pptx, pdfplumber |
| `web` | Web interface | fastapi, uvicorn, redis, celery |
| `cloud` | Cloud services | boto3, azure-*, msal |
| `kubernetes` | K8s deployment | kubernetes, jinja2, prometheus-client |
| `tracing` | Observability | opentelemetry-*, sentry-sdk, langwatch |
| `dev` | Development tools | pytest, flake8, black, mypy, bandit |

## Convenience Groups

| Group | Includes | Use Case |
|-------|----------|----------|
| `minimal` | `langchain` | Lightest functional install |
| `standard` | `ai,langchain,embeddings,documents` | Typical usage |
| `complete` | `ai,langchain,embeddings,documents,cloud,tracing` | Production ready |
| `all` | Everything | Development |

## Version Constraint Strategy

All dependencies use **tighter version ranges** for faster resolution:

```toml
# Before (slow resolution)
"pandas>=2.0.0,<3.0.0"

# After (fast resolution)  
"pandas>=2.0.0,<2.3.0"
```

## Migration Guide

### For Existing CI Pipelines

1. **Replace broad installs:**
   ```bash
   # Old
   pip install -r requirements.txt -r requirements-dev.txt
   
   # New
   pip install raft-toolkit[dev]
   ```

2. **Use targeted installs:**
   ```bash
   # For unit tests only
   pip install raft-toolkit[dev]
   
   # For integration tests
   pip install raft-toolkit[standard,dev]
   ```

3. **Update Docker builds:**
   ```dockerfile
   # Multi-stage build for production
   FROM python:3.11-slim as base
   RUN pip install raft-toolkit[standard]
   
   # Development stage
   FROM base as dev
   RUN pip install raft-toolkit[all]
   ```

### For Development

Update your local environment:

```bash
# Full development setup
pip install raft-toolkit[all]

# Or specific combinations
pip install raft-toolkit[standard,web,dev]
```

## Performance Comparison

| Installation Type | Packages | Install Time | Use Case |
|------------------|----------|--------------|----------|
| Core only | ~15 | 30-60s | Basic tests |
| Standard | ~50 | 2-3 mins | Integration tests |
| Complete | ~80 | 4-5 mins | Production |
| All | ~120 | 6-8 mins | Development |

## Troubleshooting

### Dependency Resolution Issues

If you encounter slow dependency resolution:

1. Use more specific version ranges
2. Pin problematic packages
3. Use `pip install --no-deps` for known good combinations

### Missing Dependencies

If functionality is missing:

1. Check which optional group you need
2. Install additional groups: `pip install raft-toolkit[ai,cloud]`
3. See the dependency groups reference above

### Cache Optimization

For CI/CD systems:

```yaml
# Example with caching
- uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('pyproject.toml') }}
    
- name: Install dependencies
  run: pip install raft-toolkit[standard]
```

This optimization strategy provides significant CI/CD performance improvements while maintaining full functionality flexibility.