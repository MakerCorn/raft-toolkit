# Multi-stage Dockerfile for RAFT Toolkit
# Follows Docker best practices and security guidelines

# Build arguments for dynamic configuration
ARG PYTHON_VERSION=3.11
ARG BUILD_DATE
ARG VERSION=0.2.0
ARG VCS_REF

# Stage 1: Base dependencies
FROM python:3.11-slim-bookworm AS base

# Add metadata labels
LABEL maintainer="RAFT Toolkit Team" \
      description="Retrieval Augmented Fine-Tuning Toolkit for generating synthetic Q&A datasets" \
      version="${VERSION:-0.2.0}" \
      org.opencontainers.image.title="RAFT Toolkit" \
      org.opencontainers.image.description="Retrieval Augmented Fine-Tuning Toolkit" \
      org.opencontainers.image.version="${VERSION:-0.2.0}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.source="https://github.com/makercorn/raft-toolkit" \
      org.opencontainers.image.licenses="MIT"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app

# Install system dependencies with security updates
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    gcc \
    g++ \
    build-essential \
    && apt-get upgrade -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create app user for security
RUN groupadd -r raft && useradd -r -g raft raft

# Set working directory
WORKDIR /app

# Stage 2: Dependencies
FROM base AS dependencies

# Copy project configuration
COPY pyproject.toml ./

# Install Python dependencies with enhanced error handling
RUN pip install --upgrade pip setuptools wheel && \
    # Install the package with core dependencies
    echo "Installing RAFT Toolkit with core dependencies..." && \
    pip install --no-cache-dir -e . && \
    echo "Core dependencies installed successfully" && \
    # Verify core dependencies only (transformers/langchain_community are optional)
    echo "Verifying critical dependencies..." && \
    python -c "import pypdf; print('PyPDF OK')" && \
    python -c "import openai; print('OpenAI', openai.__version__, 'OK')" && \
    python -c "import pandas; print('Pandas OK')" && \
    python -c "import pydantic; print('Pydantic OK')" && \
    python -c "import langchain_core; print('LangChain Core OK')" && \
    python -c "import tiktoken; print('TikToken OK')" && \
    # Run dependency conflict check
    echo "Checking for dependency conflicts..." && \
    pip check && \
    echo "All dependency verification completed successfully" || \
    (echo "Dependency verification failed. Check package dependencies" && exit 1)

# Stage 3: Development
FROM dependencies AS development

# Install development and testing dependencies
RUN pip install --no-cache-dir -e .[dev,all] && \
    pip install debugpy ipdb && \
    # Verify optional dependencies are now available
    echo "Verifying extended dependencies..." && \
    python -c "import transformers; print('Transformers OK')" && \
    python -c "import langchain_community; print('LangChain Community OK')" && \
    python -c "import sentence_transformers; print('Sentence Transformers OK')" && \
    echo "All development dependencies verified successfully"

# Copy source code
COPY . .

# Create necessary directories and set permissions
RUN mkdir -p /app/data /app/outputs /app/logs /app/uploads /app/test-results && \
    chown -R raft:raft /app

# Switch to app user
USER raft

# Expose ports (app and debugger)
EXPOSE 8000 5678

# Set development environment variables
ENV RAFT_ENVIRONMENT=development \
    RAFT_LOG_LEVEL=DEBUG

# Development command with debugging support
CMD ["python", "-m", "raft_toolkit.web.app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Stage 4: Testing
FROM development AS testing

# Switch back to root for test setup
USER root

# Create configurable test directories with defaults
ENV TEST_OUTPUT_DIR=/app/test-results \
    TEST_TEMP_DIR=/tmp/test-temp \
    TEST_COVERAGE_DIR=/app/coverage-reports

# Ensure test directories exist
RUN mkdir -p $TEST_OUTPUT_DIR $TEST_TEMP_DIR $TEST_COVERAGE_DIR && \
    chown -R raft:raft $TEST_OUTPUT_DIR $TEST_TEMP_DIR $TEST_COVERAGE_DIR && \
    # Make temp directory sticky for multi-user access
    chmod 1777 $TEST_TEMP_DIR

# Switch to app user
USER raft

# Set test environment variables
ENV RAFT_TESTING=true \
    RAFT_LOG_LEVEL=DEBUG \
    PYTHONPATH=/app

# Health check for testing container
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=2 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Run tests by default - uses pytest
CMD ["python", "-m", "pytest", "tests/", "-v", "--cov=raft_toolkit", "--cov-report=xml", "--cov-report=term-missing"]

# Stage 5: Production Web Application
FROM dependencies AS production

# Build-time arguments for optimization
ARG KUBERNETES_OPTIMIZED=false

# Install web dependencies
RUN pip install --no-cache-dir -e .[web] && \
    if [ "$KUBERNETES_OPTIMIZED" = "true" ]; then \
        echo "Installing Kubernetes optimizations..." && \
        pip install --no-cache-dir -e .[kubernetes] && \
        echo "Kubernetes dependencies installed successfully"; \
    fi

# Copy source code
COPY . .

# Remove unnecessary files for production
RUN rm -rf tests/ docs/ examples/ .git/ .github/ notebooks/ scripts/ && \
    find . -name "*.pyc" -delete && \
    find . -name "__pycache__" -type d -exec rm -rf {} + || true && \
    find . -name "*.pytest_cache" -type d -exec rm -rf {} + || true && \
    find . -name ".coverage" -delete || true

# Create necessary directories and set permissions
RUN mkdir -p /app/data /app/outputs /app/logs /app/uploads && \
    chown -R raft:raft /app

# Add Kubernetes-specific labels when optimized
LABEL io.kubernetes.container.name="raft-toolkit" \
      io.kubernetes.container.component="web" \
      io.openshift.expose-services="8000:http"

# Set production environment variables
ENV RAFT_ENVIRONMENT=production \
    RAFT_LOG_LEVEL=INFO \
    RAFT_LOG_FORMAT=json \
    RAFT_LOG_OUTPUT=stdout \
    PYTHONUNBUFFERED=1

# Switch to app user
USER raft

# Health check (Kubernetes-friendly)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Production command using the web entry point
CMD ["python", "-m", "raft_toolkit.web.app", "--host", "0.0.0.0", "--port", "8000"]

# Stage 6: CLI-only (lightweight)
FROM base AS cli

# Copy project configuration and install minimal dependencies
COPY pyproject.toml ./

# Install only core dependencies (no web, no dev)
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -e . && \
    echo "CLI dependencies installed successfully"

# Copy only CLI-related files
COPY raft_toolkit/ ./raft_toolkit/

# Copy source files
COPY . .

# Remove unnecessary files for CLI-only image
RUN rm -rf raft_toolkit/web/ tests/ docs/ examples/ .git/ .github/ notebooks/ scripts/ && \
    find . -name "*.pyc" -delete && \
    find . -name "__pycache__" -type d -exec rm -rf {} + || true

# Create necessary directories and set permissions
RUN mkdir -p /app/data /app/outputs /app/logs && \
    chown -R raft:raft /app

# Add CLI-specific labels
LABEL io.kubernetes.container.name="raft-toolkit" \
      io.kubernetes.container.component="cli"

# Set CLI environment variables
ENV RAFT_ENVIRONMENT=cli \
    RAFT_LOG_LEVEL=INFO \
    PYTHONUNBUFFERED=1

# Switch to app user
USER raft

# Set working directory for data processing
WORKDIR /app

# CLI entry point using the CLI module
ENTRYPOINT ["python", "-m", "raft_toolkit.cli.main"]
CMD ["--help"]