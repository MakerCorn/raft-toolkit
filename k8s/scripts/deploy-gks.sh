#!/bin/bash
set -euo pipefail

# RAFT Toolkit - Google Kubernetes Engine (GKE) Deployment Script
# This script deploys RAFT Toolkit to a GKE cluster

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="raft-toolkit"
PROJECT_ID="${PROJECT_ID:-}"
CLUSTER_NAME="${CLUSTER_NAME:-raft-toolkit-gke}"
REGION="${GCP_REGION:-us-central1}"
ZONE="${GCP_ZONE:-us-central1-a}"
MACHINE_TYPE="${MACHINE_TYPE:-e2-standard-4}"
NUM_NODES="${NUM_NODES:-3}"

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
    if ! command -v gcloud &> /dev/null; then
        log_error "Google Cloud SDK is not installed. Please install it first."
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
    
    # Check if logged in to GCP
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n1 &> /dev/null; then
        log_error "Not logged in to Google Cloud. Please run 'gcloud auth login' first."
        exit 1
    fi
    
    # Get or set project ID
    if [ -z "$PROJECT_ID" ]; then
        PROJECT_ID=$(gcloud config get-value project 2>/dev/null || echo "")
        if [ -z "$PROJECT_ID" ]; then
            log_error "PROJECT_ID not set and no default project configured. Please set PROJECT_ID environment variable or run 'gcloud config set project PROJECT_ID'"
            exit 1
        fi
    fi
    
    log_success "Prerequisites check passed (Project: $PROJECT_ID)"
}

enable_apis() {
    log_info "Enabling required Google Cloud APIs..."
    
    gcloud services enable container.googleapis.com \
        compute.googleapis.com \
        containerregistry.googleapis.com \
        cloudbuild.googleapis.com \
        --project="$PROJECT_ID"
    
    log_success "Required APIs enabled"
}

create_gke_cluster() {
    log_info "Creating GKE cluster: $CLUSTER_NAME"
    
    # Create GKE cluster with Autopilot (recommended) or Standard mode
    if [ "${GKE_MODE:-autopilot}" == "autopilot" ]; then
        gcloud container clusters create-auto "$CLUSTER_NAME" \
            --region="$REGION" \
            --project="$PROJECT_ID" \
            --enable-autorepair \
            --enable-autoupgrade \
            --enable-autoscaling || true
    else
        gcloud container clusters create "$CLUSTER_NAME" \
            --zone="$ZONE" \
            --project="$PROJECT_ID" \
            --machine-type="$MACHINE_TYPE" \
            --num-nodes="$NUM_NODES" \
            --enable-autorepair \
            --enable-autoupgrade \
            --enable-autoscaling \
            --min-nodes=1 \
            --max-nodes=10 \
            --disk-size=20GB \
            --disk-type=pd-ssd \
            --enable-network-policy \
            --addons=HorizontalPodAutoscaling,HttpLoadBalancing,NetworkPolicy \
            --workload-pool="$PROJECT_ID.svc.id.goog" || true
    fi
    
    log_success "GKE cluster ready"
}

configure_kubectl() {
    log_info "Configuring kubectl..."
    
    if [ "${GKE_MODE:-autopilot}" == "autopilot" ]; then
        gcloud container clusters get-credentials "$CLUSTER_NAME" --region="$REGION" --project="$PROJECT_ID"
    else
        gcloud container clusters get-credentials "$CLUSTER_NAME" --zone="$ZONE" --project="$PROJECT_ID"
    fi
    
    log_success "kubectl configured"
}

build_and_push_image() {
    log_info "Building and pushing Docker image..."
    
    # Configure Docker to use gcloud as a credential helper
    gcloud auth configure-docker
    
    # Build the image
    docker build -t raft-toolkit:latest .
    
    # Tag for Google Container Registry
    docker tag raft-toolkit:latest "gcr.io/$PROJECT_ID/raft-toolkit:latest"
    
    # Push to GCR
    docker push "gcr.io/$PROJECT_ID/raft-toolkit:latest"
    
    log_success "Image pushed to GCR"
}

create_service_account() {
    log_info "Creating Google Cloud service account..."
    
    # Create service account
    gcloud iam service-accounts create raft-toolkit \
        --display-name="RAFT Toolkit Service Account" \
        --project="$PROJECT_ID" || true
    
    # Grant necessary permissions
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:raft-toolkit@$PROJECT_ID.iam.gserviceaccount.com" \
        --role="roles/storage.objectViewer" || true
    
    # Enable Workload Identity
    gcloud iam service-accounts add-iam-policy-binding \
        --role roles/iam.workloadIdentityUser \
        --member "serviceAccount:$PROJECT_ID.svc.id.goog[$NAMESPACE/raft-toolkit-gcp-service-account]" \
        "raft-toolkit@$PROJECT_ID.iam.gserviceaccount.com" \
        --project="$PROJECT_ID" || true
    
    log_success "Service account configured"
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
    
    # Create service account key if needed (not recommended for production)
    if [ "${CREATE_SA_KEY:-false}" == "true" ]; then
        gcloud iam service-accounts keys create key.json \
            --iam-account="raft-toolkit@$PROJECT_ID.iam.gserviceaccount.com" \
            --project="$PROJECT_ID"
        
        kubectl create secret generic gcp-service-account-key \
            --namespace="$NAMESPACE" \
            --from-file=key.json=key.json \
            --dry-run=client -o yaml | kubectl apply -f -
        
        rm key.json
    fi
    
    log_success "Secrets configured"
}

deploy_application() {
    log_info "Deploying RAFT Toolkit..."
    
    # Update kustomization with correct image and project ID
    cd k8s/overlays/gks
    kustomize edit set image raft-toolkit="gcr.io/$PROJECT_ID/raft-toolkit:latest"
    
    # Update project ID in configuration files
    sed -i "s/your-project-id/$PROJECT_ID/g" *.yaml || true
    
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
    
    # Wait up to 10 minutes for external IP
    for i in {1..60}; do
        EXTERNAL_IP=$(kubectl get service raft-toolkit-web-service -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
        if [ ! -z "$EXTERNAL_IP" ] && [ "$EXTERNAL_IP" != "null" ]; then
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
    echo "Project: $PROJECT_ID"
    echo "Region: $REGION"
    echo ""
    
    kubectl get pods -n "$NAMESPACE"
    echo ""
    kubectl get services -n "$NAMESPACE"
}

cleanup() {
    if [ "${1:-}" == "--cleanup" ]; then
        log_warning "Cleaning up resources..."
        
        # Delete cluster
        if [ "${GKE_MODE:-autopilot}" == "autopilot" ]; then
            gcloud container clusters delete "$CLUSTER_NAME" --region="$REGION" --project="$PROJECT_ID" --quiet
        else
            gcloud container clusters delete "$CLUSTER_NAME" --zone="$ZONE" --project="$PROJECT_ID" --quiet
        fi
        
        # Delete service account
        gcloud iam service-accounts delete "raft-toolkit@$PROJECT_ID.iam.gserviceaccount.com" --project="$PROJECT_ID" --quiet || true
        
        # Delete container images
        gcloud container images delete "gcr.io/$PROJECT_ID/raft-toolkit:latest" --project="$PROJECT_ID" --quiet || true
        
        log_success "Cleanup completed"
        exit 0
    fi
}

# Main execution
main() {
    log_info "Starting GKE deployment for RAFT Toolkit"
    
    # Handle cleanup
    cleanup "$@"
    
    # Run deployment steps
    check_prerequisites
    enable_apis
    create_gke_cluster
    configure_kubectl
    build_and_push_image
    create_service_account
    setup_secrets
    deploy_application
    wait_for_deployment
    get_service_info
    show_status
    
    log_success "GKE deployment completed successfully!"
    echo ""
    log_info "Next steps:"
    echo "1. Configure DNS to point to the external IP"
    echo "2. Set up SSL certificates with Google-managed certificates"
    echo "3. Configure monitoring with Google Cloud Monitoring"
    echo "4. Review security settings and IAM policies"
}

# Help function
show_help() {
    echo "Usage: $0 [--cleanup]"
    echo ""
    echo "Deploy RAFT Toolkit to Google Kubernetes Engine (GKE)"
    echo ""
    echo "Environment Variables:"
    echo "  OPENAI_API_KEY      Required: OpenAI API key"
    echo "  PROJECT_ID          Optional: GCP project ID (uses gcloud default if not set)"
    echo "  GCP_REGION          Optional: GCP region (default: us-central1)"
    echo "  GCP_ZONE            Optional: GCP zone for standard clusters (default: us-central1-a)"
    echo "  CLUSTER_NAME        Optional: GKE cluster name (default: raft-toolkit-gke)"
    echo "  MACHINE_TYPE        Optional: Node machine type for standard clusters (default: e2-standard-4)"
    echo "  NUM_NODES           Optional: Number of nodes for standard clusters (default: 3)"
    echo "  GKE_MODE            Optional: 'autopilot' or 'standard' (default: autopilot)"
    echo "  CREATE_SA_KEY       Optional: Create service account key (default: false, not recommended)"
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