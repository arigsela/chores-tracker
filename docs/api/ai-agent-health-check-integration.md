# Health Check Integration Guide for AI Agents and Monitoring Systems

## Overview

The Chores Tracker API provides a comprehensive three-tier health check system designed for Kubernetes liveness/readiness probes, monitoring systems, and AI agent integration.

### Health Check Tiers

1. **Basic Liveness** (`/health`) - Fast, no dependencies
2. **Readiness Check** (`/api/v1/health/ready`) - Database connectivity validation
3. **Detailed Diagnostics** (`/api/v1/health/detailed`) - Component-level health status

---

## Table of Contents

1. [Quick Reference](#quick-reference)
2. [Health Check Endpoints](#health-check-endpoints)
3. [Kubernetes Integration](#kubernetes-integration)
4. [Monitoring System Integration](#monitoring-system-integration)
5. [AI Agent Integration Patterns](#ai-agent-integration-patterns)
6. [Response Formats](#response-formats)
7. [Alerting Strategies](#alerting-strategies)
8. [Troubleshooting Unhealthy States](#troubleshooting-unhealthy-states)
9. [Best Practices](#best-practices)

---

## Quick Reference

### Health Check URLs

```bash
# Basic liveness (no dependencies)
http://localhost:8000/health

# Readiness with DB check (Kubernetes readiness probe)
http://localhost:8000/api/v1/health/ready

# Detailed diagnostics (monitoring systems)
http://localhost:8000/api/v1/health/detailed
```

### Quick Test

```bash
# Test all health checks
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/health/ready
curl http://localhost:8000/api/v1/health/detailed
```

---

## Health Check Endpoints

### 1. Basic Liveness Check

**Endpoint**: `GET /health`

**Purpose**: Fast application liveness check with no dependencies

**Use Cases**:
- Kubernetes liveness probes
- Load balancer health checks
- Quick service availability checks

**Implementation:**

```python
# backend/app/api/api_v1/endpoints/health.py
@router.get("/health")
async def basic_health():
    """
    Basic liveness check - no dependencies.

    Returns 200 if the application process is running.
    Used by: Kubernetes liveness probes, load balancers.
    """
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat()
    }
```

**Example Request:**

```bash
curl -X GET "http://localhost:8000/health"
```

**Example Response:**

```json
{
  "status": "ok",
  "timestamp": "2025-11-23T12:34:56.789012"
}
```

**Response Codes:**
- **200 OK**: Application is running
- **503 Service Unavailable**: Application is not responding (timeout/crash)

**Characteristics:**
- ⚡ **Fast**: < 1ms response time
- 🔓 **No authentication required**
- 📊 **No database dependency**
- ✅ **Always returns 200** if process is alive

---

### 2. Readiness Check

**Endpoint**: `GET /api/v1/health/ready`

**Purpose**: Validate application is ready to serve traffic (database connectivity)

**Use Cases**:
- Kubernetes readiness probes
- Load balancer traffic routing
- Deployment health validation

**Implementation:**

```python
# backend/app/api/api_v1/endpoints/health.py
@router.get("/health/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """
    Readiness check - verifies database connectivity.

    Returns 200 only if the application can serve traffic.
    Used by: Kubernetes readiness probes, load balancers.
    """
    try:
        # Simple query to verify database connection
        await db.execute(text("SELECT 1"))
        return {
            "status": "ready",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "database": "disconnected",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
```

**Example Request:**

```bash
curl -X GET "http://localhost:8000/api/v1/health/ready"
```

**Success Response (200 OK):**

```json
{
  "status": "ready",
  "database": "connected",
  "timestamp": "2025-11-23T12:34:56.789012"
}
```

**Failure Response (503 Service Unavailable):**

```json
{
  "status": "not_ready",
  "database": "disconnected",
  "error": "Connection timeout",
  "timestamp": "2025-11-23T12:34:56.789012"
}
```

**Response Codes:**
- **200 OK**: Ready to serve traffic
- **503 Service Unavailable**: Not ready (database disconnected)

**Characteristics:**
- 🔌 **Tests database connectivity**
- 📦 **Validates dependencies**
- 🔓 **No authentication required**
- ⏱️ **Typical response**: 10-50ms

---

### 3. Detailed Health Check

**Endpoint**: `GET /api/v1/health/detailed`

**Purpose**: Component-level diagnostics for monitoring and debugging

**Use Cases**:
- Monitoring dashboards (Prometheus, Datadog, New Relic)
- AI agent health assessment
- Detailed troubleshooting
- Health status reporting

**Implementation:**

```python
# backend/app/api/api_v1/endpoints/health.py
@router.get("/health/detailed")
async def detailed_health(db: AsyncSession = Depends(get_db)):
    """
    Detailed health check - returns component-level status.

    Used by: Monitoring tools, debugging, dashboards.
    Returns 200 if all components healthy, 503 if any component unhealthy.
    """
    components = {}
    overall_healthy = True

    # Check database connectivity and version
    try:
        result = await db.execute(text("SELECT VERSION()"))
        db_version = result.scalar()
        components["database"] = {
            "status": "healthy",
            "version": db_version,
            "type": "MySQL"
        }
    except Exception as e:
        components["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_healthy = False

    # Future: Add more component checks here
    # - Cache connectivity (Redis, if added)
    # - External API availability
    # - File storage access
    # - Message queue status

    response_code = status.HTTP_200_OK if overall_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=response_code,
        content={
            "status": "healthy" if overall_healthy else "unhealthy",
            "components": components,
            "timestamp": datetime.utcnow().isoformat(),
            "version": "3.0.0"
        }
    )
```

**Example Request:**

```bash
curl -X GET "http://localhost:8000/api/v1/health/detailed"
```

**Success Response (200 OK):**

```json
{
  "status": "healthy",
  "components": {
    "database": {
      "status": "healthy",
      "version": "8.0.32-0ubuntu0.20.04.2",
      "type": "MySQL"
    }
  },
  "timestamp": "2025-11-23T12:34:56.789012",
  "version": "3.0.0"
}
```

**Failure Response (503 Service Unavailable):**

```json
{
  "status": "unhealthy",
  "components": {
    "database": {
      "status": "unhealthy",
      "error": "Can't connect to MySQL server on 'mysql' ([Errno 111] Connection refused)"
    }
  },
  "timestamp": "2025-11-23T12:34:56.789012",
  "version": "3.0.0"
}
```

**Response Codes:**
- **200 OK**: All components healthy
- **503 Service Unavailable**: One or more components unhealthy

**Characteristics:**
- 📊 **Component-level diagnostics**
- 🔍 **Detailed error information**
- 📈 **Includes version info**
- 🔓 **No authentication required**
- ⏱️ **Typical response**: 20-100ms

---

## Kubernetes Integration

### Liveness Probe Configuration

**Purpose**: Restart pod if application is unresponsive

```yaml
# k8s/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: chores-api
spec:
  template:
    spec:
      containers:
      - name: api
        image: your-registry/chores-api:latest
        ports:
        - containerPort: 8000
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
            scheme: HTTP
          initialDelaySeconds: 30    # Wait 30s before first check
          periodSeconds: 10           # Check every 10s
          timeoutSeconds: 5           # Timeout after 5s
          successThreshold: 1         # 1 success = healthy
          failureThreshold: 3         # 3 failures = restart pod
```

**Behavior:**
- Kubernetes checks `/health` every 10 seconds
- If 3 consecutive failures, pod is restarted
- Uses basic liveness check (no dependencies)

### Readiness Probe Configuration

**Purpose**: Remove pod from load balancer if not ready to serve traffic

```yaml
# k8s/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: chores-api
spec:
  template:
    spec:
      containers:
      - name: api
        image: your-registry/chores-api:latest
        ports:
        - containerPort: 8000
        readinessProbe:
          httpGet:
            path: /api/v1/health/ready
            port: 8000
            scheme: HTTP
          initialDelaySeconds: 15    # Wait 15s before first check
          periodSeconds: 5            # Check every 5s
          timeoutSeconds: 3           # Timeout after 3s
          successThreshold: 1         # 1 success = ready
          failureThreshold: 3         # 3 failures = not ready
```

**Behavior:**
- Kubernetes checks `/api/v1/health/ready` every 5 seconds
- If 3 consecutive failures, pod is removed from service endpoints
- Uses readiness check (validates database connectivity)

### Combined Configuration Example

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: chores-api
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: chores-api
  template:
    metadata:
      labels:
        app: chores-api
    spec:
      containers:
      - name: api
        image: your-ecr-registry/chores-api:v3.0.0
        ports:
        - containerPort: 8000
          name: http
          protocol: TCP
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: chores-db-secret
              key: url
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: chores-secret
              key: jwt-secret

        # Liveness Probe - restart if unresponsive
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
            scheme: HTTP
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          successThreshold: 1
          failureThreshold: 3

        # Readiness Probe - remove from service if not ready
        readinessProbe:
          httpGet:
            path: /api/v1/health/ready
            port: 8000
            scheme: HTTP
          initialDelaySeconds: 15
          periodSeconds: 5
          timeoutSeconds: 3
          successThreshold: 1
          failureThreshold: 3

        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

### Startup Probe (Optional)

For slow-starting applications, use a startup probe:

```yaml
startupProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 0
  periodSeconds: 5
  timeoutSeconds: 3
  successThreshold: 1
  failureThreshold: 30      # 30 * 5s = 150s max startup time
```

---

## Monitoring System Integration

### Prometheus Integration

**Metrics Endpoint**: `GET /metrics`

The API exposes Prometheus metrics at `/metrics` (IP-restricted for security).

**Prometheus Configuration:**

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'chores-api'
    scrape_interval: 15s
    metrics_path: '/metrics'
    static_configs:
      - targets: ['chores-api:8000']
    metric_relabel_configs:
      - source_labels: [__name__]
        regex: 'http_.*|chores_.*|user_.*|family_.*'
        action: keep
```

**Health Check Monitoring:**

```yaml
# prometheus-alerts.yml
groups:
  - name: chores_api_health
    interval: 30s
    rules:
      # Alert if API is down
      - alert: ChoresAPIDown
        expr: up{job="chores-api"} == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Chores API is down"
          description: "API has been unreachable for 2 minutes"

      # Alert if database connectivity fails
      - alert: ChoresAPIDatabaseUnhealthy
        expr: probe_success{job="chores-api-health"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Chores API database connectivity issue"
          description: "API readiness check failing for 1 minute"
```

**Blackbox Exporter Configuration:**

```yaml
# blackbox-exporter.yml
modules:
  http_2xx:
    prober: http
    timeout: 5s
    http:
      valid_status_codes: [200]
      method: GET

  http_health_detailed:
    prober: http
    timeout: 10s
    http:
      valid_status_codes: [200]
      method: GET
      fail_if_body_not_matches_regexp:
        - '"status":\s*"healthy"'
```

**Prometheus Scrape for Health:**

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'chores-api-health'
    metrics_path: /probe
    params:
      module: [http_health_detailed]
    static_configs:
      - targets:
        - http://chores-api:8000/api/v1/health/detailed
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: blackbox-exporter:9115
```

### Datadog Integration

**Agent Configuration:**

```yaml
# datadog-agent.yaml
init_config:

instances:
  - url: http://chores-api:8000/api/v1/health/detailed
    name: chores_api_health
    timeout: 10
    method: GET
    content_match: '"status":\s*"healthy"'
    http_response_status_code: "200"
    tags:
      - service:chores-api
      - env:production
    check_certificate_expiration: false
```

**Custom Check Script:**

```python
# datadog_checks/chores_health.py
from datadog_checks.base import AgentCheck
import requests

class ChoresHealthCheck(AgentCheck):
    def check(self, instance):
        url = instance.get('url', 'http://localhost:8000/api/v1/health/detailed')

        try:
            response = requests.get(url, timeout=10)
            health_data = response.json()

            # Overall health status
            if health_data['status'] == 'healthy':
                self.service_check('chores.api.health', AgentCheck.OK)
            else:
                self.service_check('chores.api.health', AgentCheck.CRITICAL)

            # Database component
            db_status = health_data['components']['database']['status']
            if db_status == 'healthy':
                self.service_check('chores.database.health', AgentCheck.OK)
            else:
                self.service_check('chores.database.health', AgentCheck.CRITICAL)

            # Emit metrics
            self.gauge('chores.health.check.duration', response.elapsed.total_seconds())

        except Exception as e:
            self.service_check('chores.api.health', AgentCheck.CRITICAL, message=str(e))
```

### New Relic Integration

**Synthetics Monitor:**

```javascript
// New Relic Synthetics Script
const assert = require('assert');

$http.get('http://chores-api:8000/api/v1/health/detailed', {
  headers: {
    'User-Agent': 'NewRelic-Synthetics'
  }
}, function(err, response, body) {
  assert.equal(response.statusCode, 200, 'Expected status code 200');

  const health = JSON.parse(body);
  assert.equal(health.status, 'healthy', 'Expected healthy status');

  // Check database component
  assert.equal(
    health.components.database.status,
    'healthy',
    'Expected database to be healthy'
  );

  console.log('Health check passed:', health);
});
```

### Grafana Dashboard

**Query Examples:**

```promql
# API uptime percentage (last 24h)
avg_over_time(up{job="chores-api"}[24h]) * 100

# Health check response time (p95)
histogram_quantile(0.95,
  rate(http_request_duration_seconds_bucket{endpoint="/api/v1/health/ready"}[5m])
)

# Database health status
probe_success{job="chores-api-health"}

# Failed health checks per hour
sum(increase(http_requests_total{endpoint="/api/v1/health/ready",status="503"}[1h]))
```

---

## AI Agent Integration Patterns

### Pattern 1: Health Assessment Bot

**Use Case**: AI agent monitors health and reports issues

```python
import requests
from datetime import datetime

class ChoresHealthAgent:
    def __init__(self, api_url: str):
        self.api_url = api_url
        self.health_url = f"{api_url}/api/v1/health/detailed"

    def assess_health(self) -> dict:
        """Assess API health and return structured report."""
        try:
            response = requests.get(self.health_url, timeout=10)
            health_data = response.json()

            return {
                "timestamp": datetime.utcnow().isoformat(),
                "overall_status": health_data["status"],
                "api_version": health_data["version"],
                "components": self.analyze_components(health_data["components"]),
                "recommendation": self.get_recommendation(health_data)
            }
        except requests.exceptions.Timeout:
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "overall_status": "timeout",
                "error": "Health check timed out",
                "recommendation": "Check API availability and network connectivity"
            }
        except Exception as e:
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "overall_status": "error",
                "error": str(e),
                "recommendation": "API is unreachable. Check if service is running."
            }

    def analyze_components(self, components: dict) -> list:
        """Analyze individual component health."""
        issues = []
        for component, status in components.items():
            if status["status"] != "healthy":
                issues.append({
                    "component": component,
                    "status": status["status"],
                    "error": status.get("error", "Unknown error")
                })
        return issues

    def get_recommendation(self, health_data: dict) -> str:
        """Provide actionable recommendation."""
        if health_data["status"] == "healthy":
            return "All systems operational"

        db_status = health_data["components"].get("database", {})
        if db_status.get("status") != "healthy":
            return (
                "Database connectivity issue detected. "
                "Check database server status and connection settings."
            )

        return "System health degraded. Review component statuses."

# Usage
agent = ChoresHealthAgent("http://localhost:8000")
report = agent.assess_health()
print(report)
```

### Pattern 2: Automated Incident Response

```python
class IncidentResponseAgent:
    def __init__(self, api_url: str, alert_webhook: str):
        self.api_url = api_url
        self.alert_webhook = alert_webhook
        self.consecutive_failures = 0
        self.failure_threshold = 3

    def monitor_and_respond(self):
        """Monitor health and trigger incident response."""
        health_status = self.check_health()

        if health_status["status"] != "healthy":
            self.consecutive_failures += 1

            if self.consecutive_failures >= self.failure_threshold:
                self.trigger_incident(health_status)
        else:
            if self.consecutive_failures > 0:
                self.resolve_incident(health_status)
            self.consecutive_failures = 0

    def check_health(self) -> dict:
        """Check detailed health status."""
        try:
            response = requests.get(
                f"{self.api_url}/api/v1/health/detailed",
                timeout=10
            )
            return response.json()
        except:
            return {"status": "unreachable", "components": {}}

    def trigger_incident(self, health_status: dict):
        """Trigger incident alert."""
        incident = {
            "severity": "high",
            "title": "Chores API Health Check Failure",
            "description": self.format_incident_description(health_status),
            "timestamp": datetime.utcnow().isoformat(),
            "consecutive_failures": self.consecutive_failures
        }

        # Send to incident management system
        requests.post(self.alert_webhook, json=incident)

    def resolve_incident(self, health_status: dict):
        """Resolve incident when health restored."""
        resolution = {
            "severity": "info",
            "title": "Chores API Health Restored",
            "description": "API health checks passing",
            "timestamp": datetime.utcnow().isoformat()
        }

        requests.post(self.alert_webhook, json=resolution)

    def format_incident_description(self, health_status: dict) -> str:
        """Format detailed incident description."""
        components = health_status.get("components", {})
        issues = []

        for name, status in components.items():
            if status.get("status") != "healthy":
                issues.append(f"- {name}: {status.get('error', 'Unknown')}")

        return "\n".join([
            f"API health status: {health_status['status']}",
            "Component issues:",
            *issues
        ])
```

### Pattern 3: Predictive Health Monitoring

```python
from collections import deque
from statistics import mean

class PredictiveHealthAgent:
    def __init__(self, api_url: str, window_size: int = 10):
        self.api_url = api_url
        self.response_times = deque(maxlen=window_size)
        self.health_history = deque(maxlen=window_size)

    def collect_metrics(self):
        """Collect health metrics over time."""
        import time

        start = time.time()
        try:
            response = requests.get(
                f"{self.api_url}/api/v1/health/detailed",
                timeout=10
            )
            response_time = time.time() - start
            health_data = response.json()

            self.response_times.append(response_time)
            self.health_history.append(health_data["status"] == "healthy")

        except Exception as e:
            self.response_times.append(10.0)  # Timeout value
            self.health_history.append(False)

    def predict_degradation(self) -> dict:
        """Predict potential health degradation."""
        if len(self.response_times) < 5:
            return {"prediction": "insufficient_data"}

        avg_response_time = mean(self.response_times)
        health_rate = sum(self.health_history) / len(self.health_history)

        # Degradation indicators
        slow_response = avg_response_time > 1.0  # >1s average
        frequent_failures = health_rate < 0.8  # <80% success rate

        if slow_response and frequent_failures:
            return {
                "prediction": "critical",
                "message": "High likelihood of service degradation",
                "avg_response_time": avg_response_time,
                "health_rate": health_rate,
                "recommendation": "Investigate database performance and connection pool"
            }
        elif slow_response or frequent_failures:
            return {
                "prediction": "warning",
                "message": "Potential performance issues detected",
                "avg_response_time": avg_response_time,
                "health_rate": health_rate,
                "recommendation": "Monitor closely for degradation"
            }
        else:
            return {
                "prediction": "normal",
                "message": "Service operating normally",
                "avg_response_time": avg_response_time,
                "health_rate": health_rate
            }
```

---

## Response Formats

### Success Response Structure

**Basic Health (`/health`):**
```json
{
  "status": "ok",
  "timestamp": "2025-11-23T12:34:56.789012"
}
```

**Readiness (`/api/v1/health/ready`):**
```json
{
  "status": "ready",
  "database": "connected",
  "timestamp": "2025-11-23T12:34:56.789012"
}
```

**Detailed Health (`/api/v1/health/detailed`):**
```json
{
  "status": "healthy",
  "components": {
    "database": {
      "status": "healthy",
      "version": "8.0.32-0ubuntu0.20.04.2",
      "type": "MySQL"
    }
  },
  "timestamp": "2025-11-23T12:34:56.789012",
  "version": "3.0.0"
}
```

### Error Response Structure

**Readiness Failure:**
```json
{
  "status": "not_ready",
  "database": "disconnected",
  "error": "Can't connect to MySQL server on 'mysql' ([Errno 111] Connection refused)",
  "timestamp": "2025-11-23T12:34:56.789012"
}
```

**Detailed Health Failure:**
```json
{
  "status": "unhealthy",
  "components": {
    "database": {
      "status": "unhealthy",
      "error": "OperationalError: (2003, \"Can't connect to MySQL server on 'mysql' ([Errno 111] Connection refused)\")"
    }
  },
  "timestamp": "2025-11-23T12:34:56.789012",
  "version": "3.0.0"
}
```

---

## Alerting Strategies

### Severity Levels

| Severity | Condition | Action |
|----------|-----------|--------|
| **Critical** | Liveness check fails (3+ consecutive) | Page on-call engineer, restart pod |
| **High** | Readiness check fails (3+ consecutive) | Alert team, investigate database |
| **Medium** | Detailed health shows degraded component | Create ticket, monitor |
| **Low** | Slow response times (>1s) | Log for analysis |

### Alert Examples

**PagerDuty Integration:**

```python
def send_pagerduty_alert(health_status: dict):
    """Send critical alert to PagerDuty."""
    import requests

    payload = {
        "routing_key": "YOUR_PAGERDUTY_KEY",
        "event_action": "trigger",
        "payload": {
            "summary": "Chores API Health Check Failed",
            "severity": "critical",
            "source": "health-monitor",
            "custom_details": health_status
        }
    }

    requests.post(
        "https://events.pagerduty.com/v2/enqueue",
        json=payload
    )
```

**Slack Integration:**

```python
def send_slack_alert(health_status: dict, webhook_url: str):
    """Send health alert to Slack."""
    import requests

    color = "danger" if health_status["status"] != "healthy" else "good"

    message = {
        "attachments": [{
            "color": color,
            "title": "Chores API Health Alert",
            "fields": [
                {
                    "title": "Status",
                    "value": health_status["status"],
                    "short": True
                },
                {
                    "title": "Timestamp",
                    "value": health_status["timestamp"],
                    "short": True
                }
            ],
            "text": f"Components: {health_status.get('components', {})}"
        }]
    }

    requests.post(webhook_url, json=message)
```

---

## Troubleshooting Unhealthy States

### Database Connection Failures

**Symptoms:**
- Readiness check returns 503
- Error: "Can't connect to MySQL server"
- Detailed health shows database unhealthy

**Diagnostic Steps:**

```bash
# 1. Check if database pod is running
kubectl get pods -l app=mysql

# 2. Test database connectivity from API pod
kubectl exec -it <api-pod-name> -- bash
mysql -h mysql -u chores-user -p

# 3. Check database logs
kubectl logs <mysql-pod-name>

# 4. Verify database service
kubectl get svc mysql
kubectl describe svc mysql

# 5. Check environment variables
kubectl exec -it <api-pod-name> -- env | grep DATABASE
```

**Common Fixes:**

```bash
# Restart MySQL pod
kubectl delete pod <mysql-pod-name>

# Verify DATABASE_URL secret
kubectl get secret chores-db-secret -o yaml

# Check connection pool settings
# In backend/app/db/base.py, adjust pool_size and max_overflow
```

### Slow Response Times

**Symptoms:**
- Health checks take >1s
- Intermittent timeouts

**Diagnostic Steps:**

```bash
# Monitor response times
time curl http://localhost:8000/api/v1/health/detailed

# Check database query performance
kubectl exec -it <mysql-pod-name> -- mysql -u root -p
mysql> SHOW PROCESSLIST;
mysql> SHOW STATUS LIKE 'Threads_connected';
mysql> SHOW STATUS LIKE 'Slow_queries';

# Check pod resource usage
kubectl top pod <api-pod-name>
kubectl describe pod <api-pod-name>
```

**Common Fixes:**

```yaml
# Increase resource limits in deployment
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

### Pod Restart Loops

**Symptoms:**
- Liveness probe fails repeatedly
- Pod keeps restarting

**Diagnostic Steps:**

```bash
# Check pod events
kubectl describe pod <api-pod-name>

# Check pod logs (current)
kubectl logs <api-pod-name>

# Check previous pod logs
kubectl logs <api-pod-name> --previous

# Check liveness probe settings
kubectl get pod <api-pod-name> -o yaml
```

**Common Fixes:**

```yaml
# Increase initialDelaySeconds if app takes time to start
livenessProbe:
  initialDelaySeconds: 60  # Increase from 30

# Or add startup probe for slow-starting apps
startupProbe:
  httpGet:
    path: /health
    port: 8000
  failureThreshold: 30
  periodSeconds: 5
```

---

## Best Practices

### 1. Use Appropriate Health Checks

- **Liveness**: Use `/health` (no dependencies)
- **Readiness**: Use `/api/v1/health/ready` (database check)
- **Monitoring**: Use `/api/v1/health/detailed` (component diagnostics)

### 2. Configure Probe Timing Correctly

```yaml
# Recommended settings
livenessProbe:
  initialDelaySeconds: 30  # Time for app to start
  periodSeconds: 10         # Check frequency
  timeoutSeconds: 5         # Request timeout
  failureThreshold: 3       # Failures before restart

readinessProbe:
  initialDelaySeconds: 15  # Shorter than liveness
  periodSeconds: 5          # More frequent checks
  timeoutSeconds: 3         # Shorter timeout
  failureThreshold: 3       # Failures before unready
```

### 3. Monitor Health Trends

```python
# Track health check success rate
success_rate = (successful_checks / total_checks) * 100

# Alert if success rate < 95% over 5 minutes
if success_rate < 95:
    send_alert("Health check success rate below threshold")
```

### 4. Implement Health Check Caching

For high-frequency checks, consider caching:

```python
from functools import lru_cache
from datetime import datetime, timedelta

@lru_cache(maxsize=1)
def get_cached_health(timestamp: int):
    """Cache health check for 10 seconds."""
    # Actual health check logic
    return check_health()

def health_with_cache():
    # Round timestamp to 10-second intervals
    cache_key = int(datetime.utcnow().timestamp() / 10)
    return get_cached_health(cache_key)
```

### 5. Log Health Check Failures

```python
import logging

logger = logging.getLogger(__name__)

async def readiness_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "database": "disconnected", "error": str(e)}
        )
```

### 6. Test Health Checks Locally

```bash
# Test all health checks before deploying
./scripts/test-health-checks.sh

# Script contents:
#!/bin/bash
echo "Testing basic health..."
curl -f http://localhost:8000/health || exit 1

echo "Testing readiness..."
curl -f http://localhost:8000/api/v1/health/ready || exit 1

echo "Testing detailed health..."
curl -f http://localhost:8000/api/v1/health/detailed || exit 1

echo "All health checks passed!"
```

---

## Additional Resources

- **API Documentation**: http://localhost:8000/docs
- **Prometheus Metrics**: http://localhost:8000/metrics (IP-restricted)
- **Kubernetes Docs**: https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/

---

**Last Updated**: 2025-11-23
**API Version**: 3.0.0
