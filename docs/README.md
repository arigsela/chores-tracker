# Chores Tracker Documentation

Welcome to the Chores Tracker documentation. This guide will help you understand, develop, deploy, and maintain the application.

## 📚 Documentation Structure

### 🏗️ Architecture (`/architecture/`)
System design and technical architecture documentation.

- **[BACKEND_ARCHITECTURE.md](architecture/BACKEND_ARCHITECTURE.md)** - Backend system architecture, service layers, database design
- **[CODEBASE_OVERVIEW.md](architecture/CODEBASE_OVERVIEW.md)** - High-level system overview, data models, API layers

### 🚀 Deployment (`/deployment/`)
Deployment guides, infrastructure configuration, and release management.

- **[KUBERNETES.md](deployment/KUBERNETES.md)** - Kubernetes deployment guide, MySQL StatefulSet, ingress
- **[GITOPS_CD_SETUP.md](deployment/GITOPS_CD_SETUP.md)** - ArgoCD setup and GitOps workflow
- **[GITOPS_DEPLOYMENT_ANALYSIS.md](deployment/GITOPS_DEPLOYMENT_ANALYSIS.md)** - Detailed GitOps architecture analysis
- **[RELEASING.md](deployment/RELEASING.md)** - Release process and semantic versioning
- **[frontend-deployment-setup.md](deployment/frontend-deployment-setup.md)** - Frontend containerization and deployment
- **[monitoring-account-setup.md](deployment/monitoring-account-setup.md)** - Monitoring service account configuration

### 💻 Development (`/development/`)
Development environment setup and coding guidelines.

- **[ENVIRONMENT_SETUP.md](development/ENVIRONMENT_SETUP.md)** - Local development environment configuration
- **[PYTHON_FASTAPI_CONCEPTS.md](development/PYTHON_FASTAPI_CONCEPTS.md)** - FastAPI patterns and async concepts
- **[PYTHON_FASTAPI_STRUCTURE.md](development/PYTHON_FASTAPI_STRUCTURE.md)** - Project structure and layered architecture

### 🔌 API (`/api/`)
API documentation and integration guides.

- **[JWT_AUTH_EXPLAINER.md](api/JWT_AUTH_EXPLAINER.md)** - JWT authentication flow and token structure
- **[ai-agent-health-check-integration.md](api/ai-agent-health-check-integration.md)** - Health check API and external monitoring

### 📱 Mobile (`/mobile/`)
Mobile application development guides.

- **[MOBILE_APP_DEVELOPMENT_GUIDE.md](mobile/MOBILE_APP_DEVELOPMENT_GUIDE.md)** - Mobile development approaches and framework comparison
- **[REACT_NATIVE_IMPLEMENTATION.md](mobile/REACT_NATIVE_IMPLEMENTATION.md)** - React Native implementation guide with phase tracking

### ⚙️ Operations (`/operations/`)
Operational procedures and maintenance.

- **[database-migrations.md](operations/database-migrations.md)** - Database migration procedures and Alembic usage

### 📦 Archive (`/archive/`)
Historical documentation preserved for reference.

- **[README.md](archive/README.md)** - Archive index with categorized historical documents

---

## 🚀 Quick Start Paths

### For New Developers
1. Start with [CODEBASE_OVERVIEW.md](architecture/CODEBASE_OVERVIEW.md) - Understand the system
2. Follow [ENVIRONMENT_SETUP.md](development/ENVIRONMENT_SETUP.md) - Set up your environment
3. Read [PYTHON_FASTAPI_STRUCTURE.md](development/PYTHON_FASTAPI_STRUCTURE.md) - Learn the codebase structure
4. Review [BACKEND_ARCHITECTURE.md](architecture/BACKEND_ARCHITECTURE.md) - Understand the architecture

### For Mobile Developers
1. [MOBILE_APP_DEVELOPMENT_GUIDE.md](mobile/MOBILE_APP_DEVELOPMENT_GUIDE.md) - Framework overview
2. [REACT_NATIVE_IMPLEMENTATION.md](mobile/REACT_NATIVE_IMPLEMENTATION.md) - Implementation guide
3. [JWT_AUTH_EXPLAINER.md](api/JWT_AUTH_EXPLAINER.md) - API authentication

### For DevOps/SRE
1. [KUBERNETES.md](deployment/KUBERNETES.md) - K8s infrastructure
2. [GITOPS_CD_SETUP.md](deployment/GITOPS_CD_SETUP.md) - Deployment automation
3. [RELEASING.md](deployment/RELEASING.md) - Release process
4. [database-migrations.md](operations/database-migrations.md) - Database procedures

### For API Consumers
1. [JWT_AUTH_EXPLAINER.md](api/JWT_AUTH_EXPLAINER.md) - Authentication
2. [ai-agent-health-check-integration.md](api/ai-agent-health-check-integration.md) - Health checks
3. `/docs` endpoint - Interactive API documentation (Swagger UI)

---

## 📖 Documentation Standards

### Naming Conventions
- **Architecture/Design**: `UPPERCASE_WITH_UNDERSCORES.md`
- **Guides/Tutorials**: `lowercase-with-hyphens.md`
- **Code Examples**: Include language identifier in code blocks

### Structure
- All documents include table of contents for >1000 words
- Examples are practical and runnable
- Screenshots/diagrams where helpful
- Links are relative to repository root

### Maintenance
- Update documentation when changing related code
- Mark deprecated features clearly
- Archive outdated documentation to `/archive/`
- Review documentation quarterly

---

## 🔗 External Resources

- **Live API Docs**: http://localhost:8000/docs (development)
- **Production API**: https://api.chores-tracker.com/docs
- **GitHub Repository**: https://github.com/your-org/chores-tracker
- **Issue Tracker**: https://github.com/your-org/chores-tracker/issues

---

## 📝 Contributing to Documentation

1. **For Code Changes**: Update related documentation in the same PR
2. **For New Features**: Add documentation before marking as complete
3. **For Deprecations**: Mark as deprecated, provide migration guide
4. **For Removals**: Move documentation to `/archive/` with explanation

See the project README for general contribution guidelines.

---

**Last Updated**: November 23, 2024
**Documentation Version**: 2.0
**Maintained By**: Chores Tracker Team
