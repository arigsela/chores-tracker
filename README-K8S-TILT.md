# Kubernetes-Based Tilt Development

This guide explains how to use Tilt to replicate your production Kubernetes deployments locally, giving you a development environment that closely mirrors your production setup.

## Overview

Your current `Tiltfile` uses Docker Compose for local development, which is fast but doesn't match your production Kubernetes environment. This new setup provides:

- **Production Parity**: Same container configurations as your GitOps deployments
- **Health Checks**: Liveness and readiness probes like in production
- **Resource Limits**: Memory and CPU constraints matching production
- **Service Discovery**: Kubernetes DNS for inter-service communication
- **Fast Development**: Live code updates with Tilt's live_update feature

## Files Added

- **`Tiltfile.k8s`**: Kubernetes-based Tilt configuration
- **`k8s-dev.yaml`**: Kubernetes manifests mirroring your GitOps structure
- **`README-K8S-TILT.md`**: This guide

## Prerequisites

### 1. Local Kubernetes Cluster

You need a local Kubernetes cluster. Choose one:

#### Option A: Docker Desktop (Recommended)
```bash
# Enable Kubernetes in Docker Desktop settings
# Then verify it's running:
kubectl cluster-info
```

#### Option B: Minikube
```bash
# Install and start minikube
minikube start
```

#### Option C: Kind (Kubernetes in Docker)
```bash
# Install kind, then create a cluster
kind create cluster --name chores-dev
```

### 2. Verify Setup
```bash
# Check your cluster is accessible
kubectl get nodes

# Verify Tilt can connect
tilt doctor
```

## Usage

### Starting the Kubernetes Development Environment

```bash
# Start with Kubernetes-based Tiltfile
tilt up -f Tiltfile.k8s

# Open Tilt UI (automatically opens in browser)
# Visit: http://localhost:10350
```

### Available Services

Once running, you'll have access to:

- **Backend API**: http://localhost:8000 (FastAPI with /docs)
- **Frontend Web App**: http://localhost:3000 (React/Expo web app)
- **Database**: MySQL on localhost:3306

### Development Workflow

1. **Make code changes** in `./backend/` or `./frontend/` directories
2. **Tilt auto-syncs** changes to the running containers
3. **Frontend rebuilds** automatically when you modify React/Expo source files
4. **Test your changes** against the Kubernetes deployment
5. **Run migrations** using the manual trigger in Tilt UI
6. **Run tests** using the test helper in Tilt UI

### Optional Manual Operations

All test and utility operations are **manual-only** to keep your development environment clean. In the Tilt UI, you can trigger these when needed:

#### Database Operations:
- **`db-migrate`**: Run database migrations when schema changes

#### Testing Operations:
- **`health-check`**: Quick backend health verification
- **`run-tests`**: Complete backend test suite (pytest)
- **`test-db-connection`**: Verify MySQL connection and async driver
- **`test-api`**: Quick API endpoint functionality check

#### How to Use:
1. **In Tilt UI**: Click the ▶️ button next to any optional resource
2. **Filter by label**: Use `optional`, `test`, `database`, or `api` labels to find specific operations
3. **No auto-run**: These won't run automatically or slow down your startup

#### Benefits of Optional Tests:
- **Faster Startup**: Core services start quickly without waiting for tests
- **On-Demand Testing**: Run tests only when you need them
- **Focused Development**: Choose which tests to run based on what you're working on
- **Clean UI**: Tilt interface shows only essential services by default

## Architecture Comparison

### Current Docker Compose Setup
```
┌─────────────┐    ┌─────────────┐
│   FastAPI   │    │    MySQL    │
│  (direct)   │────│  (direct)   │
└─────────────┘    └─────────────┘
```

### New Kubernetes Setup
```
┌─────────────┐    ┌─────────────────┐    ┌─────────────┐    ┌─────────────┐
│ React/Expo  │    │   FastAPI       │    │ Kubernetes  │    │    MySQL    │
│ Frontend    │────│   Backend       │────│ Service DNS │────│  Container  │
│ + Nginx     │    │   Container     │    │+ Load Bal.  │    │ + Health    │ 
│ + Health    │    │   + Health      │    │+ Discovery  │    │ + Resources │
└─────────────┘    └─────────────────┘    └─────────────┘    └─────────────┘
```

## Key Differences from Docker Compose

### 1. Service Discovery
- **Docker Compose**: Services accessible by container name
- **Kubernetes**: Services accessible via Kubernetes DNS (`servicename.namespace.svc.cluster.local`)

### 2. Health Checks
- **Docker Compose**: Basic healthcheck command
- **Kubernetes**: Separate liveness and readiness probes with detailed configuration

### 3. Resource Management
- **Docker Compose**: Unlimited resources
- **Kubernetes**: Explicit CPU and memory requests/limits

### 4. Networking
- **Docker Compose**: Bridge network
- **Kubernetes**: CNI networking with service mesh capabilities

### 5. Deployment Lifecycle
- **Docker Compose**: Simple start/stop
- **Kubernetes**: Rolling deployments, replica sets, pod lifecycle management

## Troubleshooting

### Container Won't Start
```bash
# Check pod status
kubectl get pods -n chores-dev

# View pod logs
kubectl logs -n chores-dev deployment/chores-tracker-backend

# Describe pod for events
kubectl describe pod -n chores-dev -l app=chores-tracker-backend
```

### Database Connection Issues
```bash
# Check MySQL pod
kubectl get pods -n chores-dev -l app=mysql

# Test database connection
kubectl exec -n chores-dev deployment/mysql -- mysql -u root -prootpassword -e "SELECT 1"

# Check service endpoints
kubectl get endpoints -n chores-dev mysql
```

### Port Forward Issues
```bash
# Manual port forward if Tilt's isn't working
kubectl port-forward -n chores-dev service/chores-tracker-service 8000:8000

# List all port forwards
kubectl get services -n chores-dev
```

### Tilt Issues
```bash
# Clear Tilt state
tilt down -f Tiltfile.k8s
tilt up -f Tiltfile.k8s

# Check Tilt logs
tilt logs

# Doctor command for diagnostics
tilt doctor
```

## Full Stack Development

The setup now includes both backend and frontend containers by default:

### Frontend Container Details
- **Technology**: React/Expo web build served by nginx
- **Port**: Accessible at http://localhost:3000
- **Live Updates**: Automatically rebuilds when you change source files in `./frontend/src/`
- **Configuration**: Uses dynamic config.js for API URL configuration
- **Health Checks**: nginx `/health` endpoint for Kubernetes probes

### Development Features
- **Hot Reloading**: Changes to React components sync and trigger rebuilds
- **API Integration**: Frontend connects to backend via Kubernetes service discovery
- **Production Parity**: Same nginx configuration and build process as production

## Performance Considerations

### Resource Usage
- **Memory**: Kubernetes adds ~100-200MB overhead vs Docker Compose
- **CPU**: Similar performance, but with proper resource limiting
- **Startup**: Slower initial startup due to health check delays

### Optimization Tips
- Use `live_update` for fastest code sync
- Adjust resource limits in `k8s-dev.yaml` if needed
- Consider using persistent volumes for MySQL data in longer dev sessions

## Integration with Your CI/CD

This setup helps with CI/CD because:

1. **Same Health Checks**: Your liveness/readiness probes are tested locally
2. **Same Resource Limits**: Memory/CPU limits are validated before deployment
3. **Same Network Patterns**: Service-to-service communication is tested
4. **Same Security Context**: Container security settings are validated

## Migration from Docker Compose

To gradually migrate:

1. **Keep using `tilt up`** (original Tiltfile) for daily development
2. **Use `tilt up -f Tiltfile.k8s`** when:
   - Testing deployment changes
   - Debugging production issues
   - Validating resource limits
   - Testing health check configurations
3. **Eventually switch** once comfortable with Kubernetes workflow

## Next Steps

1. **Test the setup** with your current development workflow
2. **Adjust resource limits** in `k8s-dev.yaml` based on your needs
3. **Enable frontend** if you want to test the full stack
4. **Add more development helpers** as local_resource in Tiltfile
5. **Consider adding ingress** for more realistic routing

This Kubernetes-based development environment gives you confidence that what works locally will work in production!