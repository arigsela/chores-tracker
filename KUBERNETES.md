# Kubernetes Deployment Guide

This guide explains how to deploy the Chores Tracker application to Kubernetes with a proper MySQL database configuration.

## Prerequisites

- A Kubernetes cluster
- Access to a MySQL database
- kubectl configured to access your cluster
- A container registry for your Docker images

## MySQL Database Configuration

The application requires a MySQL database in production. You have two options:

### Option 1: Use an Existing MySQL Instance

If you have an existing MySQL instance (managed service, standalone server, etc.), create a database and user:

```sql
CREATE DATABASE chores_tracker;
CREATE USER 'chores_user'@'%' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON chores_tracker.* TO 'chores_user'@'%';
FLUSH PRIVILEGES;
```

### Option 2: Deploy MySQL in Kubernetes

If you prefer to run MySQL within Kubernetes, you can use a StatefulSet:

```yaml
# mysql-statefulset.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mysql
spec:
  selector:
    matchLabels:
      app: mysql
  serviceName: mysql
  replicas: 1
  template:
    metadata:
      labels:
        app: mysql
    spec:
      containers:
      - name: mysql
        image: mysql:8.0
        ports:
        - containerPort: 3306
        env:
        - name: MYSQL_ROOT_PASSWORD
          valueFrom:
            secretKeyRef:
              name: mysql-secrets
              key: root-password
        - name: MYSQL_DATABASE
          value: chores_tracker
        - name: MYSQL_USER
          valueFrom:
            secretKeyRef:
              name: mysql-secrets
              key: user
        - name: MYSQL_PASSWORD
          valueFrom:
            secretKeyRef:
              name: mysql-secrets
              key: password
        volumeMounts:
        - name: mysql-data
          mountPath: /var/lib/mysql
  volumeClaimTemplates:
  - metadata:
      name: mysql-data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi
---
apiVersion: v1
kind: Service
metadata:
  name: mysql
spec:
  selector:
    app: mysql
  ports:
  - port: 3306
    targetPort: 3306
  clusterIP: None
```

Create MySQL secrets:

```yaml
# mysql-secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: mysql-secrets
type: Opaque
stringData:
  root-password: your-root-password
  user: chores_user
  password: your-secure-password
```

## Deploying the Application

1. Build and push the Docker image:
   ```bash
   docker build -t your-registry/chores-tracker:latest .
   docker push your-registry/chores-tracker:latest
   ```

2. Create ConfigMap for application configuration:
   ```yaml
   apiVersion: v1
   kind: ConfigMap
   metadata:
     name: chores-tracker-config
   data:
     ENVIRONMENT: "production"
     DEBUG: "False"
     BACKEND_CORS_ORIGINS: "https://your-domain.com"
   ```

3. Create Secret for sensitive information:
   ```yaml
   apiVersion: v1
   kind: Secret
   metadata:
     name: chores-tracker-secrets
   type: Opaque
   stringData:
     DATABASE_URL: "mysql+aiomysql://chores_user:your-secure-password@mysql:3306/chores_tracker"
     SECRET_KEY: "your-secure-production-key"
   ```

4. Create the Deployment:
   ```yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: chores-tracker
   spec:
     replicas: 1
     selector:
       matchLabels:
         app: chores-tracker
     template:
       metadata:
         labels:
           app: chores-tracker
       spec:
         containers:
         - name: chores-tracker
           image: your-registry/chores-tracker:latest
           ports:
           - containerPort: 8000
           envFrom:
           - configMapRef:
               name: chores-tracker-config
           - secretRef:
               name: chores-tracker-secrets
           readinessProbe:
             httpGet:
               path: /api/v1/healthcheck
               port: 8000
             initialDelaySeconds: 10
             periodSeconds: 5
   ```

5. Create a Service:
   ```yaml
   apiVersion: v1
   kind: Service
   metadata:
     name: chores-tracker
   spec:
     selector:
       app: chores-tracker
     ports:
     - port: 80
       targetPort: 8000
     type: ClusterIP
   ```

6. Create an Ingress (example for nginx-ingress):
   ```yaml
   apiVersion: networking.k8s.io/v1
   kind: Ingress
   metadata:
     name: chores-tracker
     annotations:
       kubernetes.io/ingress.class: nginx
       cert-manager.io/cluster-issuer: letsencrypt
   spec:
     tls:
     - hosts:
       - your-domain.com
       secretName: chores-tracker-tls
     rules:
     - host: your-domain.com
       http:
         paths:
         - path: /
           pathType: Prefix
           backend:
             service:
               name: chores-tracker
               port:
                 number: 80
   ```

## Initial Database Setup

After deploying, run the initial migrations:

```bash
kubectl exec -it $(kubectl get pods -l app=chores-tracker -o jsonpath="{.items[0].metadata.name}") -- python -m alembic -c backend/alembic.ini upgrade head
```

## Monitoring and Maintenance

Monitor your application using your preferred Kubernetes monitoring tools. For MySQL maintenance, consider:

1. Setting up regular database backups
2. Monitoring database performance
3. Scaling the database if needed (consider using a managed service in production) 