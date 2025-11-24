# Frontend Deployment Setup

Complete guide to deploying the React Native Web frontend for Chores Tracker to Kubernetes.

## Table of Contents

- [Overview](#overview)
- [Frontend Architecture](#frontend-architecture)
- [Build Process](#build-process)
- [Docker Containerization](#docker-containerization)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Environment Configuration](#environment-configuration)
- [Nginx Configuration](#nginx-configuration)
- [Ingress and TLS Setup](#ingress-and-tls-setup)
- [CI/CD Integration](#cicd-integration)
- [Testing and Validation](#testing-and-validation)
- [Troubleshooting](#troubleshooting)

## Overview

The Chores Tracker frontend is a React Native Web application that provides a cross-platform user interface for web browsers.

**Technology Stack:**
- **Framework**: React Native Web with Expo
- **Build Tool**: Expo CLI
- **Web Server**: Nginx (Alpine Linux)
- **Bundler**: Metro bundler
- **Deployment**: Docker container on Kubernetes

**Deployment Model:**
- **Build**: Static assets built with Expo export
- **Container**: Nginx Alpine serving static files
- **Registry**: AWS ECR
- **Orchestration**: Kubernetes with ArgoCD GitOps
- **Replicas**: 2 for high availability
- **Resource Requirements**: Minimal (128Mi-256Mi RAM, 100m-200m CPU)

**Frontend Features:**
- Single Page Application (SPA) with client-side routing
- Responsive design for web and mobile browsers
- Offline capability through service workers (future)
- Configuration injection at runtime
- Long-term static asset caching

## Frontend Architecture

### Application Structure

```
frontend/
├── src/
│   ├── components/          # Reusable React components
│   ├── screens/             # Screen components
│   ├── contexts/            # React Context (auth, etc.)
│   ├── api/                 # API client and services
│   ├── navigation/          # React Navigation setup
│   └── App.tsx              # Root component
├── public/
│   ├── config.js            # Runtime configuration
│   └── favicon.ico
├── dist/                    # Build output (generated)
│   ├── index.html
│   ├── bundles/             # JS bundles
│   └── assets/              # Static assets
├── Dockerfile.working       # Multi-stage Docker build
├── nginx.conf               # Nginx configuration
├── package.json
└── tsconfig.json
```

### Component Communication Flow

```
┌─────────────────────────────────────────────────────────────┐
│                        User Browser                          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   NGINX Ingress (TLS)                        │
│  - Routes /* to Frontend Service                             │
│  - Routes /api/* to Backend Service                          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Frontend Service (ClusterIP :80)                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│           Frontend Pods (Nginx + Static Assets)              │
│  - Serves index.html and JS bundles                          │
│  - Handles SPA routing (fallback to index.html)              │
│  - Caches static assets (1 year)                             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼ (API calls via Axios)
┌─────────────────────────────────────────────────────────────┐
│              Backend Service (ClusterIP :8000)               │
│  - FastAPI REST endpoints                                    │
│  - JWT authentication                                        │
└─────────────────────────────────────────────────────────────┘
```

### Runtime Configuration

The frontend uses runtime configuration injection to avoid rebuilding for different environments:

**config.js** (injected at runtime):
```javascript
window.CONFIG = {
  API_URL: 'https://api.chores.yourdomain.com',
  ENVIRONMENT: 'production',
  VERSION: '1.0.0'
};
```

**Usage in React:**
```typescript
// src/api/client.ts
const apiClient = axios.create({
  baseURL: window.CONFIG?.API_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});
```

## Build Process

### Local Development Build

**1. Install dependencies:**
```bash
cd frontend
npm install
```

**2. Start development server:**
```bash
# Development mode with hot reload
npm run web

# Access at http://localhost:8081
```

**3. Type checking and linting:**
```bash
# Type check
npm run type-check

# Lint code
npm run lint

# Auto-fix lint issues
npm run lint:fix
```

**4. Run tests:**
```bash
# All tests
npm test

# Unit tests only
npm run test:unit

# Integration tests
npm run test:integration

# With coverage
npm run test:coverage
```

### Production Build

**1. Build static assets:**
```bash
cd frontend

# Production build
npm run build

# Or with explicit environment
NODE_ENV=production npm run build

# Output in dist/
ls -la dist/
# Expected:
# - index.html (entry point)
# - bundles/ (JS bundles with hashes)
# - assets/ (images, fonts, etc.)
```

**2. Verify build output:**
```bash
# Check bundle size
du -sh dist/

# Expected: ~2-5MB compressed

# Verify index.html references bundles correctly
cat dist/index.html | grep bundle
```

**3. Test locally with static server:**
```bash
# Install static server
npm install -g serve

# Serve build
serve -s dist -l 3000

# Access at http://localhost:3000
# Test routing: navigate to /chores, /profile
# Ensure page refreshes work (SPA routing)
```

### Build Configuration

**Expo configuration** (`app.json`):
```json
{
  "expo": {
    "name": "Chores Tracker",
    "slug": "chores-tracker",
    "version": "1.0.0",
    "platforms": ["web", "ios", "android"],
    "web": {
      "bundler": "metro",
      "output": "static",
      "favicon": "./public/favicon.ico"
    }
  }
}
```

**TypeScript configuration** (`tsconfig.json`):
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "esnext",
    "jsx": "react-native",
    "strict": true,
    "moduleResolution": "node",
    "esModuleInterop": true,
    "skipLibCheck": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
```

## Docker Containerization

### Dockerfile Configuration

The frontend uses a two-stage Docker build for efficiency:

**Dockerfile.working:**
```dockerfile
# Stage 1: Build stage (not used in this setup - build happens in GitHub Actions)
# We use pre-built static files from CI

# Stage 2: Production runtime
FROM nginx:alpine

# Copy pre-built static files
COPY dist/ /usr/share/nginx/html/

# Copy production configuration file
COPY public/config.js /usr/share/nginx/html/config.js

# Inject config script into the built HTML file
RUN sed -i 's|</head>|  <script src="/config.js"></script>\n</head>|g' \
    /usr/share/nginx/html/index.html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Create non-root user for security
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001

# Set proper permissions
RUN chown -R nextjs:nodejs /usr/share/nginx/html && \
    chown -R nextjs:nodejs /var/cache/nginx && \
    chown -R nextjs:nodejs /var/log/nginx && \
    chown -R nextjs:nodejs /etc/nginx/conf.d

# Create pid file directory
RUN touch /var/run/nginx.pid && \
    chown -R nextjs:nodejs /var/run/nginx.pid

# Run as non-root user
USER nextjs

# Expose port
EXPOSE 3000

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
```

### Docker Build Commands

**Local build:**
```bash
cd frontend

# Ensure dist/ exists
npm run build

# Build Docker image
docker build -f Dockerfile.working -t chores-tracker-frontend:local .

# Run locally
docker run -p 3000:3000 chores-tracker-frontend:local

# Access at http://localhost:3000
```

**Build with version tag:**
```bash
VERSION=1.0.0
docker build -f Dockerfile.working \
  -t chores-tracker-frontend:${VERSION} \
  -t chores-tracker-frontend:latest \
  --build-arg BUILD_VERSION=${VERSION} \
  --build-arg BUILD_DATE=$(date -u +%Y-%m-%dT%H:%M:%SZ) \
  .
```

**Test container:**
```bash
# Run container
docker run -d -p 3000:3000 --name frontend-test \
  chores-tracker-frontend:local

# Check logs
docker logs -f frontend-test

# Test health endpoint
curl http://localhost:3000/health
# Expected: healthy

# Test SPA routing
curl -I http://localhost:3000/chores
# Should return 200 with index.html

# Cleanup
docker stop frontend-test
docker rm frontend-test
```

### Dockerignore Configuration

**`.dockerignore.working`:**
```
node_modules
.git
.github
.expo
.expo-shared
npm-debug.log
.DS_Store
*.md
!dist
src
tests
coverage
.eslintrc.js
.prettierrc
tsconfig.json
```

**Note**: `!dist` ensures the build output is included in the container.

## Kubernetes Deployment

### Deployment Manifest

**`gitops-templates/base-apps/chores-tracker-frontend/deployments.yaml`:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: chores-tracker-frontend
  namespace: default
  labels:
    app: chores-tracker-frontend
    component: frontend
    version: v1.0.0
spec:
  replicas: 2  # High availability

  selector:
    matchLabels:
      app: chores-tracker-frontend

  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1        # Allow 1 extra pod during update
      maxUnavailable: 0  # Ensure zero downtime

  template:
    metadata:
      labels:
        app: chores-tracker-frontend
        component: frontend

    spec:
      containers:
      - name: frontend
        # Updated by CI/CD pipeline
        image: 852893458518.dkr.ecr.us-east-2.amazonaws.com/chores-tracker-frontend:latest
        imagePullPolicy: Always

        ports:
        - containerPort: 3000  # Nginx listens on 3000 (non-root)
          name: http
          protocol: TCP

        # Environment variables
        env:
        - name: NODE_ENV
          value: "production"

        # Resource limits
        resources:
          requests:
            memory: "128Mi"  # Minimal for static files
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"

        # Health checks
        livenessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          successThreshold: 1
          failureThreshold: 3

        readinessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          successThreshold: 1
          failureThreshold: 3

        # Security context
        securityContext:
          allowPrivilegeEscalation: false
          runAsNonRoot: true
          runAsUser: 1001
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL

        # Volume mounts for read-only filesystem
        volumeMounts:
        - name: tmp
          mountPath: /tmp
        - name: nginx-cache
          mountPath: /var/cache/nginx
        - name: nginx-run
          mountPath: /var/run

      # Volumes (ephemeral)
      volumes:
      - name: tmp
        emptyDir: {}
      - name: nginx-cache
        emptyDir: {}
      - name: nginx-run
        emptyDir: {}

      # Pod security context
      securityContext:
        fsGroup: 1001

      restartPolicy: Always
      terminationGracePeriodSeconds: 30
```

### Service Configuration

**`gitops-templates/base-apps/chores-tracker-frontend/service.yaml`:**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: chores-tracker-frontend-service
  namespace: default
  labels:
    app: chores-tracker-frontend
    component: frontend
spec:
  type: ClusterIP

  selector:
    app: chores-tracker-frontend

  ports:
  - name: http
    port: 80           # Service port
    targetPort: 3000   # Container port (Nginx)
    protocol: TCP

  sessionAffinity: None
```

### Deploy to Kubernetes

**Manual deployment (for testing):**
```bash
# Apply manifests
kubectl apply -f gitops-templates/base-apps/chores-tracker-frontend/

# Check deployment status
kubectl get deployment chores-tracker-frontend

# Check pods
kubectl get pods -l app=chores-tracker-frontend

# Check service
kubectl get svc chores-tracker-frontend-service

# Test service internally
kubectl run -it --rm debug --image=alpine --restart=Never -- sh
# Inside pod:
wget -O- http://chores-tracker-frontend-service/health
```

**GitOps deployment (production):**
```bash
# Copy manifests to GitOps repo
cp -r gitops-templates/base-apps/chores-tracker-frontend \
  /path/to/kubernetes/base-apps/

# Commit and push
cd /path/to/kubernetes
git add base-apps/chores-tracker-frontend/
git commit -m "feat: add frontend deployment"
git push

# ArgoCD will auto-sync if configured
```

## Environment Configuration

### Runtime Configuration File

**`public/config.js`:**
```javascript
// Runtime configuration - loaded in index.html
window.CONFIG = {
  // API endpoint (adjust per environment)
  API_URL: process.env.API_URL || 'http://chores-tracker-backend:8000/api/v1',

  // Environment
  ENVIRONMENT: process.env.NODE_ENV || 'production',

  // Feature flags
  ENABLE_OFFLINE: false,
  ENABLE_ANALYTICS: false,

  // Version (updated by CI/CD)
  VERSION: '1.0.0',
  BUILD_DATE: '2025-01-15T10:00:00Z'
};
```

### Environment-Specific Configuration

**Development:**
```javascript
window.CONFIG = {
  API_URL: 'http://localhost:8000/api/v1',
  ENVIRONMENT: 'development',
  ENABLE_OFFLINE: false,
  ENABLE_ANALYTICS: false
};
```

**Staging:**
```javascript
window.CONFIG = {
  API_URL: 'https://api-staging.chores.yourdomain.com/api/v1',
  ENVIRONMENT: 'staging',
  ENABLE_OFFLINE: true,
  ENABLE_ANALYTICS: false
};
```

**Production:**
```javascript
window.CONFIG = {
  API_URL: 'https://api.chores.yourdomain.com/api/v1',
  ENVIRONMENT: 'production',
  ENABLE_OFFLINE: true,
  ENABLE_ANALYTICS: true
};
```

### Using Configuration in React

**API Client:**
```typescript
// src/api/client.ts
import axios from 'axios';

const apiClient = axios.create({
  baseURL: (window as any).CONFIG?.API_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

export default apiClient;
```

**Feature Flag:**
```typescript
// src/utils/featureFlags.ts
export const isFeatureEnabled = (feature: string): boolean => {
  const config = (window as any).CONFIG || {};
  return config[`ENABLE_${feature.toUpperCase()}`] === true;
};

// Usage
if (isFeatureEnabled('offline')) {
  // Enable offline mode
}
```

## Nginx Configuration

### Main Nginx Configuration

**`nginx.conf`:**
```nginx
worker_processes auto;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log warn;

    # Performance
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/javascript
        application/xml+rss
        application/json;

    server {
        listen 3000;
        server_name localhost;
        root /usr/share/nginx/html;
        index index.html;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;

        # Handle client-side routing (SPA)
        location / {
            try_files $uri $uri/ /index.html;
        }

        # Cache static assets with versioned filenames
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # Health check endpoint
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }

        # Disable logging for favicon
        location = /favicon.ico {
            log_not_found off;
            access_log off;
        }
    }
}
```

### SPA Routing Explanation

**Problem**: React Router uses client-side routing. When user navigates to `/chores` and refreshes, Nginx looks for `/chores/index.html` which doesn't exist.

**Solution**: `try_files $uri $uri/ /index.html;`
- First try exact file match (`$uri`)
- Then try directory match (`$uri/`)
- Finally fallback to `index.html` (SPA entry point)

**Example:**
```
User visits: https://app.chores.com/chores/123

1. Nginx checks: /usr/share/nginx/html/chores/123 (not found)
2. Nginx checks: /usr/share/nginx/html/chores/123/ (not found)
3. Nginx serves: /usr/share/nginx/html/index.html ✓
4. React Router takes over and renders /chores/123 route
```

### Static Asset Caching

**Cache headers for versioned assets:**
```nginx
# Files with content hashes (e.g., bundle.a1b2c3.js)
location ~* \.(js|css)$ {
    expires 1y;  # Cache for 1 year
    add_header Cache-Control "public, immutable";
}
```

**No cache for index.html:**
```nginx
# Always fetch latest index.html
location = /index.html {
    add_header Cache-Control "no-cache, no-store, must-revalidate";
    expires 0;
}
```

## Ingress and TLS Setup

### Ingress Configuration

**`gitops-templates/base-apps/chores-tracker-frontend/ingress.yaml`:**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: chores-tracker-frontend-ingress
  namespace: default
  labels:
    app: chores-tracker-frontend
  annotations:
    # NGINX Ingress Controller specific
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"

    # HSTS (HTTP Strict Transport Security)
    nginx.ingress.kubernetes.io/hsts: "true"
    nginx.ingress.kubernetes.io/hsts-max-age: "31536000"
    nginx.ingress.kubernetes.io/hsts-include-subdomains: "true"

    # SPA routing support
    nginx.ingress.kubernetes.io/configuration-snippet: |
      try_files $uri $uri/ /index.html;

    # Static asset caching
    nginx.ingress.kubernetes.io/location-snippet: |
      location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
      }

spec:
  # TLS configuration
  tls:
  - hosts:
    - chores.yourdomain.com  # UPDATE THIS
    secretName: chores-frontend-tls

  # Routing rules
  rules:
  - host: chores.yourdomain.com  # UPDATE THIS
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

### TLS Certificate Setup

**Option 1: cert-manager (recommended):**

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create ClusterIssuer for Let's Encrypt
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@example.com  # UPDATE THIS
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF

# Update ingress to use cert-manager
# Add annotation:
# cert-manager.io/cluster-issuer: "letsencrypt-prod"
```

**Option 2: Manual certificate:**

```bash
# Create TLS secret from certificate files
kubectl create secret tls chores-frontend-tls \
  --cert=path/to/cert.pem \
  --key=path/to/key.pem \
  --namespace=default
```

### Domain Configuration

**DNS Setup:**
```
# A record pointing to ingress load balancer IP
chores.yourdomain.com.  300  IN  A  <INGRESS_IP>

# Or CNAME to load balancer hostname
chores.yourdomain.com.  300  IN  CNAME  <INGRESS_HOSTNAME>
```

**Get ingress IP:**
```bash
kubectl get ingress chores-tracker-frontend-ingress

# For AWS Load Balancer
kubectl get svc -n ingress-nginx ingress-nginx-controller
```

## CI/CD Integration

### GitHub Actions Workflow

The frontend release workflow (`.github/workflows/frontend-release-and-deploy.yml`) handles:

1. Version calculation
2. Build production bundle
3. Docker image creation
4. Push to ECR
5. GitOps repository update

**Key workflow steps:**

```yaml
- name: Build frontend application
  working-directory: ./frontend
  run: |
    npm ci
    npm run build
    ls -la dist/

- name: Build Docker image
  uses: docker/build-push-action@v5
  with:
    context: ./frontend
    file: ./frontend/Dockerfile.working
    platforms: linux/amd64
    push: true
    tags: |
      ${{ steps.login-ecr.outputs.registry }}/chores-tracker-frontend:${{ steps.calc_version.outputs.new_version_number }}
      ${{ steps.login-ecr.outputs.registry }}/chores-tracker-frontend:latest

- name: Update frontend deployment manifest
  run: |
    cd kubernetes
    sed -i "s|image: ${BASE_IMAGE}:[^[:space:]]*|image: ${BASE_IMAGE}:${NEW_VERSION}|" \
      base-apps/chores-tracker-frontend/deployments.yaml
```

### Running a Frontend Release

**1. Trigger release workflow:**
```bash
# Go to GitHub Actions UI
# Select: "Frontend Release and Deploy"
# Inputs:
#   - Release type: minor
#   - Update GitOps: true
#   - Auto-merge: false
```

**2. Workflow execution:**
- Builds frontend (`npm run build`)
- Runs tests (`npm run test:ci`)
- Creates Docker image
- Pushes to ECR with tags:
  - `1.0.0` (version)
  - `1.0` (major.minor)
  - `1` (major)
  - `latest`
  - `sha-<commit-hash>`

**3. GitOps update:**
- Workflow creates PR in `arigsela/kubernetes`
- Updates `deployments.yaml` image tag
- PR includes release notes and deployment checklist

**4. Deploy:**
- Review and merge GitOps PR
- ArgoCD auto-syncs
- Rolling update with zero downtime

## Testing and Validation

### Pre-Deployment Testing

**1. Local build test:**
```bash
cd frontend
npm run build
npm install -g serve
serve -s dist -p 3000

# Test in browser
open http://localhost:3000
# Navigate through app
# Test authentication
# Verify API calls work
```

**2. Docker container test:**
```bash
# Build image
docker build -f Dockerfile.working -t frontend-test .

# Run container
docker run -d -p 3000:3000 --name test frontend-test

# Test endpoints
curl http://localhost:3000/health  # Should return "healthy"
curl -I http://localhost:3000/     # Should return 200
curl -I http://localhost:3000/chores  # Should return 200 (SPA routing)

# Check logs
docker logs test

# Cleanup
docker stop test && docker rm test
```

**3. Kubernetes dry-run:**
```bash
# Validate manifests
kubectl apply --dry-run=client \
  -f gitops-templates/base-apps/chores-tracker-frontend/

# Validate with server
kubectl apply --dry-run=server \
  -f gitops-templates/base-apps/chores-tracker-frontend/
```

### Post-Deployment Validation

**1. Check deployment:**
```bash
# Deployment status
kubectl get deployment chores-tracker-frontend

# Expected:
# NAME                      READY   UP-TO-DATE   AVAILABLE
# chores-tracker-frontend   2/2     2            2

# Rollout status
kubectl rollout status deployment/chores-tracker-frontend

# Pod status
kubectl get pods -l app=chores-tracker-frontend
```

**2. Test service:**
```bash
# Port forward to service
kubectl port-forward svc/chores-tracker-frontend-service 8080:80

# Test health endpoint
curl http://localhost:8080/health

# Test SPA routing
curl -I http://localhost:8080/
curl -I http://localhost:8080/chores
```

**3. Test ingress:**
```bash
# Get ingress details
kubectl describe ingress chores-tracker-frontend-ingress

# Test domain
curl -I https://chores.yourdomain.com
# Should return 200

# Test SPA routing
curl -I https://chores.yourdomain.com/chores
# Should return 200 with index.html

# Test static assets
curl -I https://chores.yourdomain.com/bundles/main.js
# Should have Cache-Control: public, immutable
```

**4. End-to-end test:**
```bash
# Access in browser
open https://chores.yourdomain.com

# Test checklist:
# [ ] Login page loads
# [ ] Can authenticate
# [ ] Dashboard displays
# [ ] Navigation works
# [ ] API calls succeed
# [ ] Page refresh preserves route
# [ ] Static assets load quickly (cached)
# [ ] No console errors
```

## Troubleshooting

### Common Issues

**1. Pod fails to start:**

```bash
# Check pod status
kubectl get pods -l app=chores-tracker-frontend

# Check events
kubectl describe pod <pod-name>

# Check logs
kubectl logs <pod-name>

# Common causes:
# - Image pull error: Check ECR credentials
# - Volume mount error: Verify volumes in deployment
# - Port conflict: Ensure port 3000 is correct
```

**2. Health check failures:**

```bash
# Test health endpoint from pod
kubectl exec -it <pod-name> -- wget -O- http://localhost:3000/health

# If fails:
# - Check nginx.conf health endpoint
# - Verify port 3000 is exposed
# - Check nginx is running: ps aux | grep nginx
```

**3. SPA routing not working (404 on refresh):**

```bash
# Check nginx config
kubectl exec -it <pod-name> -- cat /etc/nginx/nginx.conf

# Verify try_files directive:
# try_files $uri $uri/ /index.html;

# Check ingress annotations
kubectl get ingress chores-tracker-frontend-ingress -o yaml

# Should have:
# nginx.ingress.kubernetes.io/configuration-snippet: |
#   try_files $uri $uri/ /index.html;
```

**4. API calls fail (CORS errors):**

```bash
# Check config.js API_URL
kubectl exec -it <pod-name> -- cat /usr/share/nginx/html/config.js

# Verify backend CORS settings
# Should allow frontend domain

# Check in browser console:
# window.CONFIG.API_URL
# Should match backend service URL
```

**5. Static assets not cached:**

```bash
# Check response headers
curl -I https://chores.yourdomain.com/bundles/main.js

# Should have:
# Cache-Control: public, immutable
# Expires: <1 year from now>

# If missing:
# - Check nginx.conf location block
# - Check ingress location-snippet annotation
```

### Debug Commands

```bash
# Get all frontend resources
kubectl get all -l app=chores-tracker-frontend

# Describe deployment
kubectl describe deployment chores-tracker-frontend

# Check pod logs
kubectl logs -f deployment/chores-tracker-frontend

# Execute commands in pod
kubectl exec -it <pod-name> -- sh
# ls -la /usr/share/nginx/html/
# cat /etc/nginx/nginx.conf
# wget -O- http://localhost:3000/health

# Check service endpoints
kubectl get endpoints chores-tracker-frontend-service

# Test service from another pod
kubectl run -it --rm debug --image=alpine --restart=Never -- sh
wget -O- http://chores-tracker-frontend-service/health

# Check ingress
kubectl describe ingress chores-tracker-frontend-ingress
kubectl get ingress chores-tracker-frontend-ingress -o yaml
```

## Best Practices

**1. Build Optimization:**
- Use production builds (`NODE_ENV=production`)
- Enable tree-shaking and minification
- Analyze bundle size: `npm run build --analyze`
- Lazy load routes and components

**2. Caching Strategy:**
- Long-term cache static assets (1 year)
- No cache for index.html
- Use content hashes in filenames
- Set proper Cache-Control headers

**3. Security:**
- Run as non-root user
- Read-only root filesystem
- Drop all capabilities
- Set security headers (CSP, HSTS)
- Use TLS/HTTPS only

**4. Performance:**
- Enable gzip compression
- Minimize resource requests
- Use HTTP/2
- Implement service worker for offline (future)

**5. Monitoring:**
- Track deployment metrics
- Monitor error rates
- Set up alerts for 5xx errors
- Use APM for performance tracking

## Next Steps

After deploying the frontend:

1. **Set up monitoring**: Configure error tracking (Sentry, etc.)
2. **Enable analytics**: Google Analytics or alternative
3. **Implement PWA**: Service worker for offline support
4. **Performance monitoring**: Real User Monitoring (RUM)
5. **A/B testing**: Feature flag infrastructure

## Related Documentation

- [GitOps CD Setup](./GITOPS_CD_SETUP.md) - ArgoCD and GitOps workflow
- [Kubernetes Deployment](./KUBERNETES.md) - K8s architecture and configuration
- [Release Process](./RELEASING.md) - Version management
- [Backend Deployment](../CLAUDE.md#backend-fastapi--sqlalchemy) - API deployment
