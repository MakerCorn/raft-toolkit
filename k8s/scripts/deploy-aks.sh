#!/bin/bash
set -euo pipefail

# RAFT Toolkit - Azure Kubernetes Service (AKS) Deployment Script
# This script deploys RAFT Toolkit to an AKS cluster

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="raft-toolkit"
RESOURCE_GROUP="${RESOURCE_GROUP:-raft-toolkit-rg}"
CLUSTER_NAME="${CLUSTER_NAME:-raft-toolkit-aks}"
LOCATION="${LOCATION:-eastus}"
ACR_NAME="${ACR_NAME:-raftoolkitacr}"

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
    if ! command -v az &> /dev/null; then
        log_error "Azure CLI is not installed. Please install it first."
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
    
    # Check if logged in to Azure
    if ! az account show &> /dev/null; then
        log_error "Not logged in to Azure. Please run 'az login' first."
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

create_resource_group() {
    log_info "Creating resource group: $RESOURCE_GROUP"
    az group create --name "$RESOURCE_GROUP" --location "$LOCATION" || true
    log_success "Resource group ready"
}

create_acr() {
    log_info "Creating Azure Container Registry: $ACR_NAME"
    az acr create --resource-group "$RESOURCE_GROUP" --name "$ACR_NAME" --sku Basic || true
    
    # Get ACR login server
    ACR_LOGIN_SERVER=$(az acr show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" --query "loginServer" --output tsv)
    log_success "ACR ready: $ACR_LOGIN_SERVER"
}

create_aks_cluster() {
    log_info "Creating AKS cluster: $CLUSTER_NAME"
    
    # Create AKS cluster with Azure CNI and managed identity
    az aks create \
        --resource-group "$RESOURCE_GROUP" \
        --name "$CLUSTER_NAME" \
        --node-count 3 \
        --enable-addons monitoring \
        --generate-ssh-keys \
        --network-plugin azure \
        --enable-managed-identity \
        --attach-acr "$ACR_NAME" \
        --node-vm-size Standard_D2s_v3 \
        --zones 1 2 3 || true
    
    log_success "AKS cluster ready"
}

configure_kubectl() {
    log_info "Configuring kubectl..."
    az aks get-credentials --resource-group "$RESOURCE_GROUP" --name "$CLUSTER_NAME" --overwrite-existing
    log_success "kubectl configured"
}

build_and_push_image() {
    log_info "Building and pushing Docker image..."
    
    # Build the image
    docker build -t raft-toolkit:latest .
    
    # Tag for ACR
    docker tag raft-toolkit:latest "$ACR_LOGIN_SERVER/raft-toolkit:latest"
    
    # Login to ACR and push
    az acr login --name "$ACR_NAME"
    docker push "$ACR_LOGIN_SERVER/raft-toolkit:latest"
    
    log_success "Image pushed to ACR"
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
    
    # Add Azure-specific secrets if provided
    if [ ! -z "${AZURE_CLIENT_ID:-}" ]; then
        kubectl create secret generic azure-identity-secret \
            --namespace="$NAMESPACE" \
            --from-literal=client-id="$AZURE_CLIENT_ID" \
            --from-literal=tenant-id="${AZURE_TENANT_ID:-}" \
            --from-literal=subscription-id="${AZURE_SUBSCRIPTION_ID:-}" \
            --dry-run=client -o yaml | kubectl apply -f -
    fi
    
    log_success "Secrets configured"
}

deploy_application() {
    log_info "Deploying RAFT Toolkit..."
    
    # Update kustomization with correct image
    cd k8s/overlays/aks
    kustomize edit set image raft-toolkit="$ACR_LOGIN_SERVER/raft-toolkit:latest"
    
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
    
    # Wait for external IP
    log_info "Waiting for external IP (this may take a few minutes)..."
    kubectl get service raft-toolkit-web-service -n "$NAMESPACE" --watch &
    WATCH_PID=$!
    
    # Wait up to 10 minutes for external IP
    for i in {1..60}; do
        EXTERNAL_IP=$(kubectl get service raft-toolkit-web-service -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
        if [ ! -z "$EXTERNAL_IP" ] && [ "$EXTERNAL_IP" != "null" ]; then
            kill $WATCH_PID 2>/dev/null || true
            break
        fi
        sleep 10
    done
    
    if [ -z "$EXTERNAL_IP" ] || [ "$EXTERNAL_IP" == "null" ]; then
        log_warning "External IP not yet assigned. Check status with: kubectl get service raft-toolkit-web-service -n $NAMESPACE"
    else
        log_success "RAFT Toolkit is accessible at: http://$EXTERNAL_IP"
    fi
}

show_status() {
    log_info "Deployment Status:"
    echo "Namespace: $NAMESPACE"
    echo "Cluster: $CLUSTER_NAME"
    echo "Resource Group: $RESOURCE_GROUP"
    echo ""
    
    kubectl get pods -n "$NAMESPACE"
    echo ""
    kubectl get services -n "$NAMESPACE"
}

cleanup() {
    if [ "${1:-}" == "--cleanup" ]; then
        log_warning "Cleaning up resources..."
        az group delete --name "$RESOURCE_GROUP" --yes --no-wait
        log_success "Cleanup initiated"
        exit 0
    fi
}

# Main execution
main() {
    log_info "Starting AKS deployment for RAFT Toolkit"
    
    # Handle cleanup
    cleanup "$@"
    
    # Run deployment steps
    check_prerequisites
    create_resource_group
    create_acr
    create_aks_cluster
    configure_kubectl
    build_and_push_image
    setup_secrets
    deploy_application
    wait_for_deployment
    get_service_info
    show_status
    
    log_success "AKS deployment completed successfully!"
    echo ""
    log_info "Next steps:"
    echo "1. Configure DNS to point to the external IP"
    echo "2. Set up SSL certificates"
    echo "3. Configure monitoring and alerting"
    echo "4. Review security settings"
}

# Help function
show_help() {
    echo "Usage: $0 [--cleanup]"
    echo ""
    echo "Deploy RAFT Toolkit to Azure Kubernetes Service (AKS)"
    echo ""
    echo "Environment Variables:"
    echo "  OPENAI_API_KEY      Required: OpenAI API key"
    echo "  RESOURCE_GROUP      Optional: Azure resource group name (default: raft-toolkit-rg)"
    echo "  CLUSTER_NAME        Optional: AKS cluster name (default: raft-toolkit-aks)"
    echo "  LOCATION            Optional: Azure location (default: eastus)"
    echo "  ACR_NAME            Optional: Azure Container Registry name (default: raftoolkitacr)"
    echo "  AZURE_CLIENT_ID     Optional: Azure client ID for managed identity"
    echo "  AZURE_TENANT_ID     Optional: Azure tenant ID"
    echo "  AZURE_SUBSCRIPTION_ID Optional: Azure subscription ID"
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