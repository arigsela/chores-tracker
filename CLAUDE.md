# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Chores Tracker** is a full-stack family chore management application with:
- **Backend**: FastAPI (Python 3.11) with SQLAlchemy 2.0, MySQL database
- **Frontend**: Server-side rendered HTML with HTMX for dynamic updates, Tailwind CSS
- **Mobile**: React Native app for iOS/Android with offline support
- **Infrastructure**: Docker Compose for local dev, AWS ECR + Kubernetes for production

## Key Architecture Patterns

### Backend (FastAPI + SQLAlchemy)

**Service Layer Architecture**:
- **Models** (`backend/app/models/`): SQLAlchemy ORM models
- **Schemas** (`backend/app/schemas/`): Pydantic v2 models for validation
- **Repositories** (`backend/app/repositories/`): Data access layer
- **Services** (`backend/app/services/`): Business logic layer
- **Unit of Work** (`backend/app/core/unit_of_work.py`): Transaction management
- **Dependencies** (`backend/app/dependencies/`): Dependency injection

**Authentication**: JWT-based with parent/child role system
**API Structure**: RESTful endpoints under `/api/v1/`

### Frontend (HTMX + Jinja2)

- **Templates** (`backend/app/templates/`): Jinja2 HTML templates
  - `pages/`: Full page templates
  - `components/`: Reusable HTMX components
  - `layouts/`: Base layouts
- **HTMX Patterns**: Server returns HTML fragments for dynamic updates
- **JavaScript**: Minimal, mainly for HTMX initialization on dynamic content

### Mobile App (React Native)

- **Navigation**: React Navigation with stack/tab navigators
- **State**: Context API for auth state
- **API Client**: Axios with JWT token management
- **Storage**: AsyncStorage for offline persistence

## Essential Commands

### Development Setup

```bash
# Start the full stack with Docker Compose
docker-compose up

# Or use Tilt for hot-reloading development
tilt up

# Access the application
# Web: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Backend Development

```bash
# Run all tests
docker compose exec api python -m pytest

# Run specific test file
docker compose exec api python -m pytest backend/tests/test_repositories.py -v

# Run with coverage
docker compose exec api python -m pytest --cov=backend/app --cov-report=html

# Run a single test
docker compose exec api python -m pytest backend/tests/test_service_layer.py::TestUserServiceBusinessLogic::test_create_child_user -v

# Database migrations
docker compose exec api python -m alembic -c backend/alembic.ini upgrade head
docker compose exec api python -m alembic -c backend/alembic.ini revision --autogenerate -m "description"

# Access MySQL shell
docker compose exec mysql mysql -u root -p
```

### Mobile Development

```bash
cd mobile

# Install dependencies
npm install

# iOS development
npm run ios:simulator  # Run on simulator
npm run ios:device     # Run on connected device

# Android development
npm run android

# Development with local backend
npm run backend  # Start Docker backend (in one terminal)
npm run dev:simulator  # Run app with local API (in another)

# Clean cache
npm run start:clean
```

### User Management Scripts

```bash
# List all users
docker compose exec api python -m backend.app.scripts.list_users

# Create a parent user
docker compose exec api python -m backend.app.scripts.create_parent_user

# Reset a user's password
docker compose exec api python -m backend.app.scripts.reset_password

# Create test child user
docker compose exec api python -m backend.app.scripts.create_test_child
```

## Testing Strategy

### Backend Testing
- **Unit tests**: Test services, repositories in isolation
- **Integration tests**: Test API endpoints with test database
- **Test database**: Uses SQLite in-memory for speed
- **Fixtures**: See `backend/tests/conftest.py` for common test fixtures
- **Coverage target**: >70% for critical business logic

### Key Test Patterns
```python
# Always use TESTING=true environment variable
TESTING=true python3 -m pytest

# Test with specific verbosity
python -m pytest -v  # Verbose
python -m pytest --tb=short  # Short traceback
python -m pytest -x  # Stop on first failure
```

## Important Implementation Details

### HTMX Dynamic Content
When loading content dynamically with HTMX, always initialize new elements:
```javascript
// After loading new HTMX content
htmx.process(document.querySelector('#new-content'));
```

### Database Transactions
Use Unit of Work pattern for multi-repository operations:
```python
async with UnitOfWork() as uow:
    user = await uow.users.create(db=uow.session, obj_in=user_data)
    chore = await uow.chores.create(db=uow.session, obj_in=chore_data)
    await uow.commit()
```

### JWT Authentication Flow
1. Login returns JWT token (8-day expiry)
2. Include in requests: `Authorization: Bearer <token>`
3. Parent vs Child role determines API access

### Reward System
- **Fixed rewards**: Single amount
- **Range rewards**: Min/max amounts, parent sets final value on approval
- **Adjustments**: Manual balance changes with reasons

## CI/CD Pipeline

### GitHub Actions Workflows
- **backend-tests.yml**: Runs on backend changes, Python 3.11
- **deploy-to-ecr.yml**: Builds Docker image, pushes to AWS ECR
- **create-release.yml**: Creates GitHub releases with semantic versioning

### Deployment
- **Local**: Docker Compose or Tilt
- **Production**: Kubernetes via ArgoCD (GitOps)
- **Container Registry**: AWS ECR

## Common Troubleshooting

### HTMX Not Working on Dynamic Content
Add `htmx.process()` after loading new content

### Child Users Redirected to Login
Check conditional loading of parent-only endpoints in templates

### Database Connection Issues
Ensure MySQL is healthy: `docker compose exec mysql mysqladmin ping -h localhost -u root -p`

### Mobile App Can't Connect to Backend
- Use `API_URL=http://localhost:8000/api/v1` for local development
- Check CORS settings in backend

## Domain Concepts

### User Hierarchy
- **Parents**: Can create children, chores, approve completions
- **Children**: Can view assigned chores, mark complete, view balance

### Chore Lifecycle
1. Parent creates chore (assigned or unassigned)
2. Child marks as completed
3. Parent approves and sets final reward
4. Child's balance increases

### Reward Adjustments
Parents can manually adjust child balances for bonuses/penalties outside normal chore flow

## Code Style Guidelines

- **Python**: Follow PEP 8, use type hints, async/await patterns
- **SQL**: Use SQLAlchemy 2.0 async patterns
- **Templates**: Keep logic minimal, use HTMX for interactivity
- **React Native**: Functional components with hooks

## Security Considerations

- JWT tokens expire after 8 days
- Passwords hashed with bcrypt
- Role-based access control (parent/child)
- Rate limiting on auth endpoints
- Input validation with Pydantic