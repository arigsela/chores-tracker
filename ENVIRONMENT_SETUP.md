# Environment Setup Guide

## Initial Setup

1. Copy the environment template:
   ```bash
   cp .env.sample .env
   ```

2. Edit `.env` with your secure credentials:
   - Generate a strong `MYSQL_ROOT_PASSWORD`
   - Generate a strong `MYSQL_PASSWORD`
   - Generate a secure `SECRET_KEY`
   - Never commit the `.env` file to version control

3. Start the development environment:
   ```bash
   tilt up
   ```

## Security Notes

- The `.env` file contains sensitive information and should never be committed to version control
- Each developer should maintain their own `.env` file locally
- Production credentials should be managed through secure secrets management systems
- Regular security audits should be performed to ensure no credentials are accidentally committed
- Generate a secure SECRET_KEY for production using:
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(32))"
  ```

## Environment Variables

Required environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| MYSQL_ROOT_PASSWORD | MySQL root password | `strongpassword123` |
| MYSQL_DATABASE | Database name | `chores-db` |
| MYSQL_USER | Database user | `chores-user` |
| MYSQL_PASSWORD | Database password | `securepass123` |
| DATABASE_URL | Full database connection URL | `mysql+aiomysql://user:pass@mysql:3306/db` |
| SECRET_KEY | API encryption key | `your-secret-key` |
| DEBUG | Debug mode flag | `True` or `False` |
| ENVIRONMENT | Environment name | `development` or `production` |
| BACKEND_CORS_ORIGINS | Allowed CORS origins | `"http://localhost:3000,http://localhost:8000"` |
| ACCESS_TOKEN_EXPIRE_MINUTES | JWT token expiration time in minutes | `11520` |

## Local Development

For local development:

1. Create a `.env` file based on `.env.sample`:
   ```
   ENVIRONMENT=development
   DEBUG=True
   DATABASE_URL=mysql+aiomysql://chores-user:password@mysql:3306/chores-db
   SECRET_KEY=dev_secret_key
   BACKEND_CORS_ORIGINS="http://localhost:3000,http://localhost:8000"
   ```

2. Start the development environment using Tilt:
   ```bash
   tilt up
   ```

   This will start both the MySQL database and the API service.

3. To stop the development environment:
   ```bash
   tilt down
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

Migrations are automatically run when the container starts. For manual migration management:

```bash
# Using Docker Compose
docker compose exec api python -m alembic -c backend/alembic.ini upgrade head

# For Kubernetes
kubectl exec -it <pod-name> -- python -m alembic -c backend/alembic.ini upgrade head
``` 
