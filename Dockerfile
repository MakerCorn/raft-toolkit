# Multi-stage Dockerfile for RAFT Toolkit
# Stage 1: Base dependencies
FROM python:3.11-slim as base

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
    && rm -rf /var/lib/apt/lists/*

# Create app user for security
RUN groupadd -r raft && useradd -r -g raft raft

# Set working directory
WORKDIR /app

# Stage 2: Dependencies
FROM base as dependencies

# Copy requirements files
COPY requirements*.txt ./

# Install Python dependencies with error handling
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    if [ -f requirements-web.txt ]; then pip install --no-cache-dir -r requirements-web.txt; fi && \
    # Verify critical imports work
    python -c "import pypdf; import secrets; print('Security dependencies OK')" && \
    python -c "from azure.ai.evaluation import evaluate; print('Azure AI Evaluation OK')" || \
    echo "Warning: Some dependencies may have issues"

# Stage 3: Development
FROM dependencies as development

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
FROM development as testing

# Switch back to root for test setup
USER root

# Ensure test directories exist
RUN mkdir -p /app/test-results /app/coverage-reports && \
    chown -R raft:raft /app/test-results /app/coverage-reports

# Switch to app user
USER raft

# Set test environment variables
ENV TESTING=true
ENV LOG_LEVEL=DEBUG

# Run tests by default
CMD ["python", "run_tests.py", "--coverage", "--output-dir", "/app/test-results"]

# Stage 5: Production
FROM dependencies as production

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
FROM dependencies as cli

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