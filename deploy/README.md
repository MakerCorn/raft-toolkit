# RAFT Toolkit Deployment Guide

This directory contains deployment configurations for various platforms and environments.

## Platform Support

RAFT Toolkit supports deployment across multiple platforms:

- **Operating Systems**: Linux, macOS, Windows
- **Container Platforms**: Docker (Linux/Windows containers), Kubernetes
- **Cloud Providers**: AWS (EKS), Google Cloud (GKE), Azure (AKS)
- **Architectures**: amd64, arm64 (Linux only)

## Quick Start

### Docker Compose (Recommended for Development)

1. **Navigate to the docker-compose directory:**
   ```bash
   cd deploy/docker-compose
   ```

2. **Copy and configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   vim .env
   ```

3. **Start the services:**
   ```bash
   # Basic setup (web + CLI + Redis)
   docker-compose up -d

   # With Nginx reverse proxy
   COMPOSE_PROFILES=nginx docker-compose up -d

   # With Traefik reverse proxy
   COMPOSE_PROFILES=traefik docker-compose up -d

   # With monitoring (Prometheus + Grafana)
   COMPOSE_PROFILES=monitoring docker-compose up -d

   # Full setup with all services
   COMPOSE_PROFILES=nginx,monitoring docker-compose up -d
   ```

4. **Access the application:**
   - Web Interface: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Grafana (if enabled): http://localhost:3000
   - Prometheus (if enabled): http://localhost:9090

### Kubernetes Deployment

1. **Navigate to the kubernetes directory:**
   ```bash
   cd deploy/kubernetes
   ```

2. **Configure environment variables:**
   ```bash
   export NAMESPACE=raft-toolkit
   export OPENAI_API_KEY_B64=$(echo -n "your-api-key" | base64)
   export CLI_IMAGE=ghcr.io/microsoft/raft-toolkit:cli-latest
   export WEB_IMAGE=ghcr.io/microsoft/raft-toolkit:web-latest
   ```

3. **Deploy using kubectl:**
   ```bash
   # Create namespace and secrets
   envsubst < namespace.yaml | kubectl apply -f -

   # Deploy all components
   envsubst < cli-deployment.yaml | kubectl apply -f -
   envsubst < web-deployment.yaml | kubectl apply -f -
   envsubst < web-service.yaml | kubectl apply -f -
   envsubst < redis-deployment.yaml | kubectl apply -f -
   ```

4. **Or use Kustomize:**
   ```bash
   kubectl apply -k .
   ```

5. **Access the application:**
   ```bash
   # Port forward for local access
   kubectl port-forward -n raft-toolkit service/raft-web-service 8000:8000

   # Or get the LoadBalancer IP
   kubectl get service -n raft-toolkit raft-web-loadbalancer
   ```

## Directory Structure

```
deploy/
├── docker-compose/           # Docker Compose deployment
│   ├── docker-compose.yml    # Main compose file
│   ├── .env.example         # Environment variables template
│   └── nginx.conf           # Nginx configuration
├── kubernetes/              # Kubernetes manifests
│   ├── namespace.yaml       # Namespace and secrets
│   ├── cli-deployment.yaml  # CLI deployment
│   ├── web-deployment.yaml  # Web application deployment
│   ├── web-service.yaml     # Web services and ingress
│   ├── redis-deployment.yaml # Redis cache
│   └── kustomization.yaml  # Kustomize configuration
└── README.md               # This file
```

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OPENAI_API_KEY` | OpenAI API key for AI features | - | Yes |
| `REDIS_URL` | Redis connection URL | `redis://redis:6379` | No |
| `RAFT_LOG_LEVEL` | Logging level | `INFO` | No |
| `RAFT_ENVIRONMENT` | Environment name | `production` | No |
| `WEB_WORKERS` | Number of web workers | `4` | No |
| `DOMAIN_NAME` | Domain name for ingress | `localhost` | No |

### Storage Configuration

#### Docker Compose
- Data is stored in named volumes by default
- Configure `DATA_DIR`, `OUTPUT_DIR`, and `UPLOAD_DIR` in `.env` for bind mounts

#### Kubernetes
- Uses PersistentVolumeClaims for data storage
- Configure `STORAGE_CLASS` environment variable for custom storage classes

## Monitoring and Observability

### Health Checks
- Web application: `GET /health`
- Redis: `redis-cli ping`

### Metrics
- Prometheus metrics available at `/metrics` endpoint
- Grafana dashboards for visualization
- Application logs in JSON format for structured logging

### Logging
- Application logs written to stdout in JSON format
- Nginx access logs for request tracking
- Redis logs for cache operations

## Security Considerations

### Network Security
- All services run in isolated networks
- Network policies restrict inter-pod communication in Kubernetes
- Rate limiting configured in Nginx

### Container Security
- Non-root containers for all services (Linux containers)
- Read-only root filesystems where possible
- Minimal base images (Alpine Linux for Linux, Windows Server Core for Windows)
- Security contexts with dropped capabilities (Linux containers)
- Windows containers use Windows authentication and isolation

### Secrets Management
- API keys stored in Kubernetes secrets or Docker secrets
- SSL certificates managed separately
- Environment variables for sensitive configuration

## Scaling

### Horizontal Scaling
- Web application supports multiple replicas
- Redis can be configured with clustering for high availability
- Load balancing handled by ingress controllers or reverse proxies

### Vertical Scaling
- Resource requests and limits configurable
- Memory and CPU limits prevent resource exhaustion
- Persistent storage can be expanded

## Troubleshooting

### Common Issues

1. **Application won't start:**
   ```bash
   # Check logs
   docker-compose logs raft-web
   kubectl logs -n raft-toolkit deployment/raft-web
   ```

2. **Redis connection errors:**
   ```bash
   # Test Redis connectivity
   docker-compose exec raft-web ping redis
   kubectl exec -n raft-toolkit deployment/raft-web -- redis-cli -h redis ping
   ```

3. **API key issues:**
   ```bash
   # Verify API key is set
   docker-compose exec raft-web env | grep OPENAI_API_KEY
   kubectl get secret -n raft-toolkit raft-secrets -o yaml
   ```

4. **Storage issues:**
   ```bash
   # Check volume mounts
   docker-compose exec raft-web df -h
   kubectl describe pvc -n raft-toolkit
   ```

### Debug Mode

Enable debug mode by setting:
```bash
RAFT_LOG_LEVEL=DEBUG
RAFT_DEBUG=true
```

### Performance Tuning

1. **Web Workers:** Increase `WEB_WORKERS` for CPU-bound workloads
2. **Redis Memory:** Adjust Redis maxmemory settings
3. **File Upload Limits:** Configure client_max_body_size in Nginx
4. **Resource Limits:** Tune Kubernetes resource requests/limits

## Backup and Recovery

### Data Backup
```bash
# Docker Compose
docker-compose exec redis redis-cli BGSAVE
docker cp raft-redis:/data ./backup/

# Kubernetes
kubectl exec -n raft-toolkit deployment/redis -- redis-cli BGSAVE
kubectl cp raft-toolkit/redis-pod:/data ./backup/
```

### Configuration Backup
- Export Docker Compose `.env` file
- Export Kubernetes secrets and configmaps
- Backup persistent volume data

## Migration

### From Docker Compose to Kubernetes
1. Export data from Docker volumes
2. Create Kubernetes PVCs
3. Import data to Kubernetes volumes
4. Update configuration for Kubernetes environment

### Version Updates
1. Update image tags in configuration
2. Apply rolling updates
3. Monitor application health
4. Rollback if issues occur

## Support

For additional help:
- [GitHub Issues](https://github.com/microsoft/raft-toolkit/issues)
- [Documentation](https://github.com/microsoft/raft-toolkit/wiki)
- [Deployment Guide](https://github.com/microsoft/raft-toolkit/wiki/Deployment)