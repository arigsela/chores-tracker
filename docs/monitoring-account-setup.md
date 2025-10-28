# Monitoring Service Account Setup

## Quick Start

### 1. Create the Monitoring Account

```bash
cd /path/to/chores-tracker
docker-compose exec api python -m backend.app.scripts.create_monitoring_account
```

**Output:**
- Monitoring parent account credentials (username, password)
- 2 test child accounts
- 2 test chores for validation

**⚠️ IMPORTANT:** Save the displayed credentials immediately. They are shown only once.

---

### 2. Store Credentials Securely

**Option A: Environment Variables (Development)**

```bash
# Add to your .env file (NOT committed to git)
export CHORES_TRACKER_MONITORING_USERNAME="monitoring_agent"
export CHORES_TRACKER_MONITORING_PASSWORD="<password-from-setup>"
export CHORES_TRACKER_API_BASE_URL="http://localhost:8000"
```

**Option B: Secrets Manager (Production)**

```bash
# AWS Secrets Manager example
aws secretsmanager create-secret \
  --name chores-tracker/monitoring \
  --secret-string '{"username":"monitoring_agent","password":"<password>","api_url":"https://api.chores-tracker.com"}'
```

---

### 3. Test the Account

```bash
# Using the provided test script
python3 test_monitoring_auth.py
```

**Expected output:**
```
✅ Authentication: PASS
✅ /chores:         PASS
```

---

## What Gets Created

| Resource | Details |
|----------|---------|
| **Parent Account** | `monitoring_agent@healthcheck.local` with 32-char secure password |
| **Test Family** | Isolated "Monitoring & Health Checks" family |
| **Test Children** | 2 child accounts for testing child-role endpoints |
| **Test Chores** | 2 chores (1 fixed reward, 1 range reward) for functional testing |

---

## Using the Monitoring Account

### Health Check Endpoints (No Auth Required)

```bash
# Basic liveness
curl http://localhost:8000/api/v1/health

# Readiness with DB check
curl http://localhost:8000/api/v1/health/ready

# Detailed diagnostics
curl http://localhost:8000/api/v1/health/detailed
```

### Authenticated Endpoints (Monitoring Account Required)

```bash
# 1. Login
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/users/login \
  --data-urlencode "username=monitoring_agent" \
  --data-urlencode "password=<your-password>" \
  | jq -r '.access_token')

# 2. Test chore listing
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/chores
```

---

## Integration with AI Agent

For comprehensive instructions on integrating this monitoring account with your AI agent, see:

**[AI Agent Health Check Integration Guide](./ai-agent-health-check-integration.md)**

This guide includes:
- Complete Python client implementation
- Continuous monitoring script examples
- Error handling strategies
- Alerting configurations
- Security best practices

---

## Regenerating the Account

If credentials are lost or compromised:

```bash
# Run the setup script again
docker-compose exec api python -m backend.app.scripts.create_monitoring_account

# When prompted about existing account, type "yes" to recreate
```

The script will:
1. Delete existing monitoring account and family
2. Create fresh monitoring parent account with new password
3. Create new test children and chores
4. Display new credentials

---

## Troubleshooting

### Account Creation Fails

**Error:** `User 'monitoring_agent' already exists`

**Solution:** Run the script again and type "yes" when prompted to delete existing account

---

### Authentication Fails

**Error:** `401 Unauthorized`

**Possible causes:**
- Wrong password (credentials not saved correctly)
- Account was manually deleted from database
- Password contains special characters not properly escaped

**Solution:** Regenerate the account to get new credentials

---

### Cannot See Test Chores

**Error:** Authenticated but `/chores` returns empty array

**Possible cause:** Querying from wrong user context

**Solution:** Ensure you're using the monitoring_agent account, not a different user

---

## Security Notes

✅ **Isolated:** Monitoring account belongs to separate family (no production data access)
✅ **Read-Only:** In practice has read-only access (minimal write permissions)
✅ **Auditable:** All activities logged with `monitoring_agent` user ID
✅ **Secure Password:** 32-character cryptographically random password
✅ **Git-Ignored:** Credential files are excluded from version control

⚠️ **Never commit credentials to git**
⚠️ **Rotate credentials every 90 days**
⚠️ **Use HTTPS in production**
⚠️ **Monitor monitoring account activity**

---

## Files Created by Setup

```
backend/app/scripts/create_monitoring_account.py  # Setup script
docs/ai-agent-health-check-integration.md        # Integration guide
docs/monitoring-account-setup.md                 # This file
test_monitoring_auth.py                          # Test script (temp file)
.gitignore                                       # Updated with credential patterns
```

---

## Related Documentation

- [Health Check Endpoints](./health-check-endpoints.md)
- [AI Agent Integration Guide](./ai-agent-health-check-integration.md)
- [API Documentation](http://localhost:8000/docs)
- [Architecture Overview](../README.md)

---

**Last Updated:** October 28, 2025
**Maintained By:** DevOps Team
