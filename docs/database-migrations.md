# Database Migration Guide

This document explains the database migration system for the Chores Tracker application.

## Overview

Database migrations are now handled separately from the application deployment using Kubernetes Jobs. This provides better control, observability, and reliability compared to running migrations in the application's startup script.

## Architecture

### Migration Job Pattern

**Benefits:**
- ✅ Migrations run once, not on every pod start
- ✅ Failed migrations don't cause application restart loops
- ✅ Better observability with dedicated job logs
- ✅ Manual control when needed (e.g., after database restore)
- ✅ GitOps friendly with ArgoCD sync waves
- ✅ Faster application startup times

**Components:**
1. **migrate-entrypoint.sh** - Migration-specific entrypoint script
2. **docker-entrypoint.sh** - Main application entrypoint (no migration logic)
3. **Kubernetes Job** - Runs migrations before deployment
4. **ArgoCD Sync Waves** - Ensures proper ordering (migration → deployment)

## File Structure

```
chores-tracker/
├── migrate-entrypoint.sh           # Migration entrypoint
├── docker-entrypoint.sh            # Application entrypoint
├── Dockerfile                      # Includes both entrypoints
├── k8s-dev.yaml                   # Dev environment with migration job
└── gitops-templates/base-apps/chores-tracker-backend/
    ├── migration-job.yaml         # Production migration job
    ├── deployment.yaml            # Application deployment
    ├── service.yaml               # Service definition
    └── configmap.yaml            # Configuration
```

## How It Works

### Automatic Deployments

1. **GitOps triggers ArgoCD sync**
2. **Wave 0**: ConfigMaps and Secrets created
3. **Wave 1**: Migration Job runs
   - Waits for database connectivity
   - Shows current migration version
   - Runs `alembic upgrade head`
   - Verifies final state
   - Exits (job complete)
4. **Wave 2**: Application Deployment starts
   - No migration blocking
   - Fast startup (~10-30 seconds)
   - Health checks pass quickly

### ArgoCD Hook Configuration

The migration job uses these annotations:

```yaml
annotations:
  argocd.argoproj.io/sync-wave: "1"
  argocd.argoproj.io/hook: PreSync
  argocd.argoproj.io/hook-delete-policy: BeforeHookCreation
```

## Manual Migration Procedures

### Production Environment

#### Run Migration Manually

```bash
# Delete existing migration job if present
kubectl delete job -n chores-tracker-backend chores-tracker-migration

# Create new migration job
kubectl create -f gitops-templates/base-apps/chores-tracker-backend/migration-job.yaml

# Watch migration logs in real-time
kubectl logs -n chores-tracker-backend job/chores-tracker-migration -f

# Check job status
kubectl get job -n chores-tracker-backend chores-tracker-migration

# Check migration completion
kubectl get job -n chores-tracker-backend chores-tracker-migration -o jsonpath='{.status.conditions[?(@.type=="Complete")].status}'
```

#### After Database Restore

When you restore a database backup, you may need to manually run migrations:

```bash
# 1. Stop the backend deployment temporarily (optional but recommended)
kubectl scale deployment -n chores-tracker-backend chores-tracker-backend --replicas=0

# 2. Delete any existing migration job
kubectl delete job -n chores-tracker-backend chores-tracker-migration

# 3. Run migration job
kubectl create -f gitops-templates/base-apps/chores-tracker-backend/migration-job.yaml

# 4. Watch logs to ensure success
kubectl logs -n chores-tracker-backend job/chores-tracker-migration -f

# 5. Verify migration completed successfully
kubectl get job -n chores-tracker-backend chores-tracker-migration

# 6. Scale backend deployment back up
kubectl scale deployment -n chores-tracker-backend chores-tracker-backend --replicas=2
```

#### Troubleshoot Failed Migration

```bash
# View migration job logs
kubectl logs -n chores-tracker-backend job/chores-tracker-migration

# Get job events
kubectl describe job -n chores-tracker-backend chores-tracker-migration

# Check pod status
kubectl get pods -n chores-tracker-backend -l component=migration

# Get pod logs with previous attempt if job restarted
kubectl logs -n chores-tracker-backend -l component=migration --previous

# Manual database inspection
kubectl exec -it -n chores-tracker-backend mysql-client -- \
  mysql -h <RDS_ENDPOINT> -u chores_user -p'<PASSWORD>' chores_db \
  -e "SELECT * FROM alembic_version;"

# Delete failed job and retry
kubectl delete job -n chores-tracker-backend chores-tracker-migration
kubectl create -f gitops-templates/base-apps/chores-tracker-backend/migration-job.yaml
```

### Development Environment

#### Local Kubernetes (Tilt)

```bash
# Tilt automatically handles migrations via k8s-dev.yaml

# View migration job logs
kubectl logs -n chores-dev job/chores-tracker-migration -f

# Manually trigger migration
kubectl delete job -n chores-dev chores-tracker-migration
kubectl apply -f k8s-dev.yaml

# Check migration status
kubectl get job -n chores-dev chores-tracker-migration
```

#### Docker Compose

For Docker Compose, migrations still run in the entrypoint (legacy behavior):

```bash
# Migrations run automatically on container start
docker compose up -d

# View migration logs
docker compose logs api

# Manual migration inside container
docker compose exec api python -m alembic -c /app/backend/alembic.ini upgrade head

# Check current migration version
docker compose exec api python -m alembic -c /app/backend/alembic.ini current
```

## Creating New Migrations

### 1. Create Migration File

```bash
# From project root
docker compose exec api python -m alembic -c /app/backend/alembic.ini revision --autogenerate -m "description_of_changes"

# Or locally if you have environment set up
python -m alembic -c backend/alembic.ini revision --autogenerate -m "description_of_changes"
```

### 2. Review Generated Migration

```bash
# Check the generated file in backend/alembic/versions/
ls -lt backend/alembic/versions/

# Review the migration code
cat backend/alembic/versions/<revision_id>_description_of_changes.py
```

### 3. Test Migration

```bash
# Test locally with Docker Compose
docker compose down
docker compose up -d

# Or with Tilt/K8s
kubectl delete job -n chores-dev chores-tracker-migration
kubectl apply -f k8s-dev.yaml
```

### 4. Commit and Push

```bash
git add backend/alembic/versions/<new_migration>.py
git commit -m "feat: add database migration for <feature>"
git push
```

### 5. Deploy to Production

The migration will automatically run via ArgoCD:
- CI/CD builds new Docker image
- ArgoCD detects new image
- Sync wave 1: Migration job runs
- Sync wave 2: Application deployment updates

## Migration Best Practices

### DO:
- ✅ Test migrations locally before deploying
- ✅ Review auto-generated migrations for correctness
- ✅ Use `alembic downgrade` to test rollback in dev
- ✅ Monitor migration job logs in production
- ✅ Keep migrations small and focused
- ✅ Add indexes for foreign keys

### DON'T:
- ❌ Edit old migration files (create new ones instead)
- ❌ Run migrations directly on production database manually
- ❌ Delete migration files from version history
- ❌ Modify database schema without creating migration
- ❌ Ignore migration job failures

## Monitoring and Observability

### Check Migration Status

```bash
# Kubernetes
kubectl get jobs -n chores-tracker-backend -l component=migration
kubectl logs -n chores-tracker-backend -l component=migration --tail=100

# Database
kubectl exec -n chores-tracker-backend mysql-client -- \
  mysql -h <RDS_ENDPOINT> -u chores_user -p'<PASSWORD>' chores_db \
  -e "SELECT * FROM alembic_version;"
```

### Common Issues

#### Issue: Migration Job Stuck/Hanging

**Symptoms:**
- Job shows 0/1 completions
- Pod status: Running for extended time
- No logs output

**Solutions:**
```bash
# Check pod status
kubectl get pods -n chores-tracker-backend -l component=migration

# View pod events
kubectl describe pod -n chores-tracker-backend -l component=migration

# Check database connectivity
kubectl exec -n chores-tracker-backend mysql-client -- \
  nc -zv <RDS_ENDPOINT> 3306

# Delete and retry
kubectl delete job -n chores-tracker-backend chores-tracker-migration
kubectl create -f gitops-templates/base-apps/chores-tracker-backend/migration-job.yaml
```

#### Issue: Migration Conflicts After DB Restore

**Symptoms:**
- Alembic reports head mismatch
- Multiple heads detected
- Unknown revisions

**Solutions:**
```bash
# Check current database version
kubectl exec -n chores-tracker-backend mysql-client -- \
  mysql -h <RDS_ENDPOINT> -u chores_user -p'<PASSWORD>' chores_db \
  -e "SELECT * FROM alembic_version;"

# Check expected version from code
kubectl exec -n chores-tracker-backend -l app=chores-tracker-backend -- \
  python -m alembic -c /app/backend/alembic.ini heads

# Stamp database to specific version (CAREFUL!)
kubectl run -it --rm alembic-fix \
  --image=852893458518.dkr.ecr.us-east-2.amazonaws.com/chores-tracker:latest \
  --env DATABASE_URL=<YOUR_DATABASE_URL> \
  -- python -m alembic -c /app/backend/alembic.ini stamp head
```

## Reference

### Migration Job Configuration

Key settings in `migration-job.yaml`:

```yaml
spec:
  backoffLimit: 4              # Retry up to 4 times
  activeDeadlineSeconds: 300   # 5 minute timeout
  ttlSecondsAfterFinished: 86400  # Keep 24 hours

  template:
    spec:
      restartPolicy: OnFailure # Retry on failure
```

### Health Check Improvements

With migrations separated, health check delays are reduced:

**Before (with migration in entrypoint):**
- `initialDelaySeconds: 90` (liveness)
- `initialDelaySeconds: 60` (readiness)

**After (migration job pattern):**
- `initialDelaySeconds: 30` (liveness)
- `initialDelaySeconds: 10` (readiness)

This results in **~60 second faster startup** and quicker failure detection.

## Support

For issues or questions:
1. Check migration job logs: `kubectl logs -n chores-tracker-backend job/chores-tracker-migration`
2. Review database state: Check `alembic_version` table
3. Consult Alembic documentation: https://alembic.sqlalchemy.org/
4. Review application logs: `kubectl logs -n chores-tracker-backend deployment/chores-tracker-backend`
