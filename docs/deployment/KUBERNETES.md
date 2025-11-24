# Kubernetes Deployment Guide

Comprehensive guide to the Kubernetes infrastructure and deployment architecture for Chores Tracker.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
  - [Namespace Structure](#namespace-structure)
  - [Component Overview](#component-overview)
  - [Network Architecture](#network-architecture)
- [MySQL StatefulSet](#mysql-statefulset)
  - [Storage Configuration](#storage-configuration)
  - [Backup and Recovery](#backup-and-recovery)
- [Backend Deployment](#backend-deployment)
  - [Deployment Configuration](#deployment-configuration)
  - [Environment Configuration](#environment-configuration)
  - [Health Checks](#health-checks)
  - [Resource Limits](#resource-limits)
- [Frontend Deployment](#frontend-deployment)
  - [Nginx Configuration](#nginx-configuration)
  - [SPA Routing](#spa-routing)
  - [Static Asset Caching](#static-asset-caching)
- [Migration Jobs](#migration-jobs)
  - [ArgoCD Sync Waves](#argocd-sync-waves)
  - [Migration Job Configuration](#migration-job-configuration)
- [Ingress and Services](#ingress-and-services)
  - [Service Configuration](#service-configuration)
  - [Ingress Configuration](#ingress-configuration)
  - [TLS/SSL Setup](#tlsssl-setup)
- [GitOps with ArgoCD](#gitops-with-argocd)
  - [GitOps Repository Structure](#gitops-repository-structure)
  - [Deployment Workflow](#deployment-workflow)
  - [Sync Waves and Hooks](#sync-waves-and-hooks)
- [Secrets Management](#secrets-management)
- [Monitoring and Observability](#monitoring-and-observability)
- [Common Operations](#common-operations)
- [Troubleshooting](#troubleshooting)

## Overview

Chores Tracker runs on Kubernetes with the following characteristics:

**Deployment Model:**
- **GitOps**: Declarative infrastructure managed via Git
- **Continuous Deployment**: ArgoCD automatically syncs changes from Git
- **High Availability**: Multiple replicas with rolling updates
- **Stateful Data**: MySQL StatefulSet with persistent volumes
- **Zero-Downtime**: Health checks and rolling deployment strategy

**Technology Stack:**
- **Container Runtime**: Docker
- **Orchestration**: Kubernetes (EKS, GKE, or other)
- **GitOps CD**: ArgoCD
- **Ingress**: NGINX Ingress Controller
- **Database**: MySQL 8.0 StatefulSet
- **Container Registry**: AWS ECR

**Environments:**
- **Development**: Docker Compose (see `docker-compose.yml`)
- **Staging/Production**: Kubernetes cluster

## Architecture

### Namespace Structure

```
chores-tracker-backend/
├── MySQL StatefulSet
├── Backend Deployment (2 replicas)
├── Backend Service (ClusterIP)
├── Migration Jobs
├── ConfigMaps
└── Secrets

default/
├── Frontend Deployment (2 replicas)
├── Frontend Service (ClusterIP)
└── Frontend Ingress
```

**Namespace Design:**
- `chores-tracker-backend`: Backend API and database
- `default` (or custom): Frontend web application
- Separation allows independent scaling and access control

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Internet                              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   NGINX Ingress Controller                   │
│  - TLS termination                                           │
│  - Route /api/* → Backend Service                            │
│  - Route /* → Frontend Service                               │
└─────────────┬──────────────────────────┬─────────────────────┘
              │                          │
              ▼                          ▼
    ┌─────────────────┐        ┌──────────────────┐
    │ Frontend Service│        │ Backend Service  │
    │  (ClusterIP)    │        │  (ClusterIP)     │
    └────────┬────────┘        └────────┬─────────┘
             │                          │
             ▼                          ▼
    ┌─────────────────┐        ┌──────────────────┐
    │Frontend Pods    │        │Backend Pods      │
    │  (2 replicas)   │        │  (2 replicas)    │
    │  - React Native │        │  - FastAPI       │
    │    Web (nginx)  │        │  - SQLAlchemy    │
    └─────────────────┘        └────────┬─────────┘
                                        │
                                        ▼
                               ┌──────────────────┐
                               │ MySQL StatefulSet│
                               │  (1 pod)         │
                               │  - Persistent    │
                               │    Volume        │
                               └──────────────────┘

Deployment Sequence (ArgoCD Sync Waves):
┌─────────────────────────────────────────────────────────────┐
│ Wave 0: ConfigMaps, Secrets, MySQL StatefulSet              │
│ Wave 1: Migration Job (PreSync Hook)                        │
│ Wave 2: Backend Deployment, Backend Service                 │
│ Wave 3: Frontend Deployment, Frontend Service, Ingress      │
└─────────────────────────────────────────────────────────────┘
```

### Network Architecture

**Internal Communication:**
- Backend → MySQL: `mysql:3306` (within namespace)
- Frontend → Backend: `chores-tracker-backend-service:8000`

**External Access:**
- HTTPS (443) → Ingress → Services → Pods
- TLS termination at ingress level

**Security:**
- Services use ClusterIP (internal only)
- Only Ingress exposes external access
- Network policies (optional, not shown in base config)

## MySQL StatefulSet

### Storage Configuration

MySQL runs as a StatefulSet to ensure:
- Stable network identity
- Persistent storage
- Ordered deployment and scaling
- Graceful shutdowns

**Key Configuration:**
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mysql
  namespace: chores-tracker-backend
spec:
  serviceName: mysql
  replicas: 1  # Single instance for simplicity
  volumeClaimTemplates:
  - metadata:
      name: mysql-data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: gp3  # AWS EBS gp3 (adjust for your cloud)
      resources:
        requests:
          storage: 20Gi
```

**Storage Classes by Cloud Provider:**
- AWS EKS: `gp3` (general purpose SSD) or `gp2`
- GCP GKE: `standard-rwo` or `ssd`
- Azure AKS: `managed-premium`
- On-premise: Configure based on storage backend

**Persistent Volume Claims:**
- Automatically created by StatefulSet
- Survives pod restarts and deletions
- Must be manually deleted if you want to remove data

### Backup and Recovery

**Manual Backup:**
```bash
# Create backup
kubectl exec -n chores-tracker-backend statefulset/mysql -- \
  mysqldump -u root -p${MYSQL_ROOT_PASSWORD} chores_tracker > backup.sql

# With timestamp
kubectl exec -n chores-tracker-backend statefulset/mysql -- \
  mysqldump -u root -p${MYSQL_ROOT_PASSWORD} chores_tracker \
  > backup-$(date +%Y%m%d-%H%M%S).sql
```

**Restore from Backup:**
```bash
# Copy backup to pod
kubectl cp backup.sql chores-tracker-backend/mysql-0:/tmp/backup.sql

# Restore
kubectl exec -n chores-tracker-backend statefulset/mysql -- \
  mysql -u root -p${MYSQL_ROOT_PASSWORD} chores_tracker < /tmp/backup.sql
```

**Automated Backups:**
Consider using:
- CronJob for scheduled mysqldump
- Cloud provider backup solutions (AWS RDS, GCP Cloud SQL)
- Velero for cluster-level backups
- MySQL replication for high availability

## Backend Deployment

### Deployment Configuration

**Location**: `gitops-templates/base-apps/chores-tracker-backend/deployment.yaml`

**Key Features:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: chores-tracker-backend
  namespace: chores-tracker-backend
  annotations:
    argocd.argoproj.io/sync-wave: "2"  # Deploy after migration
spec:
  replicas: 2  # High availability
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0  # Zero-downtime deployments
```

**Rolling Update Strategy:**
- Creates new pod before terminating old one (`maxUnavailable: 0`)
- Allows one extra pod during update (`maxSurge: 1`)
- Ensures continuous availability during deployments

### Environment Configuration

**ConfigMap** (`configmap.yaml`):
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: chores-tracker-backend-config
  namespace: chores-tracker-backend
  annotations:
    argocd.argoproj.io/sync-wave: "0"  # Create first
data:
  ENVIRONMENT: "production"
  DEBUG: "false"
  PORT: "8000"
  BACKEND_CORS_ORIGINS: "https://your-frontend-domain.com"
```

**Secrets** (created separately, not in Git):
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: chores-tracker-backend-secrets
  namespace: chores-tracker-backend
type: Opaque
stringData:
  DATABASE_URL: "mysql+aiomysql://user:password@mysql:3306/chores_tracker"
  SECRET_KEY: "your-secret-key-here"
  MYSQL_ROOT_PASSWORD: "root-password"
```

**Environment Injection:**
```yaml
containers:
- name: chores-tracker-backend
  envFrom:
  - configMapRef:
      name: chores-tracker-backend-config
  - secretRef:
      name: chores-tracker-backend-secrets
```

### Health Checks

**Liveness Probe** (restarts unhealthy pods):
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 90  # Allow app startup time
  periodSeconds: 30
  timeoutSeconds: 10
  failureThreshold: 3  # Restart after 3 failures
```

**Readiness Probe** (removes from load balancer when unhealthy):
```yaml
readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 60
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3  # Remove from service after 3 failures
```

**Health Endpoint** (`backend/app/main.py`):
```python
@app.get("/health")
async def health():
    return {"status": "healthy"}
```

### Resource Limits

```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "200m"  # 0.2 CPU cores
  limits:
    memory: "1Gi"
    cpu: "1000m"  # 1 CPU core
```

**Resource Definitions:**
- **Requests**: Guaranteed resources for scheduling
- **Limits**: Maximum resources pod can consume
- **CPU**: Throttled if exceeded (measured in millicores)
- **Memory**: Pod killed if exceeded (OOMKilled)

**Tuning Recommendations:**
- Monitor actual usage with `kubectl top pods`
- Adjust based on traffic patterns
- Leave headroom for spikes (limits > requests)
- Production typically needs more than development

## Frontend Deployment

### Nginx Configuration

**Frontend serves static React Native Web build:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: chores-tracker-frontend
  namespace: default
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: frontend
        image: 852893458518.dkr.ecr.us-east-2.amazonaws.com/chores-tracker-frontend:latest
        ports:
        - containerPort: 3000
        env:
        - name: API_URL
          value: "http://chores-tracker-backend-service:8000/api/v1"
```

**Container Details:**
- Based on nginx:alpine
- Serves static files from `/usr/share/nginx/html`
- Custom nginx.conf for SPA routing
- Health check on `/health` endpoint

### SPA Routing

Frontend uses client-side routing (React Navigation). Nginx must serve `index.html` for all routes:

**Ingress Configuration:**
```yaml
annotations:
  nginx.ingress.kubernetes.io/configuration-snippet: |
    try_files $uri $uri/ /index.html;
```

This ensures routes like `/chores`, `/profile`, etc. work correctly.

### Static Asset Caching

**Long-term caching for static assets:**
```yaml
annotations:
  nginx.ingress.kubernetes.io/location-snippet: |
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
      expires 1y;
      add_header Cache-Control "public, immutable";
    }
```

**Benefits:**
- Improved performance
- Reduced bandwidth
- Faster page loads
- Better user experience

## Migration Jobs

### ArgoCD Sync Waves

Sync waves ensure proper deployment order:

```
Wave 0: ConfigMaps, Secrets, StatefulSets (MySQL)
   ↓
Wave 1: Migration Job (PreSync Hook)
   ↓
   Wait for migration to complete
   ↓
Wave 2: Backend Deployment, Backend Service
   ↓
Wave 3: Frontend Deployment, Frontend Service, Ingress
```

**Sync Wave Annotations:**
```yaml
metadata:
  annotations:
    argocd.argoproj.io/sync-wave: "1"
```

Lower numbers deploy first. Negative numbers are allowed.

### Migration Job Configuration

**Location**: `gitops-templates/base-apps/chores-tracker-backend/migration-job.yaml`

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: chores-tracker-migration
  namespace: chores-tracker-backend
  annotations:
    argocd.argoproj.io/sync-wave: "1"
    argocd.argoproj.io/hook: PreSync  # Run before main sync
    argocd.argoproj.io/hook-delete-policy: BeforeHookCreation
spec:
  backoffLimit: 4  # Retry up to 4 times
  activeDeadlineSeconds: 300  # 5 minute timeout
  ttlSecondsAfterFinished: 86400  # Keep logs for 24 hours
  template:
    spec:
      restartPolicy: OnFailure
      containers:
      - name: migration
        image: 852893458518.dkr.ecr.us-east-2.amazonaws.com/chores-tracker:latest
        command: ["/app/migrate-entrypoint.sh"]
        envFrom:
        - configMapRef:
            name: chores-tracker-backend-config
        - secretRef:
            name: chores-tracker-backend-secrets
```

**Migration Entrypoint** (`migrate-entrypoint.sh`):
```bash
#!/bin/bash
set -e

echo "Running database migrations..."
cd /app
python -m alembic -c backend/alembic.ini upgrade head
echo "Migrations completed successfully"
```

**How It Works:**
1. ArgoCD detects new commit in GitOps repo
2. Sync wave 0: ConfigMaps/Secrets created
3. Sync wave 1: Migration job runs (PreSync hook)
4. Job runs Alembic migrations
5. Job must complete successfully before proceeding
6. Sync wave 2+: Application deployment continues

**Viewing Migration Status:**
```bash
# Check job status
kubectl get job chores-tracker-migration -n chores-tracker-backend

# View logs
kubectl logs -n chores-tracker-backend job/chores-tracker-migration

# Check if successful
kubectl get job chores-tracker-migration -n chores-tracker-backend \
  -o jsonpath='{.status.succeeded}'
```

## Ingress and Services

### Service Configuration

**Backend Service** (`service.yaml`):
```yaml
apiVersion: v1
kind: Service
metadata:
  name: chores-tracker-backend-service
  namespace: chores-tracker-backend
spec:
  type: ClusterIP  # Internal only
  ports:
  - port: 8000
    targetPort: 8000
    protocol: TCP
    name: http
  selector:
    app: chores-tracker-backend
```

**Frontend Service**:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: chores-tracker-frontend-service
  namespace: default
spec:
  type: ClusterIP
  ports:
  - port: 80
    targetPort: 3000
    protocol: TCP
    name: http
  selector:
    app: chores-tracker-frontend
```

**Service Types:**
- **ClusterIP**: Internal cluster access only (used here)
- **NodePort**: External access on node IP (not recommended for production)
- **LoadBalancer**: Cloud load balancer (expensive, Ingress preferred)

### Ingress Configuration

**Frontend Ingress** (`ingress.yaml`):
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: chores-tracker-frontend-ingress
  namespace: default
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
    nginx.ingress.kubernetes.io/hsts: "true"
    nginx.ingress.kubernetes.io/hsts-max-age: "31536000"
spec:
  tls:
  - hosts:
    - chores-frontend.your-domain.com
    secretName: chores-frontend-tls
  rules:
  - host: chores-frontend.your-domain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: chores-tracker-frontend-service
            port:
              number: 80
```

**Key Features:**
- TLS/SSL termination at ingress
- HSTS for security
- Automatic HTTP → HTTPS redirect
- SPA routing support
- Static asset caching

### TLS/SSL Setup

**Option 1: Manual Certificate**
```bash
# Create TLS secret
kubectl create secret tls chores-frontend-tls \
  --cert=path/to/tls.crt \
  --key=path/to/tls.key \
  -n default
```

**Option 2: cert-manager (Recommended)**
```yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: chores-frontend-tls
  namespace: default
spec:
  secretName: chores-frontend-tls
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
  - chores-frontend.your-domain.com
```

**Option 3: Cloud Provider Certificate**
- AWS Certificate Manager (ACM)
- GCP Managed Certificates
- Azure Application Gateway

## GitOps with ArgoCD

### GitOps Repository Structure

**Recommended Structure:**
```
arigsela/kubernetes/  (separate Git repository)
├── base-apps/
│   ├── chores-tracker-backend/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── configmap.yaml
│   │   ├── migration-job.yaml
│   │   └── kustomization.yaml
│   └── chores-tracker-frontend/
│       ├── deployment.yaml
│       ├── service.yaml
│       ├── ingress.yaml
│       └── kustomization.yaml
├── overlays/
│   ├── staging/
│   └── production/
└── argocd-apps/
    ├── chores-tracker-backend.yaml
    └── chores-tracker-frontend.yaml
```

**Why Separate Repository?**
- Decouples infrastructure from code
- Enables RBAC (developers vs. ops)
- Cleaner audit trail
- Simplifies rollbacks

### Deployment Workflow

```
1. Developer pushes code to GitHub
   ↓
2. GitHub Actions CI builds Docker image
   ↓
3. CI pushes image to ECR with tag
   ↓
4. CI updates image tag in GitOps repo (arigsela/kubernetes)
   ↓
5. ArgoCD detects change in GitOps repo
   ↓
6. ArgoCD syncs Kubernetes cluster to match Git
   ↓
7. Migration Job runs (sync wave 1)
   ↓
8. Backend Deployment updates (sync wave 2)
   ↓
9. Frontend Deployment updates (sync wave 3)
   ↓
10. Application running with new version
```

**Image Tag Update** (in CI pipeline):
```bash
# Update image tag in deployment.yaml
yq eval -i '.spec.template.spec.containers[0].image = "852893458518.dkr.ecr.us-east-2.amazonaws.com/chores-tracker:'"${VERSION}"'"' \
  base-apps/chores-tracker-backend/deployment.yaml

# Commit and push
git add base-apps/chores-tracker-backend/deployment.yaml
git commit -m "chore: update backend image to ${VERSION}"
git push origin main
```

### Sync Waves and Hooks

**ArgoCD Sync Waves** control deployment order:

```yaml
# Wave 0: Foundation (ConfigMaps, Secrets, StatefulSets)
metadata:
  annotations:
    argocd.argoproj.io/sync-wave: "0"

# Wave 1: Migrations (Jobs)
metadata:
  annotations:
    argocd.argoproj.io/sync-wave: "1"
    argocd.argoproj.io/hook: PreSync

# Wave 2: Backend Application
metadata:
  annotations:
    argocd.argoproj.io/sync-wave: "2"

# Wave 3: Frontend and Ingress
metadata:
  annotations:
    argocd.argoproj.io/sync-wave: "3"
```

**Hook Types:**
- **PreSync**: Run before main sync (migrations)
- **Sync**: Run during sync
- **PostSync**: Run after sync (smoke tests)
- **SyncFail**: Run on sync failure (rollback)

**Hook Delete Policies:**
- **BeforeHookCreation**: Delete old job before creating new one
- **HookSucceeded**: Delete after success
- **HookFailed**: Delete after failure

## Secrets Management

**Creating Secrets:**

```bash
# From literal values
kubectl create secret generic chores-tracker-backend-secrets \
  -n chores-tracker-backend \
  --from-literal=DATABASE_URL='mysql+aiomysql://user:pass@mysql:3306/chores_tracker' \
  --from-literal=SECRET_KEY='your-secret-key-here'

# From file
kubectl create secret generic chores-tracker-backend-secrets \
  -n chores-tracker-backend \
  --from-env-file=.env.production

# Using base64 encoding (in YAML)
apiVersion: v1
kind: Secret
metadata:
  name: chores-tracker-backend-secrets
  namespace: chores-tracker-backend
type: Opaque
data:
  DATABASE_URL: bXlzcWwrYWlvbXlzcWw6Ly8uLi4=  # base64 encoded
  SECRET_KEY: eW91ci1zZWNyZXQta2V5  # base64 encoded
```

**Updating Secrets:**
```bash
# Edit directly (not recommended for production)
kubectl edit secret chores-tracker-backend-secrets -n chores-tracker-backend

# Delete and recreate
kubectl delete secret chores-tracker-backend-secrets -n chores-tracker-backend
kubectl create secret generic chores-tracker-backend-secrets \
  -n chores-tracker-backend \
  --from-literal=DATABASE_URL='new-value'

# Patch specific key
kubectl patch secret chores-tracker-backend-secrets -n chores-tracker-backend \
  -p '{"data":{"SECRET_KEY":"bmV3LXZhbHVl"}}'
```

**Best Practices:**
- Use external secret management (AWS Secrets Manager, HashiCorp Vault)
- Never commit secrets to Git
- Rotate secrets regularly
- Use RBAC to restrict access
- Encrypt secrets at rest (Kubernetes default)

**External Secrets Operator** (recommended):
```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: chores-tracker-backend-secrets
  namespace: chores-tracker-backend
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: chores-tracker-backend-secrets
  data:
  - secretKey: DATABASE_URL
    remoteRef:
      key: chores-tracker/production/database-url
```

## Monitoring and Observability

**Application Metrics:**
- Prometheus metrics exposed at `/metrics` endpoint
- Grafana dashboards for visualization
- Alertmanager for alerting

**Kubernetes Metrics:**
```bash
# Pod resource usage
kubectl top pods -n chores-tracker-backend

# Node resource usage
kubectl top nodes

# Detailed pod metrics
kubectl get --raw /apis/metrics.k8s.io/v1beta1/namespaces/chores-tracker-backend/pods
```

**Logging:**
```bash
# View logs
kubectl logs -n chores-tracker-backend deployment/chores-tracker-backend

# Follow logs
kubectl logs -f -n chores-tracker-backend deployment/chores-tracker-backend

# Previous pod logs (after crash)
kubectl logs -n chores-tracker-backend deployment/chores-tracker-backend --previous

# All pods with label
kubectl logs -n chores-tracker-backend -l app=chores-tracker-backend --tail=100
```

**Centralized Logging** (recommended):
- ELK Stack (Elasticsearch, Logstash, Kibana)
- EFK Stack (Elasticsearch, Fluentd, Kibana)
- Loki + Grafana
- Cloud provider logging (CloudWatch, Cloud Logging)

## Common Operations

### Scaling

```bash
# Scale backend to 3 replicas
kubectl scale deployment chores-tracker-backend -n chores-tracker-backend --replicas=3

# Scale frontend to 5 replicas
kubectl scale deployment chores-tracker-frontend -n default --replicas=5

# Update GitOps repo to persist change
# Edit deployment.yaml replicas field and commit
```

### Rolling Restart

```bash
# Restart backend (triggers rolling update)
kubectl rollout restart deployment/chores-tracker-backend -n chores-tracker-backend

# Restart frontend
kubectl rollout restart deployment/chores-tracker-frontend -n default
```

### Rollback

```bash
# View rollout history
kubectl rollout history deployment/chores-tracker-backend -n chores-tracker-backend

# Rollback to previous version
kubectl rollout undo deployment/chores-tracker-backend -n chores-tracker-backend

# Rollback to specific revision
kubectl rollout undo deployment/chores-tracker-backend -n chores-tracker-backend --to-revision=3

# Check rollout status
kubectl rollout status deployment/chores-tracker-backend -n chores-tracker-backend
```

### Database Access

```bash
# Access MySQL shell
kubectl exec -it -n chores-tracker-backend statefulset/mysql -- mysql -u root -p

# Run query directly
kubectl exec -n chores-tracker-backend statefulset/mysql -- \
  mysql -u root -p${MYSQL_ROOT_PASSWORD} -e "SHOW DATABASES;"

# Port forward for local access
kubectl port-forward -n chores-tracker-backend statefulset/mysql 3306:3306
# Then connect: mysql -h 127.0.0.1 -u root -p
```

### Pod Shell Access

```bash
# Execute shell in backend pod
kubectl exec -it -n chores-tracker-backend deployment/chores-tracker-backend -- /bin/bash

# Run one-off command
kubectl exec -n chores-tracker-backend deployment/chores-tracker-backend -- \
  python -m backend.app.scripts.list_users

# Execute in specific pod
kubectl exec -it -n chores-tracker-backend chores-tracker-backend-7d8f9c6b5-abc12 -- /bin/bash
```

## Troubleshooting

### Pod Not Starting

**Check pod status:**
```bash
kubectl get pods -n chores-tracker-backend
kubectl describe pod <pod-name> -n chores-tracker-backend
```

**Common issues:**
- **ImagePullBackOff**: ECR authentication issue, wrong image name
- **CrashLoopBackOff**: Application crash on startup
- **Pending**: Resource constraints, no nodes available
- **Error**: Container exited with error

**Solutions:**
```bash
# Check events
kubectl get events -n chores-tracker-backend --sort-by='.lastTimestamp'

# Check logs
kubectl logs <pod-name> -n chores-tracker-backend

# Check previous logs (if restarting)
kubectl logs <pod-name> -n chores-tracker-backend --previous
```

### Health Check Failures

**Symptoms:**
- Pods restarting frequently
- Readiness probe failing
- Pods not receiving traffic

**Diagnosis:**
```bash
# Check probe configuration
kubectl get pod <pod-name> -n chores-tracker-backend -o yaml | grep -A 10 probe

# Test health endpoint manually
kubectl exec -n chores-tracker-backend <pod-name> -- curl http://localhost:8000/health

# Check application logs for startup errors
kubectl logs <pod-name> -n chores-tracker-backend
```

**Common fixes:**
- Increase `initialDelaySeconds` if app takes time to start
- Increase `timeoutSeconds` if health check is slow
- Fix application code if `/health` endpoint is broken

### Database Connection Issues

**Symptoms:**
- Backend can't connect to MySQL
- "Connection refused" errors
- "Unknown MySQL server host" errors

**Diagnosis:**
```bash
# Check MySQL pod is running
kubectl get pods -n chores-tracker-backend | grep mysql

# Check MySQL service
kubectl get service mysql -n chores-tracker-backend

# Test connection from backend pod
kubectl exec -n chores-tracker-backend deployment/chores-tracker-backend -- \
  nc -zv mysql 3306

# Check DATABASE_URL format
kubectl get secret chores-tracker-backend-secrets -n chores-tracker-backend -o yaml
```

**Common fixes:**
- Ensure MySQL pod is running and ready
- Verify DATABASE_URL uses correct hostname (`mysql` not `localhost`)
- Check credentials in secret
- Ensure backend has network access to MySQL

### Migration Job Failures

**Symptoms:**
- Migration job shows Failed status
- Backend deployment blocked
- ArgoCD sync fails

**Diagnosis:**
```bash
# Check job status
kubectl get job chores-tracker-migration -n chores-tracker-backend

# View logs
kubectl logs job/chores-tracker-migration -n chores-tracker-backend

# Describe job
kubectl describe job chores-tracker-migration -n chores-tracker-backend
```

**Common fixes:**
```bash
# Delete failed job and retry
kubectl delete job chores-tracker-migration -n chores-tracker-backend
# ArgoCD will recreate it automatically

# Run migration manually to debug
kubectl exec -it -n chores-tracker-backend deployment/chores-tracker-backend -- \
  python -m alembic -c backend/alembic.ini upgrade head
```

### Ingress Not Routing

**Symptoms:**
- 404 errors from ingress
- Can't access application
- TLS errors

**Diagnosis:**
```bash
# Check ingress status
kubectl get ingress -n default

# Describe ingress
kubectl describe ingress chores-tracker-frontend-ingress -n default

# Check ingress controller logs
kubectl logs -n ingress-nginx deployment/nginx-ingress-controller

# Verify DNS points to ingress
nslookup chores-frontend.your-domain.com
```

**Common fixes:**
- Verify DNS record points to ingress external IP
- Check TLS secret exists
- Ensure backend service name matches ingress spec
- Verify ingress controller is running

### Resource Exhaustion

**Symptoms:**
- Pods being OOMKilled
- CPU throttling
- Pending pods

**Diagnosis:**
```bash
# Check resource usage
kubectl top pods -n chores-tracker-backend
kubectl top nodes

# Check resource requests/limits
kubectl describe pod <pod-name> -n chores-tracker-backend | grep -A 5 Limits
```

**Solutions:**
- Increase resource limits in deployment.yaml
- Add more nodes to cluster
- Optimize application memory usage
- Enable horizontal pod autoscaling (HPA)

---

## Related Documentation

- [Database Migrations](../operations/database-migrations.md) - Migration procedures and troubleshooting
- [GitOps CD Setup](GITOPS_CD_SETUP.md) - ArgoCD configuration and workflow (if exists)
- [Releasing](RELEASING.md) - Release process and versioning
- [Backend Architecture](../architecture/BACKEND_ARCHITECTURE.md) - System design and components

## Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [NGINX Ingress Controller](https://kubernetes.github.io/ingress-nginx/)
- [Tiltfile Reference](../../Tiltfile) - Local Kubernetes development

---

**Last Updated**: November 23, 2024
**Kubernetes Version**: 1.27+
**Maintained By**: Chores Tracker DevOps Team
