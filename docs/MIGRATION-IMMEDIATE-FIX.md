# IMMEDIATE FIX: Get Chores-Tracker Backend Running NOW

Your backend pods are stuck in a restart loop because migrations are hanging in the entrypoint. This guide will get you running in **5 minutes**.

## Current Status

```
❌ Pods stuck: "MySQL is up - executing migrations"
❌ Exit code 137 (SIGKILL from liveness probe timeout)
❌ Infinite restart loop
```

## Option 1: Deploy the Fixed Code (Recommended)

### Step 1: Build and Push New Image

```bash
# From project root
cd /Users/arisela/git/chores-tracker

# You'll handle the build - this is a reminder of what's changed:
# - migrate-entrypoint.sh (new file for migrations)
# - docker-entrypoint.sh (removed migration logic)
# - Dockerfile (includes both entrypoints)

# After you build and push the new image, update the production deployment
```

### Step 2: Run Migration Job Manually

```bash
# Create the migration job with the new image
# First, update the image tag in migration-job.yaml to match your new build

# Then create the job
kubectl create -f gitops-templates/base-apps/chores-tracker-backend/migration-job.yaml

# Watch migration progress
kubectl logs -n chores-tracker-backend job/chores-tracker-migration -f

# Wait for completion (should take 10-60 seconds)
kubectl get job -n chores-tracker-backend chores-tracker-migration
```

### Step 3: Deploy Updated Backend

```bash
# Update the deployment with the new image (no migration in entrypoint)
kubectl set image deployment/chores-tracker-backend \
  -n chores-tracker-backend \
  chores-tracker-backend=852893458518.dkr.ecr.us-east-2.amazonaws.com/chores-tracker:<NEW_TAG>

# Watch pods come up (should be fast now - ~30 seconds)
kubectl get pods -n chores-tracker-backend -w

# Verify health
kubectl get pods -n chores-tracker-backend
# Should show: 2/2 Running
```

## Option 2: Emergency Bypass (Temporary)

If you need the app running RIGHT NOW before building new images:

### Temporarily Disable Migration in Running Pods

```bash
# Scale down current deployment
kubectl scale deployment -n chores-tracker-backend chores-tracker-backend --replicas=0

# Run migration manually using a one-off pod
kubectl run -it --rm migration-manual \
  --image=852893458518.dkr.ecr.us-east-2.amazonaws.com/chores-tracker:5.9.0 \
  --namespace=chores-tracker-backend \
  --restart=Never \
  --env="DATABASE_URL=<YOUR_DATABASE_URL>" \
  -- /bin/sh -c "cd /app && python -m alembic -c /app/backend/alembic.ini upgrade head"

# Scale back up
kubectl scale deployment -n chores-tracker-backend chores-tracker-backend --replicas=2
```

The migration should complete this time since it's not being killed by the liveness probe.

## Verification

After either option:

```bash
# Check pods are running
kubectl get pods -n chores-tracker-backend
# Expected: 2/2 Running, no restarts

# Check application logs
kubectl logs -n chores-tracker-backend deployment/chores-tracker-backend

# Test health endpoint
kubectl port-forward -n chores-tracker-backend deployment/chores-tracker-backend 8000:8000
# Then visit: http://localhost:8000/health

# Or from inside cluster
kubectl run -it --rm curl \
  --image=curlimages/curl \
  --namespace=chores-tracker-backend \
  --restart=Never \
  -- curl -v http://chores-tracker-backend-service:8000/health
```

## What Changed

### Files Modified

1. **migrate-entrypoint.sh** (NEW)
   - Dedicated migration script
   - Better error handling
   - Verbose logging

2. **docker-entrypoint.sh** (UPDATED)
   - Removed migration logic
   - Faster startup (no migration blocking)

3. **Dockerfile** (UPDATED)
   - Includes both entrypoints

4. **GitOps Templates** (NEW)
   - `gitops-templates/base-apps/chores-tracker-backend/migration-job.yaml`
   - `gitops-templates/base-apps/chores-tracker-backend/deployment.yaml`
   - `gitops-templates/base-apps/chores-tracker-backend/service.yaml`
   - `gitops-templates/base-apps/chores-tracker-backend/configmap.yaml`

### Changes Summary

| Aspect | Before | After |
|--------|--------|-------|
| Migration location | Pod entrypoint | Kubernetes Job |
| Startup time | 60-90s (migration blocking) | 10-30s |
| Liveness delay | 90s | 30s |
| Migration failures | Infinite pod restarts | Job failure (no pod restart) |
| Manual control | Hard (need to exec into pod) | Easy (kubectl create job) |

## Next Steps

1. **Immediate**: Get pods running (use Option 1 or 2)
2. **Short-term**: Set up ArgoCD to use new GitOps templates
3. **Long-term**: Document migration procedures for team

## GitOps Integration

After deploying the fix, update your ArgoCD Application to use the new GitOps structure:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: chores-tracker-backend
  namespace: argocd
spec:
  source:
    path: gitops-templates/base-apps/chores-tracker-backend
    # ... rest of your config
```

ArgoCD will then:
1. Wave 0: Create ConfigMaps/Secrets
2. Wave 1: Run migration job (PreSync hook)
3. Wave 2: Deploy application

## Troubleshooting

### Migration Job Fails

```bash
# View logs
kubectl logs -n chores-tracker-backend job/chores-tracker-migration

# Common issues:
# - Database connectivity: Check DATABASE_URL secret
# - Schema conflicts: May need to stamp version manually
# - Timeout: Increase activeDeadlineSeconds in job spec

# Delete failed job and retry
kubectl delete job -n chores-tracker-backend chores-tracker-migration
kubectl create -f gitops-templates/base-apps/chores-tracker-backend/migration-job.yaml
```

### Pods Still Restarting

```bash
# Check if migration completed
kubectl get job -n chores-tracker-backend chores-tracker-migration

# Check database schema version
kubectl exec -n chores-tracker-backend mysql-client -- \
  mysql -h <RDS_ENDPOINT> -u chores_user -p'<PASSWORD>' chores_db \
  -e "SELECT * FROM alembic_version;"

# View pod logs
kubectl logs -n chores-tracker-backend deployment/chores-tracker-backend --tail=100

# Check for application errors (not migration issues)
kubectl describe pod -n chores-tracker-backend -l app=chores-tracker-backend
```

## Support

Full documentation: `docs/database-migrations.md`

Key commands reference:
```bash
# Migration job
kubectl get job -n chores-tracker-backend chores-tracker-migration
kubectl logs -n chores-tracker-backend job/chores-tracker-migration -f
kubectl delete job -n chores-tracker-backend chores-tracker-migration

# Backend deployment
kubectl get pods -n chores-tracker-backend
kubectl logs -n chores-tracker-backend deployment/chores-tracker-backend
kubectl describe deployment -n chores-tracker-backend chores-tracker-backend

# Database version
kubectl exec -n chores-tracker-backend mysql-client -- \
  mysql -h <RDS_ENDPOINT> -u chores_user -p'<PASSWORD>' chores_db \
  -e "SELECT * FROM alembic_version;"
```
