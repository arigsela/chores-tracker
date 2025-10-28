# AI Agent Health Check Integration Guide

## Overview

This document provides comprehensive instructions for integrating health check monitoring into your AI agent repository. The chores-tracker application provides multi-layered health check endpoints and a dedicated monitoring service account for end-to-end testing.

---

## Table of Contents

1. [Health Check Architecture](#health-check-architecture)
2. [Setup Prerequisites](#setup-prerequisites)
3. [Monitoring Service Account](#monitoring-service-account)
4. [Health Check Endpoints](#health-check-endpoints)
5. [Implementation Guide](#implementation-guide)
6. [Example Workflows](#example-workflows)
7. [Error Handling](#error-handling)
8. [Security Best Practices](#security-best-practices)
9. [Alerting Strategy](#alerting-strategy)
10. [Troubleshooting](#troubleshooting)

---

## Health Check Architecture

The chores-tracker application implements a **three-tier health check architecture**:

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: Public Health Endpoints (No Authentication)        │
│ ───────────────────────────────────────────────────────────│
│ • GET /api/v1/health          → Basic liveness              │
│ • GET /api/v1/health/ready    → Database readiness          │
│ • GET /api/v1/health/detailed → Component diagnostics       │
├─────────────────────────────────────────────────────────────┤
│ Layer 2: Authentication Testing (Service Account)           │
│ ───────────────────────────────────────────────────────────│
│ • POST /api/v1/users/login    → JWT authentication test     │
│ • GET /api/v1/users/me        → Token validation test       │
├─────────────────────────────────────────────────────────────┤
│ Layer 3: Functional Testing (Service Account)               │
│ ───────────────────────────────────────────────────────────│
│ • GET /api/v1/chores          → Business logic test         │
│ • GET /api/v1/users/summary   → Data integrity test         │
│ • GET /api/v1/assignments     → End-to-end workflow test    │
└─────────────────────────────────────────────────────────────┘
```

### When to Use Each Layer

| Layer | Check Frequency | Use Case | Alert Priority |
|-------|----------------|----------|----------------|
| **Layer 1** | Every 30 seconds | Infrastructure monitoring | Critical |
| **Layer 2** | Every 2-5 minutes | Authentication system | High |
| **Layer 3** | Every 10-15 minutes | Business logic validation | Medium |

---

## Setup Prerequisites

### 1. Create Monitoring Service Account

On the chores-tracker server, run:

```bash
cd /path/to/chores-tracker
docker-compose exec api python -m backend.app.scripts.create_monitoring_account
```

**Output:**
```
🎉 MONITORING SERVICE ACCOUNT CREATED SUCCESSFULLY!

📌 PARENT ACCOUNT (Main Monitoring Account)
   Username: monitoring_agent
   Email:    monitoring@healthcheck.local
   Password: <32-character-secure-password>
   User ID:  XX
   Family:   Monitoring & Health Checks (ID: X)

📌 TEST CHILD ACCOUNTS
   Child 1: test_child_monitor_1 (ID: XX)
   Child 2: test_child_monitor_2 (ID: XX)
   Password (both): <16-character-password>

📌 TEST CHORES
   Chore 1: [TEST] Health Check Chore - Fixed Reward (ID: XX)
   Chore 2: [TEST] Health Check Chore - Range Reward (ID: XX)
```

**⚠️ IMPORTANT:** Save these credentials immediately. They are displayed only once.

### 2. Store Credentials Securely

**Recommended: Use a Secrets Manager**

```bash
# AWS Secrets Manager
aws secretsmanager create-secret \
  --name chores-tracker/monitoring \
  --secret-string '{
    "username": "monitoring_agent",
    "password": "<password-from-setup>",
    "api_base_url": "https://api.chores-tracker.com"
  }'

# Or environment variables (for development)
export CHORES_TRACKER_MONITORING_USERNAME="monitoring_agent"
export CHORES_TRACKER_MONITORING_PASSWORD="<password>"
export CHORES_TRACKER_API_BASE_URL="https://api.chores-tracker.com"
```

---

## Monitoring Service Account

### Account Details

| Property | Value |
|----------|-------|
| **Username** | `monitoring_agent` |
| **Email** | `monitoring@healthcheck.local` |
| **Role** | Parent (read access to most endpoints) |
| **Family** | Dedicated monitoring family (isolated) |
| **Permissions** | Read-only in practice, minimal write access |
| **Purpose** | Health checks, functional testing, synthetic monitoring |

### Test Data Available

The monitoring account has access to:
- **2 test child accounts** for child-role endpoint testing
- **2 test chores** (1 fixed reward, 1 range reward) for chore workflow testing
- **Isolated family** that doesn't interfere with production data

### Security Characteristics

✅ **Isolated:** Belongs to separate family, no access to production data
✅ **Minimal Permissions:** Read-only access to test data
✅ **Auditable:** All activities logged with `monitoring_agent` user ID
✅ **Renewable:** Can be regenerated by re-running setup script
✅ **Secure Credentials:** 32-character cryptographically secure password

---

## Health Check Endpoints

### 1. Basic Liveness Check

**Endpoint:** `GET /api/v1/health`

**Purpose:** Verify application process is running

**Authentication:** None required

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2025-10-28T16:06:24.025332"
}
```

**Success Criteria:** HTTP 200 status code

**Frequency:** Every 30 seconds (Kubernetes liveness probe)

---

### 2. Readiness Check

**Endpoint:** `GET /api/v1/health/ready`

**Purpose:** Verify application can serve traffic (DB connected)

**Authentication:** None required

**Response (Healthy):**
```json
{
  "status": "ready",
  "database": "connected",
  "timestamp": "2025-10-28T16:06:24.680547"
}
```

**Response (Unhealthy):**
```json
{
  "status": "not_ready",
  "database": "disconnected",
  "error": "connection timeout",
  "timestamp": "2025-10-28T16:06:24.680547"
}
```

**Success Criteria:** HTTP 200 and `status === "ready"`

**Frequency:** Every 30 seconds (Kubernetes readiness probe)

---

### 3. Detailed Health Check

**Endpoint:** `GET /api/v1/health/detailed`

**Purpose:** Component-level diagnostics for debugging

**Authentication:** None required

**Response (Healthy):**
```json
{
  "status": "healthy",
  "components": {
    "database": {
      "status": "healthy",
      "version": "8.0.44",
      "type": "MySQL"
    }
  },
  "timestamp": "2025-10-28T16:06:25.325674",
  "version": "3.0.0"
}
```

**Response (Unhealthy):**
```json
{
  "status": "unhealthy",
  "components": {
    "database": {
      "status": "unhealthy",
      "error": "connection refused"
    }
  },
  "timestamp": "2025-10-28T16:06:25.325674",
  "version": "3.0.0"
}
```

**Success Criteria:** HTTP 200 and all components `status === "healthy"`

**Frequency:** Every 2-5 minutes (monitoring dashboard)

---

## Implementation Guide

### Technology Stack Recommendations

**Recommended: Python with `requests` or `httpx`**

```python
# requirements.txt
httpx>=0.25.0
python-dotenv>=1.0.0
```

**Alternative: Node.js with `axios`**

```javascript
// package.json
{
  "dependencies": {
    "axios": "^1.6.0",
    "dotenv": "^16.0.0"
  }
}
```

---

### Step 1: Configuration Module

**Python Example:**

```python
# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Health check monitoring configuration."""

    # API Configuration
    API_BASE_URL = os.getenv("CHORES_TRACKER_API_BASE_URL", "https://api.chores-tracker.com")

    # Monitoring Credentials
    MONITORING_USERNAME = os.getenv("CHORES_TRACKER_MONITORING_USERNAME")
    MONITORING_PASSWORD = os.getenv("CHORES_TRACKER_MONITORING_PASSWORD")

    # Check Intervals (seconds)
    LIVENESS_CHECK_INTERVAL = 30
    READINESS_CHECK_INTERVAL = 30
    DETAILED_CHECK_INTERVAL = 120
    AUTH_CHECK_INTERVAL = 120
    FUNCTIONAL_CHECK_INTERVAL = 300

    # Timeout Settings
    REQUEST_TIMEOUT = 10  # seconds

    # Retry Settings
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds

    # Alerting
    ALERT_WEBHOOK_URL = os.getenv("ALERT_WEBHOOK_URL")  # Slack/Teams/Discord

    @classmethod
    def validate(cls):
        """Validate required configuration."""
        if not cls.MONITORING_USERNAME or not cls.MONITORING_PASSWORD:
            raise ValueError(
                "Missing monitoring credentials. Set CHORES_TRACKER_MONITORING_USERNAME "
                "and CHORES_TRACKER_MONITORING_PASSWORD environment variables."
            )
```

---

### Step 2: Health Check Client

**Python Example:**

```python
# health_checker.py
import httpx
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HealthCheckClient:
    """Client for performing health checks on chores-tracker API."""

    def __init__(self):
        self.base_url = Config.API_BASE_URL
        self.username = Config.MONITORING_USERNAME
        self.password = Config.MONITORING_PASSWORD
        self.token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None

    def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Make HTTP request with error handling.

        Returns:
            Tuple of (success: bool, data: Optional[Dict], error: Optional[str])
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = httpx.request(
                method,
                url,
                timeout=Config.REQUEST_TIMEOUT,
                **kwargs
            )

            # Check if response is successful
            if 200 <= response.status_code < 300:
                try:
                    data = response.json()
                    return (True, data, None)
                except Exception:
                    # Non-JSON response but still successful
                    return (True, {"status_code": response.status_code}, None)
            else:
                error = f"HTTP {response.status_code}: {response.text}"
                return (False, None, error)

        except httpx.TimeoutException:
            return (False, None, "Request timeout")
        except httpx.ConnectError:
            return (False, None, "Connection failed")
        except Exception as e:
            return (False, None, str(e))

    def check_liveness(self) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """Check if application is alive."""
        logger.info("🔍 Checking liveness...")
        return self._make_request("GET", "/api/v1/health")

    def check_readiness(self) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """Check if application is ready to serve traffic."""
        logger.info("🔍 Checking readiness...")
        success, data, error = self._make_request("GET", "/api/v1/health/ready")

        if success and data:
            # Verify database is connected
            if data.get("status") != "ready" or data.get("database") != "connected":
                return (False, data, "Database not ready")

        return (success, data, error)

    def check_detailed_health(self) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """Get detailed component health status."""
        logger.info("🔍 Checking detailed health...")
        success, data, error = self._make_request("GET", "/api/v1/health/detailed")

        if success and data:
            # Verify all components are healthy
            if data.get("status") != "healthy":
                unhealthy_components = []
                for name, info in data.get("components", {}).items():
                    if info.get("status") != "healthy":
                        unhealthy_components.append(name)

                if unhealthy_components:
                    error = f"Unhealthy components: {', '.join(unhealthy_components)}"
                    return (False, data, error)

        return (success, data, error)

    def authenticate(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Authenticate and obtain JWT token.

        Returns:
            Tuple of (success: bool, token: Optional[str], error: Optional[str])
        """
        logger.info("🔐 Authenticating...")

        success, data, error = self._make_request(
            "POST",
            "/api/v1/users/login",
            data={
                "username": self.username,
                "password": self.password
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        if success and data:
            token = data.get("access_token")
            if token:
                self.token = token
                logger.info("✅ Authentication successful")
                return (True, token, None)
            else:
                return (False, None, "No access_token in response")

        return (False, None, error)

    def check_authenticated_endpoint(self) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """Test authenticated endpoint (users/me)."""
        logger.info("🔍 Checking authenticated endpoint...")

        # Ensure we have a token
        if not self.token:
            auth_success, _, auth_error = self.authenticate()
            if not auth_success:
                return (False, None, f"Authentication failed: {auth_error}")

        # Test /users/me endpoint
        success, data, error = self._make_request(
            "GET",
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {self.token}"}
        )

        if success and data:
            # Verify we got user data
            if data.get("username") == self.username:
                logger.info("✅ Authenticated endpoint working")
                return (True, data, None)
            else:
                return (False, data, "Unexpected user data")

        return (success, data, error)

    def check_functional_endpoint(self) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """Test functional business logic (list chores)."""
        logger.info("🔍 Checking functional endpoint...")

        # Ensure we have a token
        if not self.token:
            auth_success, _, auth_error = self.authenticate()
            if not auth_success:
                return (False, None, f"Authentication failed: {auth_error}")

        # Test /chores endpoint
        success, data, error = self._make_request(
            "GET",
            "/api/v1/chores",
            headers={"Authorization": f"Bearer {self.token}"}
        )

        if success and data:
            # Verify we got chore data (should have test chores)
            if isinstance(data, list) and len(data) >= 2:
                # Check for test chores
                test_chores = [c for c in data if c.get("title", "").startswith("[TEST]")]
                if len(test_chores) >= 2:
                    logger.info(f"✅ Functional endpoint working ({len(data)} chores, {len(test_chores)} test chores)")
                    return (True, data, None)
                else:
                    return (False, data, f"Expected at least 2 test chores, found {len(test_chores)}")
            else:
                return (False, data, "Unexpected chore data structure")

        return (success, data, error)

    def run_all_checks(self) -> Dict[str, Dict]:
        """
        Run all health checks and return comprehensive status.

        Returns:
            Dict with check results:
            {
                "liveness": {"success": bool, "data": dict, "error": str},
                "readiness": {"success": bool, "data": dict, "error": str},
                ...
            }
        """
        results = {}

        # Layer 1: Public health checks
        success, data, error = self.check_liveness()
        results["liveness"] = {"success": success, "data": data, "error": error}

        success, data, error = self.check_readiness()
        results["readiness"] = {"success": success, "data": data, "error": error}

        success, data, error = self.check_detailed_health()
        results["detailed"] = {"success": success, "data": data, "error": error}

        # Layer 2: Authentication checks
        success, token, error = self.authenticate()
        results["authentication"] = {"success": success, "token": token, "error": error}

        # Only continue if authentication succeeded
        if success:
            # Layer 3: Functional checks
            success, data, error = self.check_authenticated_endpoint()
            results["authenticated_endpoint"] = {"success": success, "data": data, "error": error}

            success, data, error = self.check_functional_endpoint()
            results["functional_endpoint"] = {"success": success, "data": data, "error": error}
        else:
            results["authenticated_endpoint"] = {"success": False, "data": None, "error": "Skipped due to auth failure"}
            results["functional_endpoint"] = {"success": False, "data": None, "error": "Skipped due to auth failure"}

        return results


# Example usage
if __name__ == "__main__":
    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        logger.error(f"❌ Configuration error: {e}")
        exit(1)

    # Run health checks
    client = HealthCheckClient()
    results = client.run_all_checks()

    # Print results
    print("\n" + "=" * 70)
    print("HEALTH CHECK RESULTS")
    print("=" * 70)

    all_passed = True
    for check_name, result in results.items():
        status_icon = "✅" if result["success"] else "❌"
        print(f"{status_icon} {check_name}: {'PASS' if result['success'] else 'FAIL'}")
        if result["error"]:
            print(f"   Error: {result['error']}")
        all_passed = all_passed and result["success"]

    print("=" * 70)

    if all_passed:
        print("🎉 All health checks passed!")
        exit(0)
    else:
        print("⚠️  Some health checks failed!")
        exit(1)
```

---

### Step 3: Continuous Monitoring Script

**Python Example:**

```python
# monitor.py
import time
import logging
from datetime import datetime
from health_checker import HealthCheckClient
from config import Config
from alerting import send_alert  # Implement your alerting logic

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ContinuousMonitor:
    """Continuous health monitoring with scheduled checks."""

    def __init__(self):
        self.client = HealthCheckClient()
        self.failure_counts = {
            "liveness": 0,
            "readiness": 0,
            "authentication": 0,
            "functional": 0
        }
        self.max_failures_before_alert = 3

    def monitor_liveness(self):
        """Monitor liveness every 30 seconds."""
        success, data, error = self.client.check_liveness()

        if not success:
            self.failure_counts["liveness"] += 1
            logger.error(f"❌ Liveness check failed: {error}")

            if self.failure_counts["liveness"] >= self.max_failures_before_alert:
                send_alert(
                    severity="critical",
                    title="Chores-Tracker Application Down",
                    message=f"Liveness check has failed {self.failure_counts['liveness']} times. Error: {error}"
                )
        else:
            if self.failure_counts["liveness"] > 0:
                send_alert(
                    severity="info",
                    title="Chores-Tracker Application Recovered",
                    message="Liveness check is now passing"
                )
            self.failure_counts["liveness"] = 0

    def monitor_readiness(self):
        """Monitor readiness every 30 seconds."""
        success, data, error = self.client.check_readiness()

        if not success:
            self.failure_counts["readiness"] += 1
            logger.error(f"❌ Readiness check failed: {error}")

            if self.failure_counts["readiness"] >= self.max_failures_before_alert:
                send_alert(
                    severity="critical",
                    title="Chores-Tracker Database Unavailable",
                    message=f"Readiness check has failed {self.failure_counts['readiness']} times. Error: {error}"
                )
        else:
            if self.failure_counts["readiness"] > 0:
                send_alert(
                    severity="info",
                    title="Chores-Tracker Database Recovered",
                    message="Readiness check is now passing"
                )
            self.failure_counts["readiness"] = 0

    def monitor_authentication(self):
        """Monitor authentication every 2 minutes."""
        success, token, error = self.client.authenticate()

        if not success:
            self.failure_counts["authentication"] += 1
            logger.error(f"❌ Authentication check failed: {error}")

            if self.failure_counts["authentication"] >= 2:  # Alert after 2 failures (4 min)
                send_alert(
                    severity="high",
                    title="Chores-Tracker Authentication System Failure",
                    message=f"Authentication has failed {self.failure_counts['authentication']} times. Error: {error}"
                )
        else:
            if self.failure_counts["authentication"] > 0:
                send_alert(
                    severity="info",
                    title="Chores-Tracker Authentication Recovered",
                    message="Authentication is now working"
                )
            self.failure_counts["authentication"] = 0

    def monitor_functional(self):
        """Monitor functional endpoints every 5 minutes."""
        success, data, error = self.client.check_functional_endpoint()

        if not success:
            self.failure_counts["functional"] += 1
            logger.error(f"❌ Functional check failed: {error}")

            if self.failure_counts["functional"] >= 2:  # Alert after 2 failures (10 min)
                send_alert(
                    severity="medium",
                    title="Chores-Tracker Business Logic Failure",
                    message=f"Functional checks have failed {self.failure_counts['functional']} times. Error: {error}"
                )
        else:
            if self.failure_counts["functional"] > 0:
                send_alert(
                    severity="info",
                    title="Chores-Tracker Business Logic Recovered",
                    message="Functional checks are now passing"
                )
            self.failure_counts["functional"] = 0

    def run(self):
        """Run continuous monitoring loop."""
        logger.info("🚀 Starting continuous monitoring...")

        last_liveness = 0
        last_readiness = 0
        last_detailed = 0
        last_auth = 0
        last_functional = 0

        while True:
            current_time = time.time()

            # Liveness check every 30 seconds
            if current_time - last_liveness >= Config.LIVENESS_CHECK_INTERVAL:
                self.monitor_liveness()
                last_liveness = current_time

            # Readiness check every 30 seconds
            if current_time - last_readiness >= Config.READINESS_CHECK_INTERVAL:
                self.monitor_readiness()
                last_readiness = current_time

            # Authentication check every 2 minutes
            if current_time - last_auth >= Config.AUTH_CHECK_INTERVAL:
                self.monitor_authentication()
                last_auth = current_time

            # Functional check every 5 minutes
            if current_time - last_functional >= Config.FUNCTIONAL_CHECK_INTERVAL:
                self.monitor_functional()
                last_functional = current_time

            # Sleep for 5 seconds before next iteration
            time.sleep(5)


if __name__ == "__main__":
    try:
        Config.validate()
        monitor = ContinuousMonitor()
        monitor.run()
    except KeyboardInterrupt:
        logger.info("🛑 Monitoring stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        exit(1)
```

---

## Example Workflows

### Quick Health Check

```bash
# Set environment variables
export CHORES_TRACKER_API_BASE_URL="https://api.chores-tracker.com"
export CHORES_TRACKER_MONITORING_USERNAME="monitoring_agent"
export CHORES_TRACKER_MONITORING_PASSWORD="<your-password>"

# Run one-time health check
python health_checker.py
```

### Continuous Monitoring

```bash
# Run continuous monitoring (foreground)
python monitor.py

# Run as background service (Linux)
nohup python monitor.py > monitoring.log 2>&1 &

# Run as systemd service
sudo systemctl start chores-tracker-monitor
```

---

## Error Handling

### Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `Connection failed` | API server unreachable | Check network, verify API URL |
| `Request timeout` | API responding slowly | Increase timeout, check server load |
| `HTTP 401: Unauthorized` | Invalid credentials | Verify username/password, regenerate account |
| `HTTP 503: Service Unavailable` | Database down | Check MySQL status, connection pool |
| `No access_token in response` | Login endpoint malfunction | Check API logs, verify auth middleware |
| `Database not ready` | MySQL connection failed | Check MySQL container, connection string |

---

## Security Best Practices

1. **Never hardcode credentials** - Use environment variables or secrets manager
2. **Rotate credentials regularly** - Regenerate monitoring account every 90 days
3. **Use HTTPS** - Always use secure connections to the API
4. **Limit token lifetime** - JWT tokens expire after 8 days
5. **Monitor monitoring** - Set up alerts if health checks stop running
6. **Audit logs** - Review monitoring account activities periodically
7. **Isolate monitoring** - Run monitoring from separate infrastructure

---

## Alerting Strategy

### Alert Severity Levels

| Severity | Trigger | Response Time | Examples |
|----------|---------|---------------|----------|
| **Critical** | 3+ failures, user-impacting | Immediate (< 5 min) | App down, database unavailable |
| **High** | 2+ failures, degraded service | Quick (< 15 min) | Auth failing, slow responses |
| **Medium** | 2+ failures, limited impact | Standard (< 1 hour) | Business logic errors |
| **Low** | Warnings, informational | Review next day | High latency, deprecated endpoints |

### Alert Channels

- **Slack/Teams/Discord:** Real-time notifications
- **PagerDuty/OpsGenie:** On-call escalation for critical alerts
- **Email:** Summary reports, non-urgent issues
- **Dashboard:** Grafana/DataDog for historical trends

---

## Troubleshooting

### Health Checks Failing but App Works

**Possible Causes:**
- Monitoring agent network issues
- Firewall blocking monitoring traffic
- Rate limiting on health endpoints

**Solution:**
1. Verify network connectivity: `curl https://api.chores-tracker.com/api/v1/health`
2. Check firewall rules for monitoring agent IP
3. Verify rate limits aren't blocking health endpoints

### Authentication Failing

**Possible Causes:**
- Password changed or account deleted
- JWT secret rotated
- Token expired

**Solution:**
1. Regenerate monitoring account: `python create_monitoring_account.py`
2. Update credentials in secrets manager
3. Restart monitoring agent

### False Positive Alerts

**Possible Causes:**
- Timeout too low
- Network latency spikes
- Server load spikes

**Solution:**
1. Increase timeout values in config
2. Adjust failure threshold before alerting
3. Add retry logic with exponential backoff

---

## Additional Resources

- **API Documentation:** https://api.chores-tracker.com/docs
- **GitHub Repository:** https://github.com/arigsela/chores-tracker
- **Architecture Docs:** `/docs/architecture.md` (chores-tracker repo)
- **OpenAPI Spec:** https://api.chores-tracker.com/openapi.json

---

## Support

For issues with health check integration:
1. Check troubleshooting section above
2. Review API logs: `docker-compose logs api -f`
3. Verify monitoring account: `docker-compose exec api python -m backend.app.scripts.list_users`
4. Contact: your-email@example.com

---

**Document Version:** 1.0
**Last Updated:** October 28, 2025
**Maintained By:** DevOps Team
