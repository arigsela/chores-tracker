# Chores Tracker

A modern web and mobile application for families to manage household chores, built with FastAPI backend and React Native Web frontend.

## 🏗️ Architecture

This application follows a modern decoupled architecture with separate backend and frontend services:

```
┌─────────────────────┐
│  React Native Web   │
│   Frontend (3000)   │ ← User Interface (Web, iOS, Android)
└──────────┬──────────┘
           │ HTTP/REST API
           ↓
┌─────────────────────┐
│   FastAPI Backend   │
│      (8000)         │ ← Business Logic & Authentication
└──────────┬──────────┘
           │ SQL (async)
           ↓
┌─────────────────────┐
│   MySQL Database    │
│      (3306)         │ ← Data Persistence
└─────────────────────┘
```

**Key Characteristics:**
- **API-First Design**: Backend serves JSON-only REST API
- **Cross-Platform Frontend**: Single React Native codebase for web, iOS, and Android
- **JWT Authentication**: Stateless token-based auth with 8-day expiry
- **Service Layer Architecture**: Clean separation of concerns in backend
- **Async Throughout**: Async Python with SQLAlchemy 2.0 and async MySQL driver

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

**Recent Updates** (August 2025)
- ✅ **React Native Web Migration** - Successfully migrated from HTMX to React Native Web
- ✅ **Child Balance Display** - Added prominent balance card for child users
- ✅ **Dashboard Authentication Fix** - Resolved issue where child users were redirected to login
- ✅ **Improved User Schemas** - Added balance field to UserInDB schema
- ✅ **Enhanced Child Experience** - Better UI/UX for child users viewing their rewards
- ✅ **Cross-Platform Support** - Single codebase now supports web, iOS, and Android

### CI/CD Status
[![Backend Tests](https://github.com/arigsela/chores-tracker/actions/workflows/backend-tests.yml/badge.svg)](https://github.com/arigsela/chores-tracker/actions/workflows/backend-tests.yml)
[![Deploy to ECR](https://github.com/arigsela/chores-tracker/actions/workflows/deploy-to-ecr.yml/badge.svg)](https://github.com/arigsela/chores-tracker/actions/workflows/deploy-to-ecr.yml)

**Test Summary:**
- Total tests: 223 (100% passing) ✅
- Coverage: 43% overall (>75% for critical business logic)
- Skipped: 15 (architectural limitations in test environment)

**Known Issues Fixed:**
- ✅ Child users no longer redirected to login after successful authentication
- ✅ Parent-only API endpoints no longer called for child users
- ✅ React component lifecycle issues resolved
- ✅ "Show All" button now works correctly for chore lists exceeding 10 items
- ✅ API integration and state management optimized

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
- **Multi-assignment modes** - Three flexible chore assignment patterns:
  - **Single**: Traditional one-child assignment
  - **Multi-Independent**: Personal chores for multiple children (e.g., "Clean your room")
  - **Unassigned Pool**: Shared chores, first-come-first-served (e.g., "Walk the dog")
- **Reward system** with fixed or range-based rewards
- **Per-assignment tracking** - Each child's completion tracked independently
- **Recurring chores** with cooldown periods (mode-specific reset behavior)
- **Real-time updates** with React state management and API polling
- **Responsive design** with React Native StyleSheet
- **Reward adjustments** - Parents can add bonuses or penalties to children's balances
- **Enhanced dashboard** - Improved UI for managing chores and viewing statistics
- **Child balance display** - Children can see their current balance prominently on dashboard
- **Role-based UI** - Optimized views for parent and child users

### Cross-Platform Support
The `frontend/` directory contains a **React Native Web** application that supports multiple platforms:
- **Web Browser** - Runs in any modern web browser at http://localhost:3000
- **iOS** - Native iOS app (via Expo)
- **Android** - Native Android app (via Expo)
- **Progressive Web App** - Can be installed on mobile devices

**Shared Features Across All Platforms:**
- Unified codebase with platform-specific optimizations
- Offline capabilities with AsyncStorage
- Responsive design adapting to screen sizes
- Native navigation patterns per platform

## 🛠️ Tech Stack

### Backend
- **FastAPI** (Python 3.11) - Modern async web framework
- **SQLAlchemy 2.0** - ORM with async support
- **MySQL 8.0** - Database (SQLite for tests)
- **Pydantic v2** - Data validation
- **JWT** - Authentication

### Frontend (React Native Web)
- **React Native Web** - Cross-platform UI framework
- **Expo** - Development and build tooling
- **React Navigation** - Navigation system
- **Axios** - API client with interceptors
- **TypeScript** - Type-safe development
- **AsyncStorage** - Local data persistence

### Development
- **Docker Compose** - Local development environment
- **Tilt** - Hot-reloading development
- **pytest** - Testing framework
- **Alembic** - Database migrations
- **GitHub Actions** - CI/CD pipeline
- **AWS ECR** - Container registry


## 🚦 Quick Start

### Prerequisites

Before you begin, ensure you have the following installed:

- **Docker Desktop** 20.10+ and **Docker Compose** 2.0+
- **Node.js** 18+ and **npm** 9+ (for frontend development)
- **Python** 3.11+ (for local backend development, optional)
- **Git** for version control

**Optional but Recommended:**
- **Tilt** for hot-reloading development experience
- **VS Code** with Python and TypeScript extensions

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
   - **Backend API**: http://localhost:8000
   - **Frontend Web UI**: http://localhost:3000
   - **API Documentation**: http://localhost:8000/docs

### Development with Hot Reloading

For a better development experience with hot reloading:

```bash
tilt up
```

## 🧪 Testing

### Backend Tests

#### Run all tests
```bash
docker compose exec api python -m pytest
```

#### Run with coverage
```bash
docker compose exec api python -m pytest --cov=backend/app --cov-report=html
```

#### Run specific test file
```bash
docker compose exec api python -m pytest backend/tests/test_repositories.py -v
```

### Frontend Tests

#### Run all tests
```bash
cd frontend
npm test
```

#### Run tests in watch mode
```bash
npm run test:watch
```

#### Run with coverage
```bash
npm run test:coverage
```

#### Type checking
```bash
npm run type-check
```

## 📚 Documentation

### Core Documentation
- **[CLAUDE.md](CLAUDE.md)** - AI assistant instructions and development commands
- **[README.md](README.md)** - This file - project overview and quick start

### Development Guides
- **[LOCAL_TESTING.md](LOCAL_TESTING.md)** - Local development and testing guide
- **[MODERNIZATION_ROADMAP.md](MODERNIZATION_ROADMAP.md)** - Modernization plan and progress tracking

### Deployment & Operations
- **[RELEASING.md](RELEASING.md)** - Release process and versioning guide
- **[ECR_DEPLOYMENT_GUIDE.md](ECR_DEPLOYMENT_GUIDE.md)** - AWS ECR deployment setup
- **[GITOPS_DEPLOYMENT_ANALYSIS.md](GITOPS_DEPLOYMENT_ANALYSIS.md)** - Kubernetes deployment architecture
- **[docs/frontend-deployment-setup.md](docs/frontend-deployment-setup.md)** - Frontend containerization and deployment

### Monitoring & Integration
- **[docs/ai-agent-health-check-integration.md](docs/ai-agent-health-check-integration.md)** - External monitoring and health check API
- **[docs/monitoring-account-setup.md](docs/monitoring-account-setup.md)** - Service account setup for monitoring

### Mobile Development
- **[documents/MOBILE_APP_DEVELOPMENT_GUIDE.md](documents/MOBILE_APP_DEVELOPMENT_GUIDE.md)** - Mobile app development guide
- **[documents/REACT_NATIVE_IMPLEMENTATION.md](documents/REACT_NATIVE_IMPLEMENTATION.md)** - React Native implementation details

### API Documentation
- **Interactive API Docs**: http://localhost:8000/docs (when running locally)
- **OpenAPI Schema**: http://localhost:8000/openapi.json

### Archived Documentation
Historical implementation plans and planning documents are available in `docs/archive/` for reference.

## 🔧 Development Commands

### Frontend Development

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start web development server
npm run web

# Run on iOS simulator (requires Xcode)
npm run ios

# Run on Android emulator (requires Android Studio)
npm run android

# Start Expo development server (choose platform)
npm start

# Run tests
npm test

# Type checking
npm run type-check

# Linting
npm run lint

# Build for production
npm run build
```

**Platform-Specific Notes:**
- **Web**: Runs at http://localhost:3000, hot-reloads on changes
- **iOS**: Requires macOS with Xcode installed
- **Android**: Requires Android Studio and emulator or physical device
- **Expo Go**: Scan QR code to test on physical device without building

### Backend Development

```bash
# Start backend with Docker
docker-compose up api

# Run backend tests
docker compose exec api python -m pytest -v

# Access Python shell
docker compose exec api python

# Format code
docker compose exec api black backend/app

# Run linter
docker compose exec api flake8 backend/app
```

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

## ⚙️ Environment Configuration

### Backend Environment Variables (.env)

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SECRET_KEY` | JWT signing key | Yes | - |
| `DATABASE_URL` | MySQL connection string | Yes | - |
| `MYSQL_ROOT_PASSWORD` | Database root password | Yes | - |
| `MYSQL_DATABASE` | Database name | Yes | `chores_tracker` |
| `MYSQL_USER` | Database user | Yes | - |
| `MYSQL_PASSWORD` | Database password | Yes | - |
| `DEBUG` | Enable debug mode | No | `false` |
| `ENVIRONMENT` | Environment name | No | `development` |
| `BACKEND_CORS_ORIGINS` | Allowed CORS origins | Yes | `["http://localhost:3000"]` |

### Frontend Environment Variables (frontend/.env)

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `REACT_APP_API_URL` | Backend API URL | No | `http://localhost:8000/api/v1` |

See `.env.sample` for a complete template.

## 🎯 Recent Feature Highlights

### Multi-Assignment Chore System (January 2025) 🆕
The application now supports three distinct chore assignment patterns to accommodate different family scenarios:

**Single Assignment Mode**:
- Traditional one-child-one-chore assignment (backward compatible)
- Example: "Mow the lawn" assigned to Alice
- Child completes → parent approves → balance increases

**Multi-Independent Mode**:
- Personal chores where each child does their own version
- Example: "Clean your room" assigned to Alice, Bob, and Charlie
- Each child completes independently
- Parent approves each completion separately
- Each child's balance increases independently

**Unassigned Pool Mode**:
- Shared household chores, first-come-first-served
- Example: "Walk the dog", "Take out trash"
- Any child can claim and complete
- Great for encouraging initiative and sharing responsibilities

**Technical Implementation**:
- Assignment-level tracking with `chore_assignments` junction table
- Per-assignment completion and approval status
- Mode-specific cooldown behavior for recurring chores
- Comprehensive validation and error handling
- 83 passing tests across unit, integration, and edge cases

See [CLAUDE.md](CLAUDE.md) for detailed API examples and usage patterns.

### Child Balance Display (August 2025)
The child balance feature provides a prominent display of rewards earned:
- **Balance Card Component**: Shows current balance with wallet icon
- **Real-time Updates**: Balance refreshes when chores are approved
- **Child-Friendly UI**: Large, clear display optimized for young users
- **Responsive Design**: Adapts to mobile and desktop screens

### Dashboard Authentication Fix (August 2025)
Resolved critical issue affecting child user experience:
- **Fixed Race Condition**: Parent-only endpoints no longer load for child users
- **Conditional Loading**: Role-specific content loads after authentication
- **Improved Error Handling**: 403 errors no longer cause login redirects
- **Smoother Navigation**: Child users stay logged in after authentication

### React Native Web Migration (August 2025)
Successfully migrated from server-side rendered HTMX to modern React Native Web:
- **Cross-Platform Capability**: Single codebase now supports web, iOS, and Android
- **Modern React Patterns**: Hooks, Context API, and functional components throughout
- **Type Safety**: Full TypeScript implementation with strict typing
- **Improved Performance**: Client-side routing and optimized API calls
- **Better Developer Experience**: Hot module reloading and comprehensive testing

## 📈 Roadmap & Future Improvements

### Completed Milestones ✅
- **Phase 1**: SQLAlchemy 2.0 and Pydantic v2 migration
- **Phase 2**: Performance optimization and Unit of Work pattern
- **Phase 3**: React Native Web migration (HTMX retirement complete)

### In Progress 🚧
- **Frontend Feature Parity**: Closing remaining 10% gap with original HTMX features
- **Mobile App Polish**: iOS and Android platform-specific optimizations
- **Test Coverage**: Expanding frontend test coverage to match backend

### Upcoming Features 📋

**Performance & Scalability:**
- Add caching layer with Redis
- Implement OpenTelemetry monitoring
- Add E2E tests with Playwright
- Performance metrics and dashboard

**Security Enhancements:**
- Refresh tokens with rotation
- OAuth2 providers (Google, GitHub)
- Two-factor authentication (2FA/TOTP)
- Comprehensive security audit
- API key authentication for services

**Mobile Features:**
- Push notifications for chore assignments
- Biometric authentication (Face ID/Touch ID)
- Offline mode with sync capability
- Native camera integration for chore verification

See [`MODERNIZATION_ROADMAP.md`](MODERNIZATION_ROADMAP.md) for detailed plans and timelines.

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

## 🔍 Troubleshooting

### Frontend Can't Connect to Backend

**Symptom**: Network errors or CORS issues in browser console

**Solutions**:
1. Ensure backend is running: `docker compose ps`
2. Check backend is accessible: `curl http://localhost:8000/health`
3. Verify CORS configuration in `backend/app/main.py`
4. Check frontend API_URL in `frontend/.env` or config

### Authentication Issues

**Symptom**: "Invalid token" or "Token expired" errors

**Solutions**:
1. JWT tokens expire after 8 days - try logging in again
2. Clear browser local storage: Open DevTools → Application → Local Storage → Clear
3. Check token format in browser DevTools → Application → Local Storage
4. Ensure `SECRET_KEY` hasn't changed between backend restarts

### Database Connection Issues

**Symptom**: Backend won't start, database connection errors

**Solutions**:
1. Check MySQL is healthy: `docker compose exec mysql mysqladmin ping -h localhost -u root -p`
2. Verify DATABASE_URL format: `mysql+aiomysql://user:password@mysql:3306/database`
3. Check MySQL logs: `docker compose logs mysql`
4. Try resetting volumes: `docker compose down -v && docker compose up`

### Port Already in Use

**Symptom**: "Address already in use" error when starting services

**Solutions**:
1. Check what's using the port: `lsof -i :8000` or `lsof -i :3000`
2. Stop conflicting service or change port in docker-compose.yml
3. Ensure old containers are stopped: `docker compose down`

### Tests Failing

**Symptom**: Tests fail when running pytest

**Solutions**:
1. Ensure test database is clean: Tests use SQLite in-memory
2. Check for environment variable conflicts: Tests use `TESTING=true`
3. Run with verbose output: `docker compose exec api python -m pytest -vv`
4. Check for database migration issues: `docker compose exec api alembic upgrade head`

### Frontend Build Issues

**Symptom**: npm errors or build failures

**Solutions**:
1. Delete node_modules and reinstall: `rm -rf node_modules && npm install`
2. Clear npm cache: `npm cache clean --force`
3. Check Node.js version: `node --version` (should be 18+)
4. Try updating dependencies: `npm update`

## 🙏 Acknowledgments

- Built with **FastAPI** by Sebastián Ramírez
- Frontend built with **React Native** and **Expo**
- Icons from **React Native Vector Icons**
- Navigation by **React Navigation**
- Database ORM by **SQLAlchemy**

---

**Last Updated:** January 2026