# Environment Setup Guide

This document explains how to configure the Chores Tracker application for different environments.

## Environment Configuration

The application uses environment variables to determine its configuration. These can be set through:
1. A `.env` file in the project root
2. Docker Compose environment variables
3. Kubernetes ConfigMaps and Secrets

## Local Development

For local development, you have two options:

### Option 1: SQLite (Simplest)

1. Create a `.env` file based on `.env.sample`:
   ```
   ENVIRONMENT=development
   DEBUG=True
   DATABASE_URL=sqlite+aiosqlite:///./chores_tracker.db
   SECRET_KEY=dev_secret_key
   BACKEND_CORS_ORIGINS="http://localhost:3000,http://localhost:8000"
   ```

2. Run with docker-compose:
   ```bash
   docker-compose up
   ```

### Option 2: MySQL (Production-like)

If you want to test with MySQL locally, you'll need to:

1. Uncomment the MySQL service in docker-compose.yml 
2. Update your `.env` file with MySQL configuration:
   ```
   ENVIRONMENT=development
   DEBUG=True
   DATABASE_URL=mysql+aiomysql://chores_user:chores_password@mysql:3306/chores_tracker
   SECRET_KEY=dev_secret_key
   BACKEND_CORS_ORIGINS="http://localhost:3000,http://localhost:8000"
   ```

3. Run with docker-compose:
   ```bash
   docker-compose up
   ```

## Production Deployment

For production deployment to Kubernetes:

1. Build the container image with production settings:
   ```bash
   docker build -t your-registry/chores-tracker:latest .
   docker push your-registry/chores-tracker:latest
   ```

2. In your GitOps Kubernetes repository, configure:

   - **ConfigMap** for non-sensitive configuration:
     ```yaml
     apiVersion: v1
     kind: ConfigMap
     metadata:
       name: chores-tracker-config
     data:
       ENVIRONMENT: "production"
       DEBUG: "False"
       BACKEND_CORS_ORIGINS: "https://your-production-domain.com"
     ```

   - **Secret** for sensitive configuration:
     ```yaml
     apiVersion: v1
     kind: Secret
     metadata:
       name: chores-tracker-secrets
     type: Opaque
     stringData:
       DATABASE_URL: "mysql+aiomysql://user:password@mysql-host:3306/chores_tracker"
       SECRET_KEY: "your-very-secure-production-key"
     ```

   - **Deployment** referencing these configurations:
     ```yaml
     apiVersion: apps/v1
     kind: Deployment
     metadata:
       name: chores-tracker
     spec:
       # ... other deployment specs
       template:
         spec:
           containers:
           - name: chores-tracker
             image: your-registry/chores-tracker:latest
             envFrom:
             - configMapRef:
                 name: chores-tracker-config
             - secretRef:
                 name: chores-tracker-secrets
     ```

## Database Migrations

Migrations are automatically run when the container starts through the `docker-entrypoint.sh` script. For the first deployment or when you need to manually run migrations:

```bash
# For local development
docker-compose exec api python -m alembic -c backend/alembic.ini upgrade head

# For Kubernetes
kubectl exec -it <pod-name> -- python -m alembic -c backend/alembic.ini upgrade head
``` 