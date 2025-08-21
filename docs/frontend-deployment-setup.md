# Frontend Deployment Setup Guide

This document outlines the setup required for deploying the frontend web application using the same containerized approach as the backend.

## Files Created

### 1. Frontend Dockerfile (`frontend/Dockerfile.working`)
- **Simple nginx build**: Uses pre-built static files from `dist/` folder
- **Production optimized**: Includes static asset caching and compression  
- **Security**: Runs as non-root user with proper permissions
- **Health checks**: Includes `/health` endpoint for Kubernetes probes

**Note**: We use `Dockerfile.working` instead of the multi-stage `Dockerfile` due to TypeScript path alias resolution issues in Docker builds. The CI workflow builds the static files locally first, then containerizes them.

### 2. Nginx Configuration (`frontend/nginx.conf`)
- **Client-side routing**: Handles SPA routing with fallback to index.html
- **Static asset optimization**: Long-term caching for JS/CSS/images
- **Security headers**: X-Frame-Options, X-Content-Type-Options, etc.
- **Compression**: Gzip enabled for text-based assets

### 3. CI/CD Workflow (`frontend-release-and-deploy.yml`)
- **Separate versioning**: Uses `frontend-v*` tags to avoid conflicts with backend
- **Quality gates**: Runs linting, type checking, and tests before build
- **Local build**: Runs `npm run build` to create static files before Docker build
- **Docker registry**: Pushes to separate ECR repository using `Dockerfile.working`
- **GitOps integration**: Creates PRs to update Kubernetes manifests

### 4. Package.json Updates
- Added `build` and `build:production` scripts for production web builds
- Uses `expo export --platform web` to generate static web assets

## Required Configuration

### AWS Secrets (GitHub Repository Secrets)
Add these new secrets to your GitHub repository:

```bash
ECR_REPOSITORY_FRONTEND=chores-tracker-frontend  # Your frontend ECR repo name
```

The following existing secrets will be reused:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY` 
- `AWS_REGION`
- `GITOPS_PAT`

### ECR Repository
Create a new ECR repository for the frontend:

```bash
aws ecr create-repository \
  --repository-name chores-tracker-frontend \
  --region us-east-2
```

### GitOps Repository Structure
In your `arigsela/kubernetes` repository, create:

```
base-apps/
├── chores-tracker/           # Existing backend
│   └── deployments.yaml
└── chores-tracker-frontend/  # New frontend
    ├── deployments.yaml
    ├── service.yaml
    └── ingress.yaml (optional)
```

### Sample Kubernetes Manifests

#### Frontend Deployment (`base-apps/chores-tracker-frontend/deployments.yaml`)
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: chores-tracker-frontend
  namespace: default
spec:
  replicas: 2
  selector:
    matchLabels:
      app: chores-tracker-frontend
  template:
    metadata:
      labels:
        app: chores-tracker-frontend
    spec:
      containers:
      - name: frontend
        image: 852893458518.dkr.ecr.us-east-2.amazonaws.com/chores-tracker-frontend:latest
        ports:
        - containerPort: 3000
        env:
        - name: NODE_ENV
          value: "production"
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
        livenessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 5
```

#### Frontend Service (`base-apps/chores-tracker-frontend/service.yaml`)
```yaml
apiVersion: v1
kind: Service
metadata:
  name: chores-tracker-frontend-service
  namespace: default
spec:
  selector:
    app: chores-tracker-frontend
  ports:
  - port: 80
    targetPort: 3000
    protocol: TCP
  type: ClusterIP
```

## Build Approach

Due to TypeScript path alias resolution issues (`@/contexts/AuthContext`) in Docker multi-stage builds with Expo, we use a **two-step build process**:

1. **Local Build**: GitHub Actions runs `npm run build` to create static files
2. **Containerization**: Docker copies the pre-built `dist/` folder into nginx container

This approach:
- ✅ Avoids module resolution issues in Docker
- ✅ Faster Docker builds (no npm install in container)
- ✅ Consistent with many React deployment patterns
- ✅ Separates build concerns from serving concerns

## Deployment Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   GitHub Repo   │    │   AWS ECR       │
│                 │    │                 │
│ Backend:        │───▶│ chores-tracker  │
│ └── Dockerfile  │    │                 │
│                 │    │ chores-tracker- │
│ Frontend:       │───▶│ frontend        │
│ └── Dockerfile  │    │                 │
└─────────────────┘    └─────────────────┘
         │                       │
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│  GitOps Repo    │    │   Kubernetes    │
│                 │    │                 │
│ chores-tracker/ │───▶│ Backend Pods    │
│ chores-tracker- │───▶│ Frontend Pods   │
│ frontend/       │    │                 │
└─────────────────┘    └─────────────────┘
```

## Key Differences from Backend

1. **Build Process**: Uses Expo to export web assets instead of Python packaging
2. **Serving**: Uses nginx instead of uvicorn
3. **Versioning**: Separate tag prefix (`frontend-v*`) to avoid conflicts
4. **Repository**: Separate ECR repository for better organization
5. **Health Checks**: Uses nginx `/health` endpoint instead of FastAPI health

## Testing the Setup

### Local Testing
```bash
cd frontend
docker build -t chores-tracker-frontend .
docker run -p 3000:3000 chores-tracker-frontend
# Visit http://localhost:3000
```

### Production Deployment
1. Run the "Frontend Release and Deploy" workflow
2. Select release type and options
3. Workflow will:
   - Build and test the frontend
   - Create Docker image and push to ECR
   - Create GitOps PR for deployment
   - Auto-merge if enabled

## Environment Configuration

The frontend may need API endpoint configuration. Consider adding environment variables:

```yaml
# In deployment.yaml
env:
- name: REACT_APP_API_URL
  value: "https://api.your-domain.com"
- name: NODE_ENV
  value: "production"
```

This setup provides a complete containerized deployment pipeline for your frontend that mirrors your backend approach while handling the specific requirements of a React Native web application.