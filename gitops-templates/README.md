# GitOps Kubernetes Templates for Frontend

These templates need to be copied to your `arigsela/kubernetes` repository to deploy the frontend.

## Directory Structure

Copy the `base-apps/chores-tracker-frontend/` directory to your GitOps repository:

```
arigsela/kubernetes/
├── base-apps/
│   ├── chores-tracker/           # Existing backend
│   │   └── deployments.yaml
│   └── chores-tracker-frontend/  # New frontend (copy this)
│       ├── deployments.yaml
│       ├── service.yaml
│       └── ingress.yaml
```

## Files Explained

### deployments.yaml
- **2 replicas** for high availability
- **Security**: Non-root user, read-only filesystem, no privilege escalation
- **Health checks**: Liveness and readiness probes on `/health` endpoint
- **Resources**: 128Mi-256Mi memory, 100m-200m CPU
- **Environment**: Production settings with API_URL pointing to backend service
- **Volumes**: Temporary directories for nginx cache and runtime files

### service.yaml
- **ClusterIP service** exposing port 80
- **Internal access**: Routes traffic from ingress to frontend pods on port 3000
- **Load balancing**: Distributes traffic across frontend replicas

### ingress.yaml
- **TLS/SSL**: HTTPS with certificate (replace domain with yours)
- **SPA routing**: Handles client-side routing by falling back to index.html
- **Static caching**: Long-term caching for JS/CSS/image assets
- **Security headers**: X-Frame-Options, XSS protection, etc.

## Required Changes

### 1. Update Domain
Replace `chores-frontend.your-domain.com` in `ingress.yaml` with your actual domain.

### 2. Update ECR Repository
Verify the image URL in `deployments.yaml` matches your ECR repository:
```yaml
image: 852893458518.dkr.ecr.us-east-2.amazonaws.com/chores-tracker-frontend:latest
```

### 3. Update API URL
The frontend is configured to connect to the backend service:
```yaml
- name: API_URL
  value: "http://chores-tracker-service:8000/api/v1"
```

Adjust this if your backend service has a different name.

## Deployment Steps

1. **Copy files** to your GitOps repository
2. **Update domain** and other environment-specific values
3. **Commit and push** to trigger ArgoCD sync
4. **Run frontend release workflow** to build and deploy new versions

## Key Features

- **Production ready** with security best practices
- **Scalable** with 2 replicas and proper resource limits
- **Observable** with health checks and proper labeling
- **Secure** with non-root execution and security headers
- **Optimized** with static asset caching and compression (handled by nginx in container)

The CI/CD workflow will automatically update the image tag in `deployments.yaml` when you release new versions.