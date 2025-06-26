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

**Phase 2 In Progress** (June 2025)
- ✅ **Rate limiting** implemented with slowapi
- ✅ **Database optimizations** - indexes, eager loading, connection pooling
- 🔄 **Unit of Work pattern** - next up
- 📋 **Test coverage to 80%** - pending

### CI/CD Status
[![Backend Tests](https://github.com/arigsela/chores-tracker/actions/workflows/backend-tests.yml/badge.svg)](https://github.com/arigsela/chores-tracker/actions/workflows/backend-tests.yml)
[![Deploy to ECR](https://github.com/arigsela/chores-tracker/actions/workflows/deploy-to-ecr.yml/badge.svg)](https://github.com/arigsela/chores-tracker/actions/workflows/deploy-to-ecr.yml)

**Test Summary:**
- Total tests: 130 (126 + 4 rate limit tests)
- Passing: 130 (100%) ✅
- Skipped: 0 ✅
- Failing: 0 ✅

**Versioning:**
- This project follows [Semantic Versioning](https://semver.org/)
- Releases are created using GitHub Actions workflow
- Docker images are automatically tagged with version numbers

## 📋 Features

- **Parent accounts** can create and manage chores
- **Child accounts** can view and complete assigned chores
- **Reward system** with fixed or range-based rewards
- **Recurring chores** with cooldown periods
- **Real-time updates** using HTMX
- **Responsive design** with Tailwind CSS

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
- [`GITHUB_ACTIONS_COMPATIBILITY.md`](GITHUB_ACTIONS_COMPATIBILITY.md) - CI/CD setup details
- [`API_TEST_FIX_SUMMARY.md`](API_TEST_FIX_SUMMARY.md) - Notes on test improvements
- [`LOCAL_TESTING.md`](LOCAL_TESTING.md) - Local development and testing guide
- [`ECR_DEPLOYMENT_GUIDE.md`](ECR_DEPLOYMENT_GUIDE.md) - AWS ECR deployment setup
- [`RELEASING.md`](RELEASING.md) - Release process and versioning guide

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
```

## 📈 Future Improvements

### Phase 2: Security & Performance (In Progress)
- ✅ Add rate limiting (completed)
- ✅ Optimize database queries (completed)
- 🔄 Add transaction management (Unit of Work) - next
- 📋 Improve test coverage to 80%

### Phase 3: Low Priority Items (Future)
- Extract HTML to template files
- Add comprehensive API documentation  
- Add caching layer (Redis)
- Enhanced monitoring and logging

### Phase 4: Advanced Security (Future)
- Implement refresh tokens
- Add OAuth2 providers
- Implement 2FA
- Conduct security audit

### Phase 3: UI & Monitoring
- Extract inline HTML to templates
- Add OpenTelemetry monitoring
- Improve documentation
- Add E2E tests
- Add performance metrics

See [`MODERNIZATION_ROADMAP.md`](MODERNIZATION_ROADMAP.md) for detailed plans.

## 🚀 Deployment

### Docker Image Versioning
The project automatically builds and tags Docker images on release:
- **Semantic version tags**: `1.0.0`, `1.0`, `1` 
- **Latest tag**: Always points to the most recent release
- **SHA tags**: `sha-abc1234` for specific commits
- **Timestamp tags**: `build-20240626-123456` for build tracking

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

**Last Updated:** June 23, 2025