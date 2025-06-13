# Kubernetes Deployment Guide

This guide provides comprehensive instructions for deploying RAFT Toolkit on Kubernetes clusters across major cloud providers: Azure Kubernetes Service (AKS), Amazon Elastic Kubernetes Service (EKS), and Google Kubernetes Engine (GKE).

## 🏗️ Architecture Overview

The RAFT Toolkit Kubernetes deployment includes:

- **Web Interface**: Scalable web application for interactive dataset generation
- **CLI Jobs**: Batch processing capabilities for automated workflows
- **Persistent Storage**: Document input and dataset output storage
- **Configuration Management**: Environment-based configuration with secrets
- **Monitoring**: Health checks and observability endpoints
- **Security**: Non-root containers, network policies, and RBAC

## 📋 Prerequisites

### Common Requirements

- **Docker**: For building and pushing container images
- **kubectl**: Kubernetes command-line tool
- **kustomize**: For managing Kubernetes configurations
- **OpenAI API Key**: Required for AI model access

### Cloud-Specific Tools

#### Azure (AKS)
- **Azure CLI**: `az` command-line tool
- **Azure Account**: With appropriate permissions

#### AWS (EKS)
- **AWS CLI**: `aws` command-line tool
- **eksctl**: EKS cluster management tool
- **Helm**: Package manager for Kubernetes (for AWS Load Balancer Controller)

#### Google Cloud (GKE)
- **Google Cloud SDK**: `gcloud` command-line tool
- **Google Cloud Project**: With billing enabled

## 🚀 Quick Start Deployment

### Option 1: Automated Deployment Scripts

We provide automated deployment scripts for each cloud provider:

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

### Option 2: Manual Deployment with Kustomize

```bash
# 1. Clone the repository
git clone https://github.com/your-org/raft-toolkit.git
cd raft-toolkit

# 2. Build and push the Docker image
docker build -t raft-toolkit:latest .
docker tag raft-toolkit:latest your-registry/raft-toolkit:latest
docker push your-registry/raft-toolkit:latest

# 3. Create secrets
kubectl create namespace raft-toolkit
kubectl create secret generic raft-toolkit-secrets \
  --namespace=raft-toolkit \
  --from-literal=OPENAI_API_KEY="your-openai-api-key" \
  --from-literal=OPENAI_API_BASE_URL="https://api.openai.com/v1"

# 4. Deploy using kustomize
# For AKS:
cd k8s/overlays/aks
kustomize edit set image raft-toolkit=your-acr.azurecr.io/raft-toolkit:latest
kustomize build . | kubectl apply -f -

# For EKS:
cd k8s/overlays/eks
kustomize edit set image raft-toolkit=your-account.dkr.ecr.region.amazonaws.com/raft-toolkit:latest
kustomize build . | kubectl apply -f -

# For GKE:
cd k8s/overlays/gks
kustomize edit set image raft-toolkit=gcr.io/your-project/raft-toolkit:latest
kustomize build . | kubectl apply -f -
```

### Option 3: Helm Deployment

```bash
# 1. Install using Helm
helm install raft-toolkit ./k8s/helm \
  --namespace raft-toolkit \
  --create-namespace \
  --set secrets.openaiApiKey="your-openai-api-key" \
  --set image.repository="your-registry/raft-toolkit" \
  --set image.tag="latest"

# 2. Upgrade deployment
helm upgrade raft-toolkit ./k8s/helm \
  --namespace raft-toolkit \
  --set secrets.openaiApiKey="your-openai-api-key"
```

## ☁️ Cloud-Specific Deployment Guides

### Azure Kubernetes Service (AKS)

#### Automated Deployment

```bash
# Set required environment variables
export OPENAI_API_KEY="your-openai-api-key"
export RESOURCE_GROUP="raft-toolkit-rg"
export CLUSTER_NAME="raft-toolkit-aks"
export LOCATION="eastus"
export ACR_NAME="raftoolkitacr"

# Optional: Azure OpenAI configuration
export AZURE_CLIENT_ID="your-azure-client-id"
export AZURE_TENANT_ID="your-azure-tenant-id"
export AZURE_SUBSCRIPTION_ID="your-azure-subscription-id"

# Deploy
./k8s/scripts/deploy-aks.sh
```

#### Manual AKS Setup

```bash
# 1. Create resource group
az group create --name raft-toolkit-rg --location eastus

# 2. Create Azure Container Registry
az acr create --resource-group raft-toolkit-rg --name raftoolkitacr --sku Basic

# 3. Create AKS cluster
az aks create \
  --resource-group raft-toolkit-rg \
  --name raft-toolkit-aks \
  --node-count 3 \
  --enable-addons monitoring \
  --generate-ssh-keys \
  --attach-acr raftoolkitacr

# 4. Get credentials
az aks get-credentials --resource-group raft-toolkit-rg --name raft-toolkit-aks

# 5. Deploy application
cd k8s/overlays/aks
kustomize build . | kubectl apply -f -
```

#### AKS Features

- **Azure CNI networking** for advanced networking features
- **Azure Container Registry** integration for seamless image management
- **Azure Application Gateway Ingress Controller** for advanced routing
- **Azure Files/Disks** for persistent storage
- **Workload Identity** for secure Azure service access
- **Azure Monitor** integration for observability

### Amazon Elastic Kubernetes Service (EKS)

#### Automated Deployment

```bash
# Set required environment variables
export OPENAI_API_KEY="your-openai-api-key"
export AWS_REGION="us-west-2"
export CLUSTER_NAME="raft-toolkit-eks"
export ECR_REPOSITORY="raft-toolkit"

# Optional: AWS-specific configuration
export AWS_ROLE_ARN="arn:aws:iam::account:role/raft-toolkit-role"
export EFS_FILE_SYSTEM_ID="fs-xxxxxxxxx"

# Deploy
./k8s/scripts/deploy-eks.sh
```

#### Manual EKS Setup

```bash
# 1. Create ECR repository
aws ecr create-repository --repository-name raft-toolkit --region us-west-2

# 2. Create EKS cluster using eksctl
eksctl create cluster \
  --name raft-toolkit-eks \
  --region us-west-2 \
  --node-type m5.large \
  --nodes 3 \
  --with-oidc \
  --managed

# 3. Install AWS Load Balancer Controller
eksctl create iamserviceaccount \
  --cluster=raft-toolkit-eks \
  --namespace=kube-system \
  --name=aws-load-balancer-controller \
  --attach-policy-arn=arn:aws:iam::aws:policy/ElasticLoadBalancingFullAccess \
  --approve

helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=raft-toolkit-eks \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller

# 4. Deploy application
cd k8s/overlays/eks
kustomize build . | kubectl apply -f -
```

#### EKS Features

- **Amazon EBS CSI driver** for persistent volume storage
- **Amazon EFS** for shared file storage across pods
- **AWS Load Balancer Controller** for advanced load balancing
- **IAM Roles for Service Accounts (IRSA)** for secure AWS service access
- **AWS VPC CNI** for native VPC networking
- **CloudWatch Container Insights** for monitoring

### Google Kubernetes Engine (GKE)

#### Automated Deployment

```bash
# Set required environment variables
export OPENAI_API_KEY="your-openai-api-key"
export PROJECT_ID="your-gcp-project-id"
export GCP_REGION="us-central1"
export CLUSTER_NAME="raft-toolkit-gke"

# Optional: Use standard mode instead of autopilot
export GKE_MODE="standard"  # or "autopilot" (default)

# Deploy
./k8s/scripts/deploy-gks.sh
```

#### Manual GKE Setup

```bash
# 1. Enable required APIs
gcloud services enable container.googleapis.com compute.googleapis.com

# 2. Create GKE Autopilot cluster (recommended)
gcloud container clusters create-auto raft-toolkit-gke \
  --region=us-central1 \
  --project=your-project-id

# Or create standard cluster
gcloud container clusters create raft-toolkit-gke \
  --zone=us-central1-a \
  --machine-type=e2-standard-4 \
  --num-nodes=3 \
  --enable-autoscaling \
  --min-nodes=1 \
  --max-nodes=10

# 3. Get credentials
gcloud container clusters get-credentials raft-toolkit-gke --region=us-central1

# 4. Deploy application
cd k8s/overlays/gks
kustomize build . | kubectl apply -f -
```

#### GKE Features

- **GKE Autopilot** for fully managed node management
- **Google Container Registry/Artifact Registry** for image storage
- **Google Cloud Load Balancer** with global load balancing
- **Persistent Disk/Filestore** for storage
- **Workload Identity** for secure GCP service access
- **Google Cloud Monitoring** integration

## 🔧 Configuration

### Environment Variables

Configure the deployment using environment variables:

```bash
# Required
export OPENAI_API_KEY="your-openai-api-key"

# Optional - General Configuration
export RAFT_LOG_LEVEL="INFO"                    # DEBUG, INFO, WARNING, ERROR
export RAFT_LOG_FORMAT="json"                   # json, text, minimal
export RAFT_WORKERS="2"                         # Number of worker threads
export RAFT_QUESTIONS="5"                       # Questions per chunk
export RAFT_DISTRACTORS="1"                     # Distractor documents
export RAFT_CHUNK_SIZE="512"                    # Chunk size in tokens

# Optional - Rate Limiting
export RAFT_RATE_LIMIT_ENABLED="true"           # Enable rate limiting
export RAFT_RATE_LIMIT_STRATEGY="sliding_window" # Rate limiting strategy
export RAFT_RATE_LIMIT_PRESET="openai_gpt4"     # Preset configuration
export RAFT_RATE_LIMIT_REQUESTS_PER_MINUTE="500" # Custom request limit
export RAFT_RATE_LIMIT_TOKENS_PER_MINUTE="10000" # Custom token limit

# Optional - Azure OpenAI
export AZURE_OPENAI_ENABLED="true"              # Enable Azure OpenAI
export AZURE_OPENAI_KEY="your-azure-openai-key"
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"

# Optional - External Services
export SENTRY_DSN="your-sentry-dsn"             # Error tracking
export DATADOG_API_KEY="your-datadog-api-key"   # Monitoring

# Input Sources Configuration
export RAFT_SOURCE_TYPE="local"                 # Input source type (local, s3, sharepoint)
export RAFT_SOURCE_URI="/app/data/documents"    # Source URI or path
export RAFT_SOURCE_MAX_FILE_SIZE="52428800"     # Max file size (50MB)
export RAFT_SOURCE_BATCH_SIZE="100"             # Processing batch size

# S3 Input Source (optional)
export AWS_ACCESS_KEY_ID="your-aws-access-key"
export AWS_SECRET_ACCESS_KEY="your-aws-secret-key"
export AWS_DEFAULT_REGION="us-east-1"
export RAFT_SOURCE_URI="s3://your-bucket/documents/"

# SharePoint Input Source (optional)
export RAFT_SOURCE_CREDENTIALS='{
  "auth_method": "client_credentials",
  "client_id": "your-app-id",
  "client_secret": "your-app-secret",
  "tenant_id": "your-tenant-id"
}'
```

### Secrets Management

Create Kubernetes secrets for sensitive data:

```bash
# OpenAI API Key (required)
kubectl create secret generic raft-toolkit-secrets \
  --namespace=raft-toolkit \
  --from-literal=OPENAI_API_KEY="your-openai-api-key" \
  --from-literal=OPENAI_API_BASE_URL="https://api.openai.com/v1"

# Azure OpenAI (optional)
kubectl create secret generic raft-toolkit-secrets \
  --namespace=raft-toolkit \
  --from-literal=AZURE_OPENAI_KEY="your-azure-openai-key" \
  --from-literal=AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/" \
  --dry-run=client -o yaml | kubectl apply -f -

# External services (optional)
kubectl create secret generic raft-toolkit-secrets \
  --namespace=raft-toolkit \
  --from-literal=SENTRY_DSN="your-sentry-dsn" \
  --from-literal=DATADOG_API_KEY="your-datadog-api-key" \
  --dry-run=client -o yaml | kubectl apply -f -

# S3 input source credentials (optional)
kubectl create secret generic raft-toolkit-s3-secrets \
  --namespace=raft-toolkit \
  --from-literal=AWS_ACCESS_KEY_ID="your-aws-access-key" \
  --from-literal=AWS_SECRET_ACCESS_KEY="your-aws-secret-key" \
  --from-literal=AWS_DEFAULT_REGION="us-east-1"

# SharePoint input source credentials (optional)
kubectl create secret generic raft-toolkit-sharepoint-secrets \
  --namespace=raft-toolkit \
  --from-literal=RAFT_SOURCE_CREDENTIALS='{
    "auth_method": "client_credentials",
    "client_id": "your-app-id",
    "client_secret": "your-app-secret",
    "tenant_id": "your-tenant-id"
  }'
```

### Storage Configuration

Configure persistent storage for document input and dataset output:

```bash
# Azure (AKS) - Azure Files for shared storage
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: raft-toolkit-output-pvc
spec:
  storageClassName: azurefile-csi-premium
  accessModes: [ReadWriteMany]
  resources:
    requests:
      storage: 50Gi

# AWS (EKS) - EFS for shared storage
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: raft-toolkit-output-pvc
spec:
  storageClassName: efs-sc
  accessModes: [ReadWriteMany]
  resources:
    requests:
      storage: 50Gi

# GCP (GKE) - Filestore for shared storage
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: raft-toolkit-output-pvc
spec:
  storageClassName: filestore-csi
  accessModes: [ReadWriteMany]
  resources:
    requests:
      storage: 50Gi
```

## 🔄 Running CLI Jobs

### One-time Job

```bash
# Create a job for processing documents
kubectl apply -f - <<EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: raft-processing-job
  namespace: raft-toolkit
spec:
  template:
    spec:
      containers:
      - name: raft-toolkit
        image: your-registry/raft-toolkit:latest
        command: ["python", "cli/main.py"]
        args:
        - "--datapath"
        - "/app/input"
        - "--output"
        - "/app/output"
        - "--rate-limit"
        - "--rate-limit-preset"
        - "openai_gpt4"
        - "--questions"
        - "5"
        - "--workers"
        - "2"
        envFrom:
        - configMapRef:
            name: raft-toolkit-config
        - secretRef:
            name: raft-toolkit-secrets
        volumeMounts:
        - name: input-storage
          mountPath: /app/input
        - name: output-storage
          mountPath: /app/output
      volumes:
      - name: input-storage
        persistentVolumeClaim:
          claimName: raft-toolkit-input-pvc
      - name: output-storage
        persistentVolumeClaim:
          claimName: raft-toolkit-output-pvc
      restartPolicy: Never
  backoffLimit: 3
EOF
```

### Scheduled Jobs (CronJob)

```bash
# Create a scheduled job for regular processing
kubectl apply -f - <<EOF
apiVersion: batch/v1
kind: CronJob
metadata:
  name: raft-scheduled-processing
  namespace: raft-toolkit
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: raft-toolkit
            image: your-registry/raft-toolkit:latest
            command: ["python", "cli/main.py"]
            args:
            - "--datapath"
            - "/app/input"
            - "--output"
            - "/app/output/$(date +%Y%m%d)"
            - "--rate-limit"
            - "--rate-limit-preset"
            - "conservative"
            envFrom:
            - configMapRef:
                name: raft-toolkit-config
            - secretRef:
                name: raft-toolkit-secrets
            volumeMounts:
            - name: input-storage
              mountPath: /app/input
            - name: output-storage
              mountPath: /app/output
          volumes:
          - name: input-storage
            persistentVolumeClaim:
              claimName: raft-toolkit-input-pvc
          - name: output-storage
            persistentVolumeClaim:
              claimName: raft-toolkit-output-pvc
          restartPolicy: OnFailure
EOF
```

## 📊 Monitoring and Observability

### Health Checks

The deployment includes built-in health checks:

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

### Metrics Collection

Enable Prometheus metrics collection:

```bash
# Add Prometheus annotations to enable scraping
metadata:
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "8000"
    prometheus.io/path: "/metrics"
```

### Logging

Configure structured logging:

```bash
# Set logging configuration
export RAFT_LOG_LEVEL="INFO"
export RAFT_LOG_FORMAT="json"
export RAFT_LOG_OUTPUT="stdout"

# For external log aggregation (e.g., ELK, Splunk)
export RAFT_LOG_FORMAT="json"
```

## 🔒 Security Considerations

### Container Security

- **Non-root user**: Containers run as non-root user (UID 1000)
- **Read-only filesystem**: Root filesystem is read-only
- **Dropped capabilities**: All Linux capabilities are dropped
- **Security contexts**: Pod and container security contexts are configured

### Network Security

```yaml
# Network policy example
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: raft-toolkit-network-policy
  namespace: raft-toolkit
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: raft-toolkit
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to: []
    ports:
    - protocol: TCP
      port: 443  # HTTPS outbound
    - protocol: TCP
      port: 80   # HTTP outbound
```

### RBAC Configuration

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: raft-toolkit
  name: raft-toolkit-role
rules:
- apiGroups: [""]
  resources: ["configmaps", "secrets"]
  verbs: ["get", "list"]
- apiGroups: ["batch"]
  resources: ["jobs"]
  verbs: ["create", "get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: raft-toolkit-binding
  namespace: raft-toolkit
subjects:
- kind: ServiceAccount
  name: raft-toolkit-service-account
  namespace: raft-toolkit
roleRef:
  kind: Role
  name: raft-toolkit-role
  apiGroup: rbac.authorization.k8s.io
```

## 🚀 Scaling and Performance

### Horizontal Pod Autoscaling

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: raft-toolkit-hpa
  namespace: raft-toolkit
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: raft-toolkit-web
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Vertical Pod Autoscaling

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: raft-toolkit-vpa
  namespace: raft-toolkit
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: raft-toolkit-web
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
    - containerName: raft-toolkit-web
      maxAllowed:
        cpu: 2
        memory: 4Gi
      minAllowed:
        cpu: 100m
        memory: 128Mi
```

### Resource Optimization

```yaml
# Production resource configuration
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "1000m"

# High-performance configuration
resources:
  requests:
    memory: "2Gi"
    cpu: "1000m"
  limits:
    memory: "4Gi"
    cpu: "2000m"
```

## 🛠️ Troubleshooting

### Common Issues

#### Pod Startup Issues

```bash
# Check pod status
kubectl get pods -n raft-toolkit

# Check pod logs
kubectl logs -n raft-toolkit deployment/raft-toolkit-web

# Describe pod for events
kubectl describe pod -n raft-toolkit <pod-name>
```

#### Configuration Issues

```bash
# Check configmap
kubectl get configmap -n raft-toolkit raft-toolkit-config -o yaml

# Check secrets
kubectl get secret -n raft-toolkit raft-toolkit-secrets -o yaml

# Verify environment variables in pod
kubectl exec -n raft-toolkit <pod-name> -- env | grep RAFT
```

#### Storage Issues

```bash
# Check PVC status
kubectl get pvc -n raft-toolkit

# Check storage class
kubectl get storageclass

# Check volume mounts
kubectl describe pod -n raft-toolkit <pod-name>
```

#### Network Issues

```bash
# Check service
kubectl get service -n raft-toolkit

# Check ingress
kubectl get ingress -n raft-toolkit

# Test internal connectivity
kubectl exec -n raft-toolkit <pod-name> -- curl http://raft-toolkit-web-service/health
```

### Performance Tuning

#### Rate Limiting Optimization

```bash
# Monitor rate limiting statistics
kubectl logs -n raft-toolkit deployment/raft-toolkit-web | grep "Rate Limiting Statistics"

# Adjust rate limits based on service tier
export RAFT_RATE_LIMIT_REQUESTS_PER_MINUTE="1000"
export RAFT_RATE_LIMIT_TOKENS_PER_MINUTE="50000"
```

#### Worker Configuration

```bash
# Adjust worker count based on cluster resources
export RAFT_WORKERS="4"           # For CPU-intensive workloads
export RAFT_EMBED_WORKERS="2"     # For I/O-intensive workloads
```

## 🔄 Maintenance and Updates

### Rolling Updates

```bash
# Update image tag
kubectl set image deployment/raft-toolkit-web raft-toolkit-web=your-registry/raft-toolkit:v2.0.0 -n raft-toolkit

# Check rollout status
kubectl rollout status deployment/raft-toolkit-web -n raft-toolkit

# Rollback if needed
kubectl rollout undo deployment/raft-toolkit-web -n raft-toolkit
```

### Configuration Updates

```bash
# Update configmap
kubectl patch configmap raft-toolkit-config -n raft-toolkit --patch '{"data":{"RAFT_LOG_LEVEL":"DEBUG"}}'

# Restart deployment to pick up changes
kubectl rollout restart deployment/raft-toolkit-web -n raft-toolkit
```

### Backup and Restore

```bash
# Backup namespace resources
kubectl get all,configmap,secret,pvc -n raft-toolkit -o yaml > raft-toolkit-backup.yaml

# Backup persistent volumes
# Use cloud-specific backup tools (Azure Backup, AWS EBS Snapshots, GCP Persistent Disk Snapshots)

# Restore from backup
kubectl apply -f raft-toolkit-backup.yaml
```

## 🧹 Cleanup

### Remove Deployment

```bash
# Using kustomize
kustomize build k8s/overlays/aks | kubectl delete -f -

# Using kubectl
kubectl delete namespace raft-toolkit

# Using Helm
helm uninstall raft-toolkit -n raft-toolkit
```

### Cloud Resource Cleanup

```bash
# AKS cleanup
./k8s/scripts/deploy-aks.sh --cleanup

# EKS cleanup
./k8s/scripts/deploy-eks.sh --cleanup

# GKE cleanup
./k8s/scripts/deploy-gks.sh --cleanup
```

## 📚 Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Azure Kubernetes Service (AKS)](https://docs.microsoft.com/en-us/azure/aks/)
- [Amazon Elastic Kubernetes Service (EKS)](https://docs.aws.amazon.com/eks/)
- [Google Kubernetes Engine (GKE)](https://cloud.google.com/kubernetes-engine/docs)
- [Kustomize Documentation](https://kustomize.io/)
- [Helm Documentation](https://helm.sh/docs/)

## 🆘 Support

For additional support:

1. Check the [troubleshooting section](#-troubleshooting) above
2. Review cluster logs and events
3. Consult cloud provider documentation
4. Open an issue in the project repository

---

This guide provides comprehensive coverage of deploying RAFT Toolkit on Kubernetes. Choose the deployment method that best fits your infrastructure and operational requirements.