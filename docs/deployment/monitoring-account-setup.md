# Monitoring Service Account Setup

Complete guide to setting up Kubernetes service accounts and RBAC configuration for Prometheus metrics collection and monitoring integration.

## Table of Contents

- [Overview](#overview)
- [Service Account Architecture](#service-account-architecture)
- [Prometheus Metrics Overview](#prometheus-metrics-overview)
- [RBAC Configuration](#rbac-configuration)
- [Service Account Setup](#service-account-setup)
- [Prometheus Integration](#prometheus-integration)
- [Monitoring Stack Setup](#monitoring-stack-setup)
- [Security Considerations](#security-considerations)
- [Verification and Testing](#verification-and-testing)
- [Troubleshooting](#troubleshooting)

## Overview

The Chores Tracker backend exposes Prometheus metrics at the `/metrics` endpoint. To collect these metrics in a Kubernetes environment, we need to configure proper service accounts with appropriate RBAC permissions.

**Monitoring Architecture:**
```
┌─────────────────────────────────────────────────────────────┐
│                    Prometheus Server                         │
│  - ServiceAccount: prometheus                                │
│  - ClusterRole: prometheus                                   │
│  - Scrapes /metrics endpoints                                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Backend Pods (with /metrics)                    │
│  - Service annotations: prometheus.io/scrape                 │
│  - Port 8000                                                 │
│  - Path /metrics                                             │
└─────────────────────────────────────────────────────────────┘
```

**Key Components:**
- **Service Account**: Identity for Prometheus to access K8s API
- **ClusterRole**: Permissions to discover and scrape pods/services
- **ClusterRoleBinding**: Links service account to cluster role
- **ServiceMonitor**: Custom resource for Prometheus Operator (optional)

## Service Account Architecture

### Why Service Accounts Matter

**Security Principle: Least Privilege**

Service accounts provide:
- **Authentication**: Prove identity to Kubernetes API
- **Authorization**: Grant minimum required permissions
- **Audit**: Track which component made API calls
- **Isolation**: Separate credentials per service

**Without Service Account:**
```bash
# Prometheus would use default service account
# May have too many or too few permissions
# Harder to audit and control access
```

**With Dedicated Service Account:**
```bash
# Prometheus has explicit permissions
# Can revoke access without affecting other services
# Clear audit trail in K8s logs
```

### Service Account Permissions Needed

**Prometheus needs to:**
1. **Discover** pods and services
2. **Read** pod/service metadata (labels, annotations)
3. **Access** endpoints for scraping
4. **Monitor** namespace resources

**Prometheus does NOT need:**
- Create/update/delete resources
- Access secrets
- Modify deployments
- Execute commands in pods

## Prometheus Metrics Overview

### Backend Metrics Endpoint

**Endpoint:** `http://chores-tracker-backend:8000/metrics`

**Metric Categories:**

| Category | Metrics | Examples |
|----------|---------|----------|
| **HTTP** | Request count, duration, size | `http_requests_total`, `http_request_duration_seconds` |
| **Chores** | Created, completed, approved | `chores_created_total{mode="single"}` |
| **Users** | Registrations, logins | `user_logins_total{role="parent"}` |
| **Families** | Created, active count | `families_active_count` |
| **Rewards** | Adjustments, payments | `rewards_paid_total` |
| **Errors** | API errors, database errors | `api_errors_total{endpoint="/api/v1/chores"}` |

**Full metrics documentation:** See `backend/app/core/metrics.py`

### Service Annotations for Prometheus

The backend service uses annotations to enable automatic discovery:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: chores-tracker-backend
  namespace: chores-tracker-backend
  annotations:
    # Enable Prometheus scraping
    prometheus.io/scrape: "true"
    # Port to scrape metrics from
    prometheus.io/port: "8000"
    # Path to metrics endpoint
    prometheus.io/path: "/metrics"
spec:
  selector:
    app: chores-tracker-backend
  ports:
  - name: http
    port: 8000
    targetPort: 8000
```

## RBAC Configuration

### ClusterRole for Prometheus

**Purpose**: Define permissions Prometheus needs cluster-wide.

**Create:** `k8s/monitoring/prometheus-clusterrole.yaml`

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: prometheus
  labels:
    app: prometheus
rules:
# Read access to pods for service discovery
- apiGroups: [""]
  resources:
  - nodes
  - nodes/metrics
  - services
  - endpoints
  - pods
  verbs: ["get", "list", "watch"]

# Read access to ConfigMaps (for Prometheus config reloading)
- apiGroups: [""]
  resources:
  - configmaps
  verbs: ["get"]

# Read access to Ingress (for ingress controller metrics)
- apiGroups: ["networking.k8s.io"]
  resources:
  - ingresses
  verbs: ["get", "list", "watch"]

# Read access to non-resource URLs (for /metrics on API server)
- nonResourceURLs:
  - /metrics
  - /metrics/cadvisor
  verbs: ["get"]
```

### ServiceAccount

**Purpose**: Identity that Prometheus runs as.

**Create:** `k8s/monitoring/prometheus-serviceaccount.yaml`

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: prometheus
  namespace: monitoring  # Or wherever Prometheus is deployed
  labels:
    app: prometheus
automountServiceAccountToken: true
```

**Token Mounting:**
- `automountServiceAccountToken: true`: Automatically mount token in Prometheus pod
- Token location: `/var/run/secrets/kubernetes.io/serviceaccount/token`
- Prometheus uses this token to authenticate with K8s API

### ClusterRoleBinding

**Purpose**: Grant the ClusterRole permissions to the ServiceAccount.

**Create:** `k8s/monitoring/prometheus-clusterrolebinding.yaml`

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: prometheus
  labels:
    app: prometheus
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: prometheus
subjects:
- kind: ServiceAccount
  name: prometheus
  namespace: monitoring  # Must match ServiceAccount namespace
```

**Scope:**
- `ClusterRole` + `ClusterRoleBinding` = Cluster-wide permissions
- Alternative: `Role` + `RoleBinding` = Namespace-scoped permissions

### Namespace-Scoped Alternative (More Secure)

**For single-namespace monitoring:**

```yaml
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: prometheus
  namespace: chores-tracker-backend
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: prometheus
  namespace: chores-tracker-backend
rules:
- apiGroups: [""]
  resources: ["services", "endpoints", "pods"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: prometheus
  namespace: chores-tracker-backend
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: prometheus
subjects:
- kind: ServiceAccount
  name: prometheus
  namespace: chores-tracker-backend
```

**Tradeoffs:**
- **ClusterRole**: Monitors entire cluster, requires broader permissions
- **Role**: Monitors single namespace, more secure but limited scope

## Service Account Setup

### Step 1: Create Monitoring Namespace

```bash
# Create namespace for monitoring stack
kubectl create namespace monitoring

# Verify
kubectl get namespaces | grep monitoring
```

### Step 2: Apply RBAC Resources

```bash
# Create all monitoring RBAC resources
kubectl apply -f k8s/monitoring/prometheus-serviceaccount.yaml
kubectl apply -f k8s/monitoring/prometheus-clusterrole.yaml
kubectl apply -f k8s/monitoring/prometheus-clusterrolebinding.yaml

# Verify service account
kubectl get serviceaccount prometheus -n monitoring

# Verify cluster role
kubectl get clusterrole prometheus

# Verify binding
kubectl get clusterrolebinding prometheus
```

### Step 3: Verify Permissions

```bash
# Check what the service account can do
kubectl auth can-i list pods \
  --as=system:serviceaccount:monitoring:prometheus

# Expected: yes

kubectl auth can-i create pods \
  --as=system:serviceaccount:monitoring:prometheus

# Expected: no

kubectl auth can-i get services \
  --as=system:serviceaccount:monitoring:prometheus \
  --all-namespaces

# Expected: yes
```

### Step 4: Configure Prometheus to Use Service Account

**Prometheus Deployment:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prometheus
  template:
    metadata:
      labels:
        app: prometheus
    spec:
      # Use the service account we created
      serviceAccountName: prometheus

      containers:
      - name: prometheus
        image: prom/prometheus:v2.47.0
        args:
        - '--config.file=/etc/prometheus/prometheus.yml'
        - '--storage.tsdb.path=/prometheus'
        - '--web.console.libraries=/usr/share/prometheus/console_libraries'
        - '--web.console.templates=/usr/share/prometheus/consoles'
        ports:
        - containerPort: 9090
          name: web
        volumeMounts:
        - name: config
          mountPath: /etc/prometheus
        - name: storage
          mountPath: /prometheus

      volumes:
      - name: config
        configMap:
          name: prometheus-config
      - name: storage
        emptyDir: {}
```

## Prometheus Integration

### Prometheus Configuration

**Create:** `k8s/monitoring/prometheus-configmap.yaml`

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: monitoring
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s

    scrape_configs:
    # Scrape Prometheus itself
    - job_name: 'prometheus'
      static_configs:
      - targets: ['localhost:9090']

    # Kubernetes API server metrics
    - job_name: 'kubernetes-apiservers'
      kubernetes_sd_configs:
      - role: endpoints
      scheme: https
      tls_config:
        ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
      bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
      relabel_configs:
      - source_labels: [__meta_kubernetes_namespace, __meta_kubernetes_service_name, __meta_kubernetes_endpoint_port_name]
        action: keep
        regex: default;kubernetes;https

    # Kubernetes nodes (kubelet)
    - job_name: 'kubernetes-nodes'
      kubernetes_sd_configs:
      - role: node
      scheme: https
      tls_config:
        ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
      bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
      relabel_configs:
      - action: labelmap
        regex: __meta_kubernetes_node_label_(.+)

    # Kubernetes pods with prometheus.io/scrape annotation
    - job_name: 'kubernetes-pods'
      kubernetes_sd_configs:
      - role: pod

      relabel_configs:
      # Only scrape pods with prometheus.io/scrape=true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true

      # Custom scrape path (default: /metrics)
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)

      # Custom scrape port (default: pod port)
      - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
        action: replace
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: $1:$2
        target_label: __address__

      # Add pod metadata as labels
      - action: labelmap
        regex: __meta_kubernetes_pod_label_(.+)
      - source_labels: [__meta_kubernetes_namespace]
        action: replace
        target_label: kubernetes_namespace
      - source_labels: [__meta_kubernetes_pod_name]
        action: replace
        target_label: kubernetes_pod_name

    # Kubernetes services with prometheus.io/scrape annotation
    - job_name: 'kubernetes-services'
      kubernetes_sd_configs:
      - role: service

      relabel_configs:
      # Only scrape services with prometheus.io/scrape=true
      - source_labels: [__meta_kubernetes_service_annotation_prometheus_io_scrape]
        action: keep
        regex: true

      # Custom scrape path
      - source_labels: [__meta_kubernetes_service_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)

      # Custom scrape port
      - source_labels: [__address__, __meta_kubernetes_service_annotation_prometheus_io_port]
        action: replace
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: $1:$2
        target_label: __address__

      # Add service metadata as labels
      - action: labelmap
        regex: __meta_kubernetes_service_label_(.+)
      - source_labels: [__meta_kubernetes_namespace]
        action: replace
        target_label: kubernetes_namespace
      - source_labels: [__meta_kubernetes_service_name]
        action: replace
        target_label: kubernetes_service_name
```

### Apply Prometheus Configuration

```bash
# Create ConfigMap
kubectl apply -f k8s/monitoring/prometheus-configmap.yaml

# Deploy Prometheus
kubectl apply -f k8s/monitoring/prometheus-deployment.yaml

# Expose Prometheus UI
kubectl expose deployment prometheus \
  --type=ClusterIP \
  --port=9090 \
  --name=prometheus-service \
  -n monitoring

# Port forward to access locally
kubectl port-forward svc/prometheus-service 9090:9090 -n monitoring

# Access UI
open http://localhost:9090
```

## Monitoring Stack Setup

### Option 1: Prometheus Operator (Recommended)

**Install Prometheus Operator with Helm:**

```bash
# Add Prometheus community Helm repo
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install kube-prometheus-stack
# Includes: Prometheus, Grafana, Alertmanager, exporters
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false

# Wait for pods to be ready
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=prometheus -n monitoring --timeout=300s
```

**ServiceMonitor for Chores Tracker:**

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: chores-tracker-backend
  namespace: monitoring
  labels:
    app: chores-tracker-backend
spec:
  # Which namespaces to monitor
  namespaceSelector:
    matchNames:
    - chores-tracker-backend

  # Which services to monitor
  selector:
    matchLabels:
      app: chores-tracker-backend

  # Endpoints to scrape
  endpoints:
  - port: http  # Service port name
    path: /metrics
    interval: 30s
    scrapeTimeout: 10s
```

**Apply ServiceMonitor:**

```bash
kubectl apply -f k8s/monitoring/servicemonitor-chores-tracker.yaml

# Verify Prometheus discovered the target
kubectl port-forward svc/prometheus-kube-prometheus-prometheus 9090:9090 -n monitoring

# Open Prometheus UI > Status > Targets
# Should see: chores-tracker-backend/chores-tracker-backend/0
```

### Option 2: Vanilla Prometheus

**Complete deployment with ConfigMap approach:**

```bash
# 1. Create RBAC resources
kubectl apply -f k8s/monitoring/prometheus-serviceaccount.yaml
kubectl apply -f k8s/monitoring/prometheus-clusterrole.yaml
kubectl apply -f k8s/monitoring/prometheus-clusterrolebinding.yaml

# 2. Create configuration
kubectl apply -f k8s/monitoring/prometheus-configmap.yaml

# 3. Deploy Prometheus
kubectl apply -f k8s/monitoring/prometheus-deployment.yaml

# 4. Expose service
kubectl apply -f k8s/monitoring/prometheus-service.yaml

# 5. Verify
kubectl get all -n monitoring
```

### Grafana Integration

**Install Grafana:**

```bash
# If using kube-prometheus-stack, Grafana is included
# Access Grafana
kubectl port-forward svc/prometheus-grafana 3000:80 -n monitoring

# Default credentials:
# Username: admin
# Password: prom-operator (or get from secret)

# Get password from secret
kubectl get secret prometheus-grafana -n monitoring -o jsonpath="{.data.admin-password}" | base64 -d; echo
```

**Add Prometheus Data Source:**

1. Open Grafana UI (http://localhost:3000)
2. Login with admin credentials
3. Configuration > Data Sources > Add data source
4. Select Prometheus
5. URL: `http://prometheus-kube-prometheus-prometheus:9090`
6. Save & Test

**Import Chores Tracker Dashboard:**

1. Create dashboard
2. Add panel for chore metrics:
   - Query: `rate(chores_created_total[5m])`
   - Visualization: Graph
3. Add panel for user logins:
   - Query: `sum by (role) (user_logins_total)`
   - Visualization: Stat
4. Save dashboard

**Example PromQL Queries:**

```promql
# Chores created per hour by mode
rate(chores_created_total[1h]) * 3600

# Chore completion rate
rate(chores_completed_total[5m]) / rate(chores_created_total[5m])

# 95th percentile API response time
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Error rate
rate(api_errors_total[5m])

# Active users by role
active_users_count

# Top 5 slowest endpoints
topk(5, http_request_duration_seconds_sum / http_request_duration_seconds_count)
```

## Security Considerations

### Principle of Least Privilege

**Good: Minimal Permissions**
```yaml
rules:
- apiGroups: [""]
  resources: ["pods", "services", "endpoints"]
  verbs: ["get", "list", "watch"]  # Read-only
```

**Bad: Over-privileged**
```yaml
rules:
- apiGroups: ["*"]
  resources: ["*"]
  verbs: ["*"]  # Full cluster admin!
```

### Network Policies

**Restrict Prometheus network access:**

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: prometheus-network-policy
  namespace: monitoring
spec:
  podSelector:
    matchLabels:
      app: prometheus

  policyTypes:
  - Ingress
  - Egress

  # Allow incoming traffic to Prometheus UI
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: monitoring
    ports:
    - protocol: TCP
      port: 9090

  # Allow outgoing traffic to scrape targets
  egress:
  # DNS
  - to:
    - namespaceSelector: {}
      podSelector:
        matchLabels:
          k8s-app: kube-dns
    ports:
    - protocol: UDP
      port: 53

  # Kubernetes API
  - to:
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 443

  # Application metrics endpoints
  - to:
    - namespaceSelector:
        matchLabels:
          name: chores-tracker-backend
    ports:
    - protocol: TCP
      port: 8000
```

### Secret Management

**Prometheus configuration with secrets:**

```yaml
# For external authentication
apiVersion: v1
kind: Secret
metadata:
  name: prometheus-basic-auth
  namespace: monitoring
type: Opaque
stringData:
  username: prometheus
  password: <generate-secure-password>
```

**Use in scrape config:**
```yaml
scrape_configs:
- job_name: 'external-service'
  basic_auth:
    username_file: /etc/prometheus/secrets/username
    password_file: /etc/prometheus/secrets/password
  static_configs:
  - targets: ['external-service:9100']
```

## Verification and Testing

### Verify Service Account

```bash
# Check service account exists
kubectl get serviceaccount prometheus -n monitoring

# Describe to see secrets
kubectl describe serviceaccount prometheus -n monitoring

# Get token (for manual API calls)
TOKEN=$(kubectl get secret -n monitoring \
  $(kubectl get serviceaccount prometheus -n monitoring -o jsonpath='{.secrets[0].name}') \
  -o jsonpath='{.data.token}' | base64 -d)

echo $TOKEN
```

### Test API Access

```bash
# Test API access with service account token
kubectl run -it --rm test \
  --image=curlimages/curl \
  --restart=Never \
  --serviceaccount=prometheus \
  --namespace=monitoring \
  -- sh

# Inside pod:
TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
APISERVER=https://kubernetes.default.svc

# List pods
curl -s $APISERVER/api/v1/namespaces/chores-tracker-backend/pods \
  --header "Authorization: Bearer $TOKEN" \
  --cacert /var/run/secrets/kubernetes.io/serviceaccount/ca.crt | jq .
```

### Verify Metrics Scraping

```bash
# Port forward to Prometheus
kubectl port-forward svc/prometheus-service 9090:9090 -n monitoring

# Open UI
open http://localhost:9090

# Check targets: Status > Targets
# Should see chores-tracker-backend with state "UP"

# Run test query
# In Prometheus UI: Expression Browser
# Query: chores_created_total
# Should return metrics if backend has created chores
```

### Test Metrics Endpoint

```bash
# Port forward directly to backend
kubectl port-forward svc/chores-tracker-backend 8000:8000 \
  -n chores-tracker-backend

# Fetch metrics
curl http://localhost:8000/metrics

# Expected output:
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
# http_requests_total{method="GET",endpoint="/api/v1/chores"} 42.0
# ...
```

## Troubleshooting

### Prometheus Not Scraping Targets

**Symptom:** Targets show as "DOWN" in Prometheus UI

**Debugging:**

```bash
# 1. Check service annotations
kubectl get svc chores-tracker-backend -n chores-tracker-backend -o yaml | grep prometheus

# Expected:
#   prometheus.io/scrape: "true"
#   prometheus.io/port: "8000"
#   prometheus.io/path: "/metrics"

# 2. Verify service endpoints
kubectl get endpoints chores-tracker-backend -n chores-tracker-backend

# Should show pod IPs

# 3. Check Prometheus logs
kubectl logs -f deployment/prometheus -n monitoring

# Look for errors like:
# - "permission denied" → RBAC issue
# - "no such host" → Service discovery issue
# - "connection refused" → Backend not exposing metrics

# 4. Test metrics endpoint manually
kubectl run -it --rm curl --image=curlimages/curl --restart=Never -- \
  curl -v http://chores-tracker-backend.chores-tracker-backend:8000/metrics
```

### RBAC Permission Denied

**Symptom:** Prometheus logs show 403 Forbidden errors

**Fix:**

```bash
# Check current permissions
kubectl auth can-i list pods \
  --as=system:serviceaccount:monitoring:prometheus \
  --namespace=chores-tracker-backend

# If "no", update ClusterRole
kubectl edit clusterrole prometheus

# Add missing permissions:
rules:
- apiGroups: [""]
  resources: ["pods", "services", "endpoints"]
  verbs: ["get", "list", "watch"]
```

### Metrics Not Appearing in Prometheus

**Symptom:** Prometheus scraping successfully but queries return no data

**Debugging:**

```bash
# 1. Verify metrics are actually being generated
kubectl exec -it <backend-pod> -n chores-tracker-backend -- \
  curl localhost:8000/metrics | grep chores_created_total

# If empty, application hasn't recorded metrics yet
# Trigger some actions (create chores, login, etc.)

# 2. Check Prometheus scrape interval
# In Prometheus UI > Status > Configuration
# Look for scrape_interval and last scrape time

# 3. Force immediate scrape (Prometheus Operator)
# Delete ServiceMonitor and recreate
kubectl delete servicemonitor chores-tracker-backend -n monitoring
kubectl apply -f k8s/monitoring/servicemonitor-chores-tracker.yaml
```

### High Cardinality Metrics

**Symptom:** Prometheus running out of memory, slow queries

**Cause:** Too many unique label combinations

**Fix:**

```python
# Bad: User ID as label (high cardinality)
user_actions_total.labels(user_id=user.id).inc()  # ❌

# Good: User role as label (low cardinality)
user_actions_total.labels(role=user.role).inc()  # ✓
```

**Monitor cardinality:**
```promql
# Top metrics by cardinality
topk(10, count by (__name__)({__name__=~".+"}))
```

## Best Practices

**1. Service Account Security:**
- Use namespace-scoped roles when possible
- Grant minimum required permissions
- Regularly audit service account usage
- Rotate tokens periodically (automated by K8s)

**2. Metrics Design:**
- Keep label cardinality low (<100 unique values)
- Use consistent naming conventions
- Document all custom metrics
- Avoid metrics for high-frequency events without aggregation

**3. Scrape Configuration:**
- Set appropriate scrape intervals (15-30s typical)
- Configure scrape timeouts < interval
- Use service discovery instead of static configs
- Monitor scrape duration and failures

**4. Resource Limits:**
```yaml
# Prometheus deployment
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "1000m"
```

**5. Data Retention:**
```yaml
# Prometheus args
args:
- '--storage.tsdb.retention.time=15d'  # Keep 15 days
- '--storage.tsdb.retention.size=10GB'  # Or 10GB max
```

## Next Steps

After setting up monitoring:

1. **Create Dashboards**: Build Grafana dashboards for key metrics
2. **Configure Alerts**: Set up Prometheus alerting rules
3. **Notification Channels**: Integrate with Slack, PagerDuty, etc.
4. **Log Aggregation**: Add ELK or Loki for centralized logging
5. **Distributed Tracing**: Consider Jaeger for request tracing

## Related Documentation

- [GitOps CD Setup](./GITOPS_CD_SETUP.md) - ArgoCD deployment workflow
- [Kubernetes Deployment](./KUBERNETES.md) - K8s architecture
- [Backend Metrics](../../backend/app/core/metrics.py) - Custom metrics definitions
- [Prometheus Documentation](https://prometheus.io/docs/) - Official Prometheus docs
- [Kubernetes RBAC](https://kubernetes.io/docs/reference/access-authn-authz/rbac/) - RBAC reference
