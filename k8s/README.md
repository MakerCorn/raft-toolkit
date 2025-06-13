# RAFT Toolkit - Kubernetes Deployment

This directory contains comprehensive Kubernetes deployment configurations for RAFT Toolkit across major cloud providers.

## 📁 Directory Structure

```
k8s/
├── base/                           # Base Kubernetes manifests
│   ├── namespace.yaml             # Namespace definition
│   ├── configmap.yaml             # Configuration management
│   ├── secret.yaml                # Secrets template
│   ├── deployment.yaml            # Web application deployment
│   ├── service.yaml               # Service definition
│   ├── job.yaml                   # CLI job template
│   ├── pvc.yaml                   # Persistent volume claims
│   ├── ingress.yaml               # Ingress configuration
│   └── kustomization.yaml         # Base kustomization
├── overlays/                      # Cloud-specific overlays
│   ├── aks/                       # Azure Kubernetes Service
│   │   ├── kustomization.yaml     # AKS-specific kustomization
│   │   ├── deployment-patch.yaml  # AKS deployment patches
│   │   ├── service-patch.yaml     # AKS service configuration
│   │   ├── ingress-patch.yaml     # Application Gateway Ingress
│   │   ├── pvc-patch.yaml         # Azure storage classes
│   │   └── azure-identity.yaml    # Workload Identity setup
│   ├── eks/                       # Amazon Elastic Kubernetes Service
│   │   ├── kustomization.yaml     # EKS-specific kustomization
│   │   ├── deployment-patch.yaml  # EKS deployment patches
│   │   ├── service-patch.yaml     # ALB service configuration
│   │   ├── ingress-patch.yaml     # ALB Ingress Controller
│   │   ├── pvc-patch.yaml         # EBS/EFS storage classes
│   │   ├── aws-iam-service-account.yaml # IAM roles for service accounts
│   │   └── aws-load-balancer-controller.yaml # Storage classes
│   └── gks/                       # Google Kubernetes Engine
│       ├── kustomization.yaml     # GKE-specific kustomization
│       ├── deployment-patch.yaml  # GKE deployment patches
│       ├── service-patch.yaml     # GCP Load Balancer configuration
│       ├── ingress-patch.yaml     # GCP Ingress Controller
│       ├── pvc-patch.yaml         # GCP storage classes
│       ├── gcp-service-account.yaml # Workload Identity setup
│       └── gcp-storage-classes.yaml # Persistent Disk/Filestore
├── helm/                          # Helm chart
│   ├── Chart.yaml                 # Helm chart metadata
│   ├── values.yaml                # Default values
│   └── templates/                 # Helm templates
│       ├── deployment.yaml        # Templated deployment
│       └── _helpers.tpl           # Template helpers
└── scripts/                       # Deployment automation
    ├── deploy-aks.sh              # AKS deployment script
    ├── deploy-eks.sh              # EKS deployment script
    └── deploy-gks.sh              # GKE deployment script
```

## 🚀 Quick Start

### Option 1: Automated Deployment (Recommended)

Choose your cloud provider and run the corresponding script:

```bash
# Azure Kubernetes Service (AKS)
export OPENAI_API_KEY="your-openai-api-key"
./scripts/deploy-aks.sh

# Amazon Elastic Kubernetes Service (EKS)
export OPENAI_API_KEY="your-openai-api-key"
./scripts/deploy-eks.sh

# Google Kubernetes Engine (GKE)
export OPENAI_API_KEY="your-openai-api-key"
export PROJECT_ID="your-gcp-project-id"
./scripts/deploy-gks.sh
```

### Option 2: Manual Deployment with Kustomize

```bash
# 1. Build and push your image
docker build -t raft-toolkit:latest ../
docker tag raft-toolkit:latest your-registry/raft-toolkit:latest
docker push your-registry/raft-toolkit:latest

# 2. Create secrets
kubectl create namespace raft-toolkit
kubectl create secret generic raft-toolkit-secrets \
  --namespace=raft-toolkit \
  --from-literal=OPENAI_API_KEY="your-openai-api-key"

# 3. Deploy to your preferred cloud
cd overlays/aks  # or eks/gks
kustomize edit set image raft-toolkit=your-registry/raft-toolkit:latest
kustomize build . | kubectl apply -f -
```

### Option 3: Helm Deployment

```bash
helm install raft-toolkit ./helm \
  --namespace raft-toolkit \
  --create-namespace \
  --set secrets.openaiApiKey="your-openai-api-key" \
  --set image.repository="your-registry/raft-toolkit"
```

## ☁️ Cloud Provider Features

### Azure Kubernetes Service (AKS)
- **Azure Container Registry** integration
- **Application Gateway Ingress Controller**
- **Azure Files/Disks** for persistent storage
- **Workload Identity** for secure Azure service access
- **Azure Monitor** integration

### Amazon Elastic Kubernetes Service (EKS)
- **Amazon ECR** integration
- **AWS Load Balancer Controller**
- **EBS/EFS** for persistent storage
- **IAM Roles for Service Accounts (IRSA)**
- **CloudWatch Container Insights**

### Google Kubernetes Engine (GKE)
- **Google Container Registry** integration
- **GCP Load Balancer** with global load balancing
- **Persistent Disk/Filestore** for storage
- **Workload Identity** for secure GCP service access
- **Google Cloud Monitoring**

## 🔧 Configuration

### Environment Variables

Required:
```bash
export OPENAI_API_KEY="your-openai-api-key"
```

Optional configuration:
```bash
# Performance tuning
export RAFT_WORKERS="2"
export RAFT_QUESTIONS="5"
export RAFT_DISTRACTORS="1"

# Rate limiting
export RAFT_RATE_LIMIT_ENABLED="true"
export RAFT_RATE_LIMIT_PRESET="openai_gpt4"

# Logging
export RAFT_LOG_LEVEL="INFO"
export RAFT_LOG_FORMAT="json"
```

### Cloud-Specific Variables

#### Azure (AKS)
```bash
export RESOURCE_GROUP="raft-toolkit-rg"
export CLUSTER_NAME="raft-toolkit-aks"
export LOCATION="eastus"
export ACR_NAME="raftoolkitacr"
```

#### AWS (EKS)
```bash
export AWS_REGION="us-west-2"
export CLUSTER_NAME="raft-toolkit-eks"
export ECR_REPOSITORY="raft-toolkit"
```

#### Google Cloud (GKE)
```bash
export PROJECT_ID="your-gcp-project-id"
export GCP_REGION="us-central1"
export CLUSTER_NAME="raft-toolkit-gke"
```

## 🏃‍♂️ Running CLI Jobs

### One-time Processing Job

```bash
kubectl apply -f - <<EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: raft-processing-$(date +%s)
  namespace: raft-toolkit
spec:
  template:
    spec:
      containers:
      - name: raft-toolkit
        image: your-registry/raft-toolkit:latest
        command: ["python", "cli/main.py"]
        args:
        - "--datapath=/app/input"
        - "--output=/app/output"
        - "--rate-limit"
        - "--rate-limit-preset=openai_gpt4"
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
EOF
```

### Scheduled Processing (CronJob)

```bash
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
            - "--datapath=/app/input"
            - "--output=/app/output/\$(date +%Y%m%d)"
            - "--rate-limit"
            - "--rate-limit-preset=conservative"
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

## 📊 Monitoring

### Check Deployment Status

```bash
# Check all resources
kubectl get all -n raft-toolkit

# Check pods
kubectl get pods -n raft-toolkit

# Check services
kubectl get services -n raft-toolkit

# Check ingress
kubectl get ingress -n raft-toolkit
```

### View Logs

```bash
# Web application logs
kubectl logs -n raft-toolkit deployment/raft-toolkit-web -f

# Job logs
kubectl logs -n raft-toolkit job/raft-processing-job-name

# Get logs from all pods
kubectl logs -n raft-toolkit -l app.kubernetes.io/name=raft-toolkit
```

### Access Application

```bash
# Port forward for local access
kubectl port-forward -n raft-toolkit service/raft-toolkit-web-service 8080:80

# Get external IP/hostname
kubectl get service -n raft-toolkit raft-toolkit-web-service
kubectl get ingress -n raft-toolkit raft-toolkit-ingress
```

## 🔒 Security Best Practices

1. **Use specific image tags** instead of `latest` in production
2. **Rotate secrets regularly** using Kubernetes secret management
3. **Enable network policies** to restrict pod-to-pod communication
4. **Use RBAC** to limit service account permissions
5. **Enable pod security standards** for additional security
6. **Regularly update** base images and dependencies
7. **Use cloud-native secret management** (Azure Key Vault, AWS Secrets Manager, etc.)

## 🚀 Scaling

### Horizontal Pod Autoscaler

```bash
kubectl apply -f - <<EOF
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
EOF
```

## 🧹 Cleanup

### Remove Application

```bash
# Using kustomize
kustomize build overlays/aks | kubectl delete -f -  # or eks/gks

# Using kubectl
kubectl delete namespace raft-toolkit

# Using Helm
helm uninstall raft-toolkit -n raft-toolkit
```

### Cloud Infrastructure Cleanup

```bash
# Use the automated cleanup scripts
./scripts/deploy-aks.sh --cleanup
./scripts/deploy-eks.sh --cleanup
./scripts/deploy-gks.sh --cleanup
```

## 📚 Additional Resources

- [Complete Kubernetes Deployment Guide](../docs/KUBERNETES.md)
- [RAFT Toolkit Documentation](../README.md)
- [Configuration Reference](../docs/CONFIGURATION.md)
- [Troubleshooting Guide](../docs/TROUBLESHOOTING.md)

## 🆘 Troubleshooting

Common issues and solutions:

1. **Image pull errors**: Ensure image registry authentication is configured
2. **Pod startup failures**: Check logs with `kubectl logs` and `kubectl describe pod`
3. **Storage issues**: Verify storage classes and PVC status
4. **Network connectivity**: Check service discovery and ingress configuration
5. **Resource constraints**: Monitor CPU/memory usage and adjust resource limits

For detailed troubleshooting, see the [Kubernetes Deployment Guide](../docs/KUBERNETES.md#-troubleshooting).