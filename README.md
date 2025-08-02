# Chores Tracker

A modern web application for families to manage household chores, built with FastAPI, SQLAlchemy, and HTMX.

## 🚀 Project Status

### Phase 1 & 2 Progress ✅

**Phase 1 Completed** (December 2024)
- ✅ **SQLAlchemy 2.0** migration completed
- ✅ **Pydantic v2** migration completed  
- ✅ **pytest-asyncio** warnings fixed
- ✅ **Test coverage** improved to 70%+
- ✅ **Service layer** architecture implemented
- ✅ **All deprecations** removed - using 2024 best practices

**Phase 2 Completed** (December 2024 - January 2025)
- ✅ **Rate limiting** implemented with slowapi
- ✅ **Database optimizations** - indexes, eager loading, connection pooling
- ✅ **Unit of Work pattern** - transaction management implemented
- ✅ **API Documentation** - Enhanced OpenAPI specs with examples
- ✅ **Reward Adjustments** - Manual balance adjustments for bonuses/penalties
- ✅ **Dashboard Improvements** - Enhanced parent dashboard functionality

### CI/CD Status
[![Backend Tests](https://github.com/arigsela/chores-tracker/actions/workflows/backend-tests.yml/badge.svg)](https://github.com/arigsela/chores-tracker/actions/workflows/backend-tests.yml)
[![Deploy to ECR](https://github.com/arigsela/chores-tracker/actions/workflows/deploy-to-ecr.yml/badge.svg)](https://github.com/arigsela/chores-tracker/actions/workflows/deploy-to-ecr.yml)

**Test Summary:**
- Total tests: 223 (100% passing) ✅
- Coverage: 43% overall (>75% for critical business logic)
- Skipped: 15 (architectural limitations in test environment)

**CI/CD Pipeline:**
- **Automated Deployment**: Push to main triggers Docker build and ECR push
- **Security Scanning**: Trivy vulnerability scanning on every build
- **Multi-Tag Strategy**: Semantic versions, SHA tags, timestamps, and latest
- **GitHub Actions**: Comprehensive workflows for testing, building, and deployment

**Versioning:**
- This project follows [Semantic Versioning](https://semver.org/)
- Releases are created using GitHub Actions workflow
- Docker images are automatically tagged with version numbers

## 📋 Features

### Core Features
- **Parent accounts** can create and manage chores
- **Child accounts** can view and complete assigned chores
- **Reward system** with fixed or range-based rewards
- **Recurring chores** with cooldown periods
- **Real-time updates** using HTMX
- **Responsive design** with Tailwind CSS
- **Reward adjustments** - Parents can add bonuses or penalties to children's balances
- **Enhanced dashboard** - Improved UI for managing chores and viewing statistics

### Mobile App (React Native)
- **Native iOS and Android support** - Full-featured mobile application
- **Offline capabilities** - Works without constant internet connection
- **Push notifications** - Get alerts for new chores and approvals
- **Biometric authentication** - Secure login with Face ID/Touch ID
- **Native animations** - Smooth, responsive user experience

## 🛠️ Tech Stack

### Backend
- **FastAPI** (Python 3.11) - Modern async web framework
- **SQLAlchemy 2.0** - ORM with async support
- **MySQL 5.7** - Database (SQLite for tests)
- **Pydantic v2** - Data validation
- **JWT** - Authentication

### Frontend
- **Jinja2** - Template engine
- **HTMX** - Dynamic updates without JavaScript
- **Tailwind CSS** - Styling
- **Alpine.js** - Minimal JavaScript reactivity

### Development
- **Docker Compose** - Local development environment
- **Tilt** - Hot-reloading development
- **pytest** - Testing framework
- **Alembic** - Database migrations
- **GitHub Actions** - CI/CD pipeline
- **AWS ECR** - Container registry

### Mobile (React Native)
- **React Native 0.80.0** - Cross-platform mobile framework
- **React Navigation** - Navigation system
- **Async Storage** - Local data persistence
- **Reanimated 3** - Smooth animations
- **Axios** - API client

## 🚦 Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11 (for local development)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/arigsela/chores-tracker.git
   cd chores-tracker
   ```

2. **Create environment file**
   ```bash
   cp .env.sample .env
   # Edit .env with your settings
   ```

3. **Generate secret key**
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   # Add to .env as SECRET_KEY
   ```

4. **Start the application**
   ```bash
   docker-compose up
   ```

5. **Access the application**
   - Web UI: http://localhost:8000
   - API docs: http://localhost:8000/docs

### Development with Hot Reloading

For a better development experience with hot reloading:

```bash
tilt up
```

## 🧪 Testing

### Run all tests
```bash
docker compose exec api python -m pytest
```

### Run with coverage
```bash
docker compose exec api python -m pytest --cov=backend/app --cov-report=html
```

### Run specific test file
```bash
docker compose exec api python -m pytest backend/tests/test_repositories.py -v
```

## 📚 Documentation

### Key Documentation Files
- [`CLAUDE.md`](CLAUDE.md) - AI assistant instructions and development commands
- [`MODERNIZATION_ROADMAP.md`](MODERNIZATION_ROADMAP.md) - Detailed modernization plan and progress
- [`LOCAL_TESTING.md`](LOCAL_TESTING.md) - Local development and testing guide
- [`ECR_DEPLOYMENT_GUIDE.md`](ECR_DEPLOYMENT_GUIDE.md) - AWS ECR deployment setup
- [`GITOPS_DEPLOYMENT_ANALYSIS.md`](GITOPS_DEPLOYMENT_ANALYSIS.md) - Kubernetes deployment architecture
- [`RELEASING.md`](RELEASING.md) - Release process and versioning guide
- [`MOBILE_APP_DEVELOPMENT_GUIDE.md`](documents/MOBILE_APP_DEVELOPMENT_GUIDE.md) - Mobile app development guide
- [`REACT_NATIVE_IMPLEMENTATION.md`](documents/REACT_NATIVE_IMPLEMENTATION.md) - React Native implementation details

### API Documentation
When running locally, visit http://localhost:8000/docs for interactive API documentation.

## 🔧 Development Commands

### Database Operations
```bash
# Run migrations
docker compose exec api python -m alembic -c backend/alembic.ini upgrade head

# Create new migration
docker compose exec api python -m alembic -c backend/alembic.ini revision --autogenerate -m "description"

# Access MySQL shell
docker compose exec db mysql -u root -p
```

### User Management
```bash
# List all users
docker compose exec api python -m backend.app.scripts.list_users

# Reset a user's password
docker compose exec api python -m backend.app.scripts.reset_password

# Create a parent user
docker compose exec api python -m backend.app.scripts.create_parent_user
```

### Mobile App Development
```bash
# Navigate to mobile directory
cd mobile

# Install dependencies
npm install

# iOS development
npm run ios

# Android development
npm run android

# Run with backend
npm run backend  # In one terminal
npm run dev:simulator  # In another terminal
```

## 📈 Future Improvements

### Phase 3: UI & Performance (Partially Complete)
- ✅ Extract HTML to template files (completed)
- 📋 Add caching layer (Redis)
- 📋 Enhanced monitoring and logging
- 📋 Add OpenTelemetry monitoring
- 📋 Add E2E tests
- 📋 Add performance metrics

### Phase 4: Advanced Security (Future)
- Implement refresh tokens with rotation
- Add OAuth2 providers (Google, GitHub)
- Implement 2FA with TOTP
- Conduct comprehensive security audit
- Add API key authentication for services

See [`MODERNIZATION_ROADMAP.md`](MODERNIZATION_ROADMAP.md) for detailed plans.

## 🚀 Deployment

### CI/CD Pipeline
The project uses a comprehensive CI/CD pipeline:

1. **Docker Build & Push** (GitHub Actions)
   - Triggered on push to main or manual release
   - Builds Docker image with multi-stage Dockerfile
   - Pushes to AWS ECR with multiple tags
   - Includes Trivy security scanning

2. **GitOps Deployment** (ArgoCD)
   - Uses dual repository pattern:
     - Application code: `github.com/arigsela/chores-tracker`
     - Infrastructure configs: `github.com/arigsela/kubernetes`
   - ArgoCD automatically syncs Kubernetes deployments
   - Self-healing infrastructure with automatic rollback

### Docker Image Versioning
The project automatically builds and tags Docker images:
- **Semantic version tags**: `v3.0.0`, `v3.0`, `v3` 
- **Latest tag**: Always points to the most recent main branch
- **SHA tags**: `sha-abc1234` for specific commits
- **Timestamp tags**: `build-20240626-123456` for build tracking
- **Branch tags**: Feature branch names for testing

### Container Registry
- **AWS ECR**: `852893458518.dkr.ecr.us-east-2.amazonaws.com/chores-tracker`
- **Authentication**: Via ECR credentials sync CronJob
- **Lifecycle**: Automated cleanup of old images

### Creating a Release
See [`RELEASING.md`](RELEASING.md) for detailed instructions on creating releases.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style
- Follow PEP 8 for Python code
- Use type hints for all functions
- Write tests for new features
- Keep test coverage above 70% for new code

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with FastAPI by Sebastián Ramírez
- UI components from Tailwind CSS
- Dynamic updates powered by HTMX

---

**Last Updated:** January 2025