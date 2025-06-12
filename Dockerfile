# Multi-stage Dockerfile for RAFT Toolkit
# Follows Docker best practices and security guidelines

# Stage 1: Base dependencies
FROM python:3.11-slim AS base

# Add metadata labels
LABEL maintainer="RAFT Toolkit Team" \
      description="Retrieval Augmentation Fine-Tuning Toolkit" \
      version="0.1.0" \
      org.opencontainers.image.source="https://github.com/your-org/raft-toolkit"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    gcc \
    g++ \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create app user for security
RUN groupadd -r raft && useradd -r -g raft raft

# Set working directory
WORKDIR /app

# Stage 2: Dependencies
FROM base AS dependencies

# Copy requirements files
COPY requirements*.txt ./

# Install Python dependencies with enhanced error handling
RUN pip install --upgrade pip && \
    # Install core requirements first
    echo "📦 Installing core dependencies..." && \
    pip install --no-cache-dir -r requirements.txt && \
    echo "✅ Core dependencies installed successfully" && \
    # Install web dependencies if they exist
    if [ -f requirements-web.txt ]; then \
        echo "🌐 Installing web dependencies..." && \
        pip install --no-cache-dir -r requirements-web.txt && \
        echo "✅ Web dependencies installed successfully"; \
    fi && \
    # Verify critical imports work
    echo "🔍 Verifying critical dependencies..." && \
    python -c "import pypdf; import secrets; print('✅ Security dependencies OK')" && \
    python -c "import openai; print('✅ OpenAI', openai.__version__, 'OK')" && \
    python -c "from azure.ai.evaluation import evaluate; print('✅ Azure AI Evaluation OK')" && \
    python -c "import fastapi; print('✅ FastAPI', fastapi.__version__, 'OK')" && \
    # Run dependency conflict check
    echo "🔗 Checking for dependency conflicts..." && \
    pip check && \
    echo "🎉 All dependency verification completed successfully" || \
    (echo "❌ Dependency verification failed. Run 'python scripts/check_dependencies.py' for details" && exit 1)

# Stage 3: Development
FROM dependencies AS development

# Install development and testing dependencies
RUN if [ -f requirements-test.txt ]; then pip install --no-cache-dir -r requirements-test.txt; fi

# Install debugging tools
RUN pip install debugpy ipdb

# Copy source code
COPY . .

# Create necessary directories and set permissions
RUN mkdir -p /app/data /app/outputs /app/logs /app/uploads /app/test-results && \
    chown -R raft:raft /app

# Switch to app user
USER raft

# Expose ports (app and debugger)
EXPOSE 8000 5678

# Development command with debugging support
CMD ["python", "-m", "debugpy", "--listen", "0.0.0.0:5678", "--wait-for-client", "run_web.py", "--host", "0.0.0.0", "--debug"]

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
ENV TESTING=true \
    LOG_LEVEL=DEBUG \
    PYTHONPATH=/app

# Health check for testing container
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=2 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Run tests by default - uses environment variables for directory configuration
CMD ["python", "run_tests.py", "--coverage"]

# Stage 5: Production
FROM dependencies AS production

# Copy source code
COPY . .

# Remove unnecessary files for production
RUN rm -rf tests/ docs/ examples/ .git/ .github/ notebooks/ && \
    find . -name "*.pyc" -delete && \
    find . -name "__pycache__" -type d -exec rm -rf {} + || true && \
    find . -name "*.pytest_cache" -type d -exec rm -rf {} + || true

# Create necessary directories and set permissions
RUN mkdir -p /app/data /app/outputs /app/logs /app/uploads && \
    chown -R raft:raft /app

# Switch to app user
USER raft

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Production command
CMD ["python", "run_web.py", "--host", "0.0.0.0", "--port", "8000"]

# Stage 6: CLI-only (lightweight)
FROM dependencies AS cli

# Copy only CLI-related files
COPY core/ ./core/
COPY cli/ ./cli/
COPY tools/ ./tools/
COPY templates/ ./templates/
COPY raft.py ./

# Create necessary directories and set permissions
RUN mkdir -p /app/data /app/outputs && \
    chown -R raft:raft /app

# Switch to app user
USER raft

# CLI command
ENTRYPOINT ["python", "raft.py"]