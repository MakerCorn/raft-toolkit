# 🚀 RAFT Toolkit Deployment Guide

> **Comprehensive guide for deploying RAFT Toolkit in various environments**

This guide covers deployment options from local development to production cloud deployments, including Docker, Kubernetes, and major cloud platforms.

---

## 📋 Table of Contents

- [🏠 Local Development](#-local-development)
- [🐳 Docker Deployment](#-docker-deployment)
- [☸️ Kubernetes Deployment](#️-kubernetes-deployment)
- [🚀 Advanced Deployment Patterns](#-advanced-deployment-patterns)
  - [Multi-Target Docker Builds](#multi-target-docker-builds)
  - [Production Environment Configuration](#production-environment-configuration)
  - [Enhanced Monitoring & Observability](#enhanced-monitoring--observability)
  - [Advanced Security Configuration](#advanced-security-configuration)
  - [Multi-Cloud Kubernetes Quick Deploy](#multi-cloud-kubernetes-quick-deploy)
- [☁️ Cloud Platforms](#️-cloud-platforms)
  - [AWS Deployment](#aws-deployment)
  - [Azure Deployment](#azure-deployment)
  - [Google Cloud Deployment](#google-cloud-deployment)
- [🔒 Security Considerations](#-security-considerations)
- [🔄 CI/CD Integration](#-cicd-integration)
  - [GitHub Actions Workflows](#github-actions-workflows)
  - [Environment Variables for CI/CD](#environment-variables-for-cicd)
  - [Pipeline Configuration Examples](#pipeline-configuration-examples)
  - [Testing & Release Infrastructure](#testing--release-infrastructure)
- [📊 Monitoring & Logging](#-monitoring--logging)
- [🔧 Troubleshooting](#-troubleshooting)

---

## 🏠 Local Development

### Quick Setup

```bash
# Clone and install
git clone <repository-url>
cd raft-toolkit
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Run CLI
python raft.py --help

# Run web interface
python run_web.py
```

### Development Server

```bash
# Development mode with auto-reload
python run_web.py --debug --reload

# Custom host/port
python run_web.py --host 0.0.0.0 --port 8080

# With specific workers
python run_web.py --workers 4
```

### Environment Configuration

Create `.env` file:

```bash
# Core Configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_API_BASE_URL=https://api.openai.com/v1

# Web Server
WEB_HOST=127.0.0.1
WEB_PORT=8000
WEB_DEBUG=true
WEB_WORKERS=1

# Processing
DEFAULT_WORKERS=4
MAX_WORKERS=8
JOB_TIMEOUT=3600

# File Upload
MAX_UPLOAD_SIZE=52428800  # 50MB
UPLOAD_TIMEOUT=300

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=detailed
```

---

## 🐳 Docker Deployment

### Docker Compose (Recommended)

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  raft-toolkit:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - WEB_HOST=0.0.0.0
      - WEB_PORT=8000
      - WEB_WORKERS=4
    volumes:
      - ./data:/app/data
      - ./outputs:/app/outputs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

**Dockerfile**:
```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements*.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN groupadd -r raft && useradd -r -g raft raft
RUN chown -R raft:raft /app
USER raft

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start command
CMD ["python", "run_web.py", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Commands

```bash
# Build and run with Docker Compose
docker-compose up -d

# Scale services
docker-compose up -d --scale raft-toolkit=3

# View logs
docker-compose logs -f raft-toolkit

# Update and restart
docker-compose pull
docker-compose up -d

# Stop services
docker-compose down
```

### Production Docker Setup

**docker-compose.prod.yml**:
```yaml
version: '3.8'

services:
  raft-toolkit:
    build: .
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - WEB_HOST=0.0.0.0
      - WEB_WORKERS=4
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - raft-toolkit
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
```

---

## ☸️ Kubernetes Deployment

### Namespace and ConfigMap

**namespace.yaml**:
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: raft-toolkit
```

**configmap.yaml**:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: raft-config
  namespace: raft-toolkit
data:
  WEB_HOST: "0.0.0.0"
  WEB_PORT: "8000"
  WEB_WORKERS: "4"
  DEFAULT_WORKERS: "4"
  MAX_WORKERS: "16"
  LOG_LEVEL: "INFO"
```

### Secrets

**secrets.yaml**:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: raft-secrets
  namespace: raft-toolkit
type: Opaque
data:
  OPENAI_API_KEY: <base64-encoded-api-key>
  # AZURE_OPENAI_KEY: <base64-encoded-azure-key>
```

### Deployment

**deployment.yaml**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: raft-toolkit
  namespace: raft-toolkit
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
        image: raft-toolkit:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: raft-secrets
              key: OPENAI_API_KEY
        envFrom:
        - configMapRef:
            name: raft-config
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        volumeMounts:
        - name: data-storage
          mountPath: /app/data
      volumes:
      - name: data-storage
        persistentVolumeClaim:
          claimName: raft-data-pvc
```

### Service and Ingress

**service.yaml**:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: raft-toolkit-service
  namespace: raft-toolkit
spec:
  selector:
    app: raft-toolkit
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
```

**ingress.yaml**:
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: raft-toolkit-ingress
  namespace: raft-toolkit
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/client-max-body-size: "50m"
spec:
  tls:
  - hosts:
    - raft.yourdomain.com
    secretName: raft-tls
  rules:
  - host: raft.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: raft-toolkit-service
            port:
              number: 80
```

### Deploy to Kubernetes

```bash
# Apply all resources
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f secrets.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml

# Check deployment
kubectl get pods -n raft-toolkit
kubectl get services -n raft-toolkit
kubectl get ingress -n raft-toolkit

# View logs
kubectl logs -f deployment/raft-toolkit -n raft-toolkit

# Scale deployment
kubectl scale deployment raft-toolkit --replicas=5 -n raft-toolkit
```

---

## 🚀 Advanced Deployment Patterns

### Multi-Target Docker Builds

RAFT Toolkit supports multiple build targets optimized for different use cases:

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

### Production Environment Configuration

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

### Enhanced Monitoring & Observability

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

### Advanced Security Configuration

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

### Production Deployment Patterns

**Docker Compose Production Setup:**
```bash
# Production stack with Redis and monitoring
docker compose -f docker-compose.yml up -d

# Development with hot reload
docker compose -f docker-compose.dev.yml up -d

# Testing environment
docker compose -f docker-compose.test.yml up
```

**Single Container Production:**
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

### Multi-Cloud Kubernetes Quick Deploy

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

---

## ☁️ Cloud Platforms

### AWS Deployment

#### ECS with Fargate

**task-definition.json**:
```json
{
  "family": "raft-toolkit",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "2048",
  "memory": "4096",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "raft-toolkit",
      "image": "your-account.dkr.ecr.region.amazonaws.com/raft-toolkit:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "WEB_HOST",
          "value": "0.0.0.0"
        },
        {
          "name": "WEB_WORKERS",
          "value": "4"
        }
      ],
      "secrets": [
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:raft/openai-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/raft-toolkit",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3
      }
    }
  ]
}
```

**ECS Service with ALB**:
```bash
# Create ECS cluster
aws ecs create-cluster --cluster-name raft-toolkit

# Register task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Create service
aws ecs create-service \
  --cluster raft-toolkit \
  --service-name raft-toolkit-service \
  --task-definition raft-toolkit:1 \
  --desired-count 3 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-12345,subnet-67890],securityGroups=[sg-12345],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:region:account:targetgroup/raft-toolkit/1234567890123456,containerName=raft-toolkit,containerPort=8000"
```

#### Lambda Deployment (Serverless)

**serverless.yml**:
```yaml
service: raft-toolkit

provider:
  name: aws
  runtime: python3.11
  region: us-west-2
  timeout: 900
  memorySize: 3008
  environment:
    OPENAI_API_KEY: ${ssm:/raft-toolkit/openai-api-key}

functions:
  api:
    handler: lambda_handler.handler
    events:
      - http:
          path: /{proxy+}
          method: ANY
          cors: true
    layers:
      - arn:aws:lambda:us-west-2:123456789:layer:python-deps:1

plugins:
  - serverless-python-requirements
  - serverless-wsgi

custom:
  wsgi:
    app: web.app
    packRequirements: false
  pythonRequirements:
    dockerizePip: true
    layer: true
```

### Azure Deployment

#### Container Apps

**containerapp.yaml**:
```yaml
apiVersion: 2022-03-01
location: eastus
resourceGroup: raft-toolkit-rg
properties:
  managedEnvironmentId: /subscriptions/{subscription}/resourceGroups/raft-toolkit-rg/providers/Microsoft.App/managedEnvironments/raft-env
  configuration:
    ingress:
      external: true
      targetPort: 8000
      allowInsecure: false
    secrets:
    - name: openai-api-key
      value: your-openai-api-key
  template:
    containers:
    - name: raft-toolkit
      image: raftregistry.azurecr.io/raft-toolkit:latest
      env:
      - name: OPENAI_API_KEY
        secretRef: openai-api-key
      - name: WEB_HOST
        value: "0.0.0.0"
      - name: WEB_WORKERS
        value: "4"
      resources:
        cpu: 2.0
        memory: 4Gi
    scale:
      minReplicas: 1
      maxReplicas: 10
      rules:
      - name: http-rule
        http:
          metadata:
            concurrentRequests: '100'
```

Deploy with Azure CLI:
```bash
# Create resource group
az group create --name raft-toolkit-rg --location eastus

# Create container registry
az acr create --resource-group raft-toolkit-rg --name raftregistry --sku Basic

# Build and push image
az acr build --registry raftregistry --image raft-toolkit:latest .

# Create container app environment
az containerapp env create \
  --name raft-env \
  --resource-group raft-toolkit-rg \
  --location eastus

# Deploy container app
az containerapp create \
  --name raft-toolkit \
  --resource-group raft-toolkit-rg \
  --environment raft-env \
  --image raftregistry.azurecr.io/raft-toolkit:latest \
  --target-port 8000 \
  --ingress external \
  --secrets openai-api-key=your-openai-api-key \
  --env-vars OPENAI_API_KEY=secretref:openai-api-key WEB_HOST=0.0.0.0 WEB_WORKERS=4
```

### Google Cloud Deployment

#### Cloud Run

**cloudrun.yaml**:
```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: raft-toolkit
  annotations:
    run.googleapis.com/ingress: all
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/maxScale: "10"
        run.googleapis.com/execution-environment: gen2
        run.googleapis.com/cpu-throttling: "false"
    spec:
      containerConcurrency: 100
      timeoutSeconds: 900
      containers:
      - image: gcr.io/PROJECT_ID/raft-toolkit:latest
        ports:
        - containerPort: 8000
        env:
        - name: WEB_HOST
          value: "0.0.0.0"
        - name: WEB_PORT
          value: "8000"
        - name: WEB_WORKERS
          value: "4"
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: openai-api-key
              key: key
        resources:
          limits:
            cpu: 2000m
            memory: 4Gi
```

Deploy with gcloud:
```bash
# Build and push to Container Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/raft-toolkit

# Create secret
echo -n "your-openai-api-key" | gcloud secrets create openai-api-key --data-file=-

# Deploy to Cloud Run
gcloud run deploy raft-toolkit \
  --image gcr.io/PROJECT_ID/raft-toolkit:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8000 \
  --memory 4Gi \
  --cpu 2 \
  --concurrency 100 \
  --max-instances 10 \
  --set-env-vars WEB_HOST=0.0.0.0,WEB_WORKERS=4 \
  --set-secrets OPENAI_API_KEY=openai-api-key:latest
```

---

## 🔒 Security Considerations

### API Key Management

**Environment Variables**: Never commit API keys to source control
```bash
# Use secret management services
export OPENAI_API_KEY=$(aws secretsmanager get-secret-value --secret-id raft/openai --query SecretString --output text)
```

**Secret Rotation**: Implement automatic key rotation
```bash
# Example rotation script
#!/bin/bash
NEW_KEY=$(generate_new_api_key)
aws secretsmanager update-secret --secret-id raft/openai --secret-string "$NEW_KEY"
kubectl rollout restart deployment/raft-toolkit -n raft-toolkit
```

### Network Security

**HTTPS/TLS**: Always use HTTPS in production
```nginx
server {
    listen 443 ssl http2;
    server_name raft.yourdomain.com;
    
    ssl_certificate /etc/ssl/certs/raft.crt;
    ssl_certificate_key /etc/ssl/private/raft.key;
    
    location / {
        proxy_pass http://raft-toolkit:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Firewall Rules**: Restrict access to necessary ports
```bash
# AWS Security Group
aws ec2 authorize-security-group-ingress \
  --group-id sg-12345678 \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0

# Block direct access to application port
aws ec2 revoke-security-group-ingress \
  --group-id sg-12345678 \
  --protocol tcp \
  --port 8000 \
  --cidr 0.0.0.0/0
```

### Authentication & Authorization

**API Authentication**: Implement API key authentication
```python
# In web application
@app.middleware("http")
async def verify_api_key(request: Request, call_next):
    if request.url.path.startswith("/api/"):
        api_key = request.headers.get("X-API-Key")
        if not verify_api_key(api_key):
            return JSONResponse({"error": "Invalid API key"}, status_code=401)
    return await call_next(request)
```

**OAuth Integration**: For enterprise deployments
```python
# OAuth configuration
OAUTH_CONFIG = {
    "client_id": os.getenv("OAUTH_CLIENT_ID"),
    "client_secret": os.getenv("OAUTH_CLIENT_SECRET"),
    "authorize_url": "https://auth.company.com/oauth/authorize",
    "token_url": "https://auth.company.com/oauth/token"
}
```

---

## 🔄 CI/CD Integration

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
- 🐍 **Multi-Python Support**: Testing on Python 3.11, 3.12
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

### Testing & Release Infrastructure

#### Recent Major Improvements (v1.0.1)

The RAFT Toolkit now includes a robust, fully-automated testing and release infrastructure:

**✅ Complete Test Suite Reliability**
- **43/43 unit tests passing**: All unit test failures have been resolved
- **Fixed critical test issues**: Mock paths, environment isolation, token caching
- **Cross-platform testing**: Linux, macOS, and Windows support
- **Multi-Python version testing**: Python 3.11 and 3.12

**🚀 Automated Release Pipeline**
- **Tag-triggered releases**: Create releases by pushing version tags
- **Build system fixes**: Resolved package discovery and build configuration issues
- **GitHub Actions integration**: Automated building, testing, and publishing
- **Release tools**: Interactive release script for safe version management

**🛠️ Enhanced Developer Experience**
- **Release script**: `./scripts/create_release.sh` for guided release creation
- **Build validation**: Local testing before CI/CD deployment
- **Comprehensive documentation**: Step-by-step guides for releases and testing

**📦 Improved Build System**
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

See [Release Management Guide](docs/RELEASES.md) for the complete release management guide.

---

## 📊 Monitoring & Logging

### Application Monitoring

**Health Checks**: Implement comprehensive health endpoints
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": get_version(),
        "dependencies": {
            "openai": check_openai_connection(),
            "redis": check_redis_connection(),
            "disk_space": check_disk_space()
        }
    }
```

**Metrics Collection**: Use Prometheus metrics
```python
from prometheus_client import Counter, Histogram, generate_latest

REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    REQUEST_DURATION.observe(time.time() - start_time)
    return response
```

### Logging Configuration

**Structured Logging**:
```python
import structlog

logger = structlog.get_logger()

logger.info("Processing started", 
           job_id=job_id, 
           file_size=file_size, 
           user_id=user_id)
```

**Log Aggregation** (ELK Stack):
```yaml
# docker-compose.logging.yml
version: '3.8'
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.5.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    
  logstash:
    image: docker.elastic.co/logstash/logstash:8.5.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    
  kibana:
    image: docker.elastic.co/kibana/kibana:8.5.0
    ports:
      - "5601:5601"
```

### Alerting

**PagerDuty Integration**:
```python
def send_alert(message, severity="high"):
    payload = {
        "routing_key": os.getenv("PAGERDUTY_ROUTING_KEY"),
        "event_action": "trigger",
        "payload": {
            "summary": message,
            "severity": severity,
            "source": "raft-toolkit"
        }
    }
    requests.post("https://events.pagerduty.com/v2/enqueue", json=payload)
```

**Slack Notifications**:
```python
def notify_slack(message, channel="#alerts"):
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    payload = {
        "channel": channel,
        "text": message,
        "username": "RAFT Toolkit"
    }
    requests.post(webhook_url, json=payload)
```

---

## 🔧 Troubleshooting

### Common Deployment Issues

#### Container Issues

**Image Build Failures**:
```bash
# Check Docker build context
docker build --no-cache -t raft-toolkit .

# Debug build steps
docker build --target builder -t raft-debug .
docker run -it raft-debug /bin/bash
```

**Memory Issues**:
```bash
# Check container memory usage
docker stats raft-toolkit

# Increase memory limits
docker run -m 4g raft-toolkit
```

#### Kubernetes Issues

**Pod Failures**:
```bash
# Check pod status
kubectl describe pod <pod-name> -n raft-toolkit

# View logs
kubectl logs <pod-name> -n raft-toolkit --previous

# Debug with temporary pod
kubectl run debug --image=busybox -it --rm -- /bin/sh
```

**Service Discovery**:
```bash
# Test service connectivity
kubectl exec -it <pod-name> -n raft-toolkit -- curl http://redis:6379

# Check DNS resolution
kubectl exec -it <pod-name> -n raft-toolkit -- nslookup redis
```

#### Load Balancer Issues

**Health Check Failures**:
```bash
# Test health endpoint directly
curl -v http://pod-ip:8000/health

# Check load balancer configuration
aws elbv2 describe-target-health --target-group-arn <arn>
```

**SSL Certificate Issues**:
```bash
# Check certificate validity
openssl x509 -in certificate.crt -text -noout

# Test SSL connection
openssl s_client -connect raft.yourdomain.com:443
```

### Performance Issues

**High CPU Usage**:
```bash
# Profile application
python -m cProfile -o profile.stats run_web.py

# Analyze profile
python -c "import pstats; pstats.Stats('profile.stats').sort_stats('cumulative').print_stats(20)"
```

**Memory Leaks**:
```bash
# Monitor memory usage
python -m memory_profiler run_web.py

# Use memory debugging
python -m tracemalloc run_web.py
```

**Slow Requests**:
```bash
# Enable request tracing
export TRACE_REQUESTS=true
python run_web.py

# Use APM tools
pip install elastic-apm
export ELASTIC_APM_SERVICE_NAME=raft-toolkit
```

### Database/Redis Issues

**Connection Problems**:
```bash
# Test Redis connectivity
redis-cli -h redis-host -p 6379 ping

# Check Redis logs
docker logs redis-container

# Monitor Redis performance
redis-cli --latency-history -h redis-host -p 6379
```

**Data Persistence**:
```bash
# Check Redis persistence
redis-cli config get save
redis-cli config get appendonly

# Backup Redis data
redis-cli --rdb backup.rdb
```

---

## 📚 Additional Resources

### Infrastructure as Code

**Terraform Examples**: [examples/terraform/](examples/terraform/)
**Helm Charts**: [examples/helm/](examples/helm/)
**Ansible Playbooks**: [examples/ansible/](examples/ansible/)

### CI/CD Integration

**GitHub Actions**: [.github/workflows/deploy.yml](.github/workflows/deploy.yml)
**GitLab CI**: [.gitlab-ci.yml](.gitlab-ci.yml)
**Jenkins Pipeline**: [Jenkinsfile](Jenkinsfile)

### Monitoring Dashboards

**Grafana Dashboards**: [monitoring/grafana/](monitoring/grafana/)
**Datadog Integration**: [monitoring/datadog/](monitoring/datadog/)
**CloudWatch Dashboards**: [monitoring/cloudwatch/](monitoring/cloudwatch/)

---

For platform-specific deployment guides and examples, see the `docs/deployment/` directory in the repository.