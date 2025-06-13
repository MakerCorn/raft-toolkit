#!/bin/bash
set -euo pipefail

# RAFT Toolkit - Amazon Elastic Kubernetes Service (EKS) Deployment Script
# This script deploys RAFT Toolkit to an EKS cluster

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="raft-toolkit"
CLUSTER_NAME="${CLUSTER_NAME:-raft-toolkit-eks}"
REGION="${AWS_REGION:-us-west-2}"
NODE_GROUP_NAME="${NODE_GROUP_NAME:-raft-toolkit-nodes}"
ECR_REPOSITORY="${ECR_REPOSITORY:-raft-toolkit}"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if required tools are installed
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    
    if ! command -v eksctl &> /dev/null; then
        log_error "eksctl is not installed. Please install it first."
        exit 1
    fi
    
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed. Please install it first."
        exit 1
    fi
    
    if ! command -v kustomize &> /dev/null; then
        log_error "kustomize is not installed. Please install it first."
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured. Please run 'aws configure' first."
        exit 1
    fi
    
    # Get AWS account ID
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    
    log_success "Prerequisites check passed (Account: $AWS_ACCOUNT_ID)"
}

create_ecr_repository() {
    log_info "Creating ECR repository: $ECR_REPOSITORY"
    
    aws ecr create-repository --repository-name "$ECR_REPOSITORY" --region "$REGION" || true
    
    # Get ECR URI
    ECR_URI=$(aws ecr describe-repositories --repository-names "$ECR_REPOSITORY" --region "$REGION" --query 'repositories[0].repositoryUri' --output text)
    log_success "ECR repository ready: $ECR_URI"
}

create_eks_cluster() {
    log_info "Creating EKS cluster: $CLUSTER_NAME"
    
    # Create cluster configuration
    cat > eks-cluster-config.yaml << EOF
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig

metadata:
  name: $CLUSTER_NAME
  region: $REGION
  version: "1.28"

managedNodeGroups:
  - name: $NODE_GROUP_NAME
    instanceType: m5.large
    desiredCapacity: 3
    minSize: 1
    maxSize: 5
    availabilityZones: ["${REGION}a", "${REGION}b", "${REGION}c"]
    volumeSize: 20
    volumeType: gp3
    ssh:
      allow: false
    iam:
      withAddonPolicies:
        autoScaler: true
        awsLoadBalancerController: true
        ebs: true
        efs: true

addons:
  - name: vpc-cni
  - name: coredns
  - name: kube-proxy
  - name: aws-ebs-csi-driver

iam:
  withOIDC: true
  serviceAccounts:
    - metadata:
        name: raft-toolkit-aws-service-account
        namespace: $NAMESPACE
      wellKnownPolicies:
        ebsCSIController: true
EOF

    # Create the cluster
    eksctl create cluster -f eks-cluster-config.yaml
    
    # Clean up config file
    rm eks-cluster-config.yaml
    
    log_success "EKS cluster ready"
}

install_aws_load_balancer_controller() {
    log_info "Installing AWS Load Balancer Controller..."
    
    # Create IAM service account
    eksctl create iamserviceaccount \
        --cluster="$CLUSTER_NAME" \
        --namespace=kube-system \
        --name=aws-load-balancer-controller \
        --role-name "AmazonEKSLoadBalancerControllerRole" \
        --attach-policy-arn=arn:aws:iam::aws:policy/ElasticLoadBalancingFullAccess \
        --approve \
        --override-existing-serviceaccounts || true
    
    # Install the controller using Helm
    helm repo add eks https://aws.github.io/eks-charts || true
    helm repo update
    
    helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
        -n kube-system \
        --set clusterName="$CLUSTER_NAME" \
        --set serviceAccount.create=false \
        --set serviceAccount.name=aws-load-balancer-controller || true
    
    log_success "AWS Load Balancer Controller installed"
}

configure_kubectl() {
    log_info "Configuring kubectl..."
    aws eks update-kubeconfig --region "$REGION" --name "$CLUSTER_NAME"
    log_success "kubectl configured"
}

build_and_push_image() {
    log_info "Building and pushing Docker image..."
    
    # Get ECR login token
    aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"
    
    # Build the image
    docker build -t raft-toolkit:latest .
    
    # Tag for ECR
    docker tag raft-toolkit:latest "$ECR_URI:latest"
    
    # Push to ECR
    docker push "$ECR_URI:latest"
    
    log_success "Image pushed to ECR"
}

setup_secrets() {
    log_info "Setting up secrets..."
    
    # Check if OpenAI API key is provided
    if [ -z "${OPENAI_API_KEY:-}" ]; then
        log_error "OPENAI_API_KEY environment variable is required"
        exit 1
    fi
    
    # Create namespace
    kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
    
    # Create secrets
    kubectl create secret generic raft-toolkit-secrets \
        --namespace="$NAMESPACE" \
        --from-literal=OPENAI_API_KEY="$OPENAI_API_KEY" \
        --from-literal=OPENAI_API_BASE_URL="https://api.openai.com/v1" \
        --dry-run=client -o yaml | kubectl apply -f -
    
    # Add AWS-specific secrets if provided
    if [ ! -z "${AWS_ROLE_ARN:-}" ]; then
        kubectl create secret generic aws-credentials-secret \
            --namespace="$NAMESPACE" \
            --from-literal=role-arn="$AWS_ROLE_ARN" \
            --dry-run=client -o yaml | kubectl apply -f -
    fi
    
    log_success "Secrets configured"
}

deploy_application() {
    log_info "Deploying RAFT Toolkit..."
    
    # Update kustomization with correct image
    cd k8s/overlays/eks
    kustomize edit set image raft-toolkit="$ECR_URI:latest"
    
    # Update EFS file system ID if provided
    if [ ! -z "${EFS_FILE_SYSTEM_ID:-}" ]; then
        sed -i "s/\${EFS_FILE_SYSTEM_ID}/$EFS_FILE_SYSTEM_ID/g" aws-load-balancer-controller.yaml
    fi
    
    # Apply the configuration
    kustomize build . | kubectl apply -f -
    
    cd ../../..
    log_success "Application deployed"
}

wait_for_deployment() {
    log_info "Waiting for deployment to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/raft-toolkit-web -n "$NAMESPACE"
    log_success "Deployment is ready"
}

get_service_info() {
    log_info "Getting service information..."
    
    # Wait for external hostname
    log_info "Waiting for load balancer hostname (this may take a few minutes)..."
    
    # Wait up to 10 minutes for external hostname
    for i in {1..60}; do
        EXTERNAL_HOSTNAME=$(kubectl get service raft-toolkit-web-service -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "")
        if [ ! -z "$EXTERNAL_HOSTNAME" ] && [ "$EXTERNAL_HOSTNAME" != "null" ]; then
            break
        fi
        sleep 10
    done
    
    if [ -z "$EXTERNAL_HOSTNAME" ] || [ "$EXTERNAL_HOSTNAME" == "null" ]; then
        log_warning "External hostname not yet assigned. Check status with: kubectl get service raft-toolkit-web-service -n $NAMESPACE"
    else
        log_success "RAFT Toolkit is accessible at: http://$EXTERNAL_HOSTNAME"
    fi
}

show_status() {
    log_info "Deployment Status:"
    echo "Namespace: $NAMESPACE"
    echo "Cluster: $CLUSTER_NAME"
    echo "Region: $REGION"
    echo ""
    
    kubectl get pods -n "$NAMESPACE"
    echo ""
    kubectl get services -n "$NAMESPACE"
}

cleanup() {
    if [ "${1:-}" == "--cleanup" ]; then
        log_warning "Cleaning up resources..."
        eksctl delete cluster --name "$CLUSTER_NAME" --region "$REGION"
        aws ecr delete-repository --repository-name "$ECR_REPOSITORY" --region "$REGION" --force || true
        log_success "Cleanup completed"
        exit 0
    fi
}

# Main execution
main() {
    log_info "Starting EKS deployment for RAFT Toolkit"
    
    # Handle cleanup
    cleanup "$@"
    
    # Run deployment steps
    check_prerequisites
    create_ecr_repository
    create_eks_cluster
    install_aws_load_balancer_controller
    configure_kubectl
    build_and_push_image
    setup_secrets
    deploy_application
    wait_for_deployment
    get_service_info
    show_status
    
    log_success "EKS deployment completed successfully!"
    echo ""
    log_info "Next steps:"
    echo "1. Configure DNS to point to the load balancer hostname"
    echo "2. Set up SSL certificates with ACM"
    echo "3. Configure monitoring with CloudWatch"
    echo "4. Review security settings and IAM policies"
}

# Help function
show_help() {
    echo "Usage: $0 [--cleanup]"
    echo ""
    echo "Deploy RAFT Toolkit to Amazon Elastic Kubernetes Service (EKS)"
    echo ""
    echo "Environment Variables:"
    echo "  OPENAI_API_KEY      Required: OpenAI API key"
    echo "  AWS_REGION          Optional: AWS region (default: us-west-2)"
    echo "  CLUSTER_NAME        Optional: EKS cluster name (default: raft-toolkit-eks)"
    echo "  NODE_GROUP_NAME     Optional: Node group name (default: raft-toolkit-nodes)"
    echo "  ECR_REPOSITORY      Optional: ECR repository name (default: raft-toolkit)"
    echo "  AWS_ROLE_ARN        Optional: IAM role ARN for service account"
    echo "  EFS_FILE_SYSTEM_ID  Optional: EFS file system ID for shared storage"
    echo ""
    echo "Options:"
    echo "  --cleanup           Delete all created resources"
    echo "  --help              Show this help message"
}

# Check for help flag
if [ "${1:-}" == "--help" ]; then
    show_help
    exit 0
fi

# Run main function
main "$@"