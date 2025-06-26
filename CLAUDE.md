# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Chores Tracker is a web application designed to help families manage household chores. Parents can assign chores to children, set rewards, and track completion. Children can mark chores as complete, and parents can approve them, with rewards tracked for allowance purposes.

## Recent Updates (December 24, 2024)

### Phase 1 Completed ✅
- **SQLAlchemy 2.0**: Migrated from legacy patterns to modern declarative syntax
- **Pydantic v2**: Updated all schemas to use ConfigDict and model_dump()
- **pytest-asyncio**: Fixed configuration warnings with proper pytest.ini
- **Test Coverage**: Improved core component coverage to >75%
- **Service Layer**: Implemented complete service architecture (Phase 1.5)
- **Dependencies**: All packages updated to latest stable versions

### CI/CD Fixes Completed ✅
- **Python Compatibility**: Fixed Python 3.9+ union syntax (`T | None` → `Optional[T]`)
- **Test Authentication**: Fixed JWT token creation in test files
- **Service Method Calls**: Corrected parameter names in service method invocations
- **Schema Validation**: Made `assignee_id` optional in `ChoreResponse` schema
- **CI Environment**: Added `TESTING=true` to GitHub Actions workflow

### Missing HTML Endpoints Implemented ✅
- **GET /chores/{id}/approve-form**: Returns approval form for parents
- **GET /chores/{id}/edit-form**: Returns edit form for parents
- **PUT /chores/{id}**: Updates chore details (JSON API)
- Created corresponding HTML templates (approve-form.html, edit-form.html)
- All previously skipped tests now passing

### Unit of Work Pattern ✅
- **Implementation**: Already exists in `app/core/unit_of_work.py`
- **Features**: Async context manager for transactional operations
- **Repository Access**: Lazy-loaded user and chore repositories
- **Usage**: Used in `bulk_assign_chores` and `approve_chore_with_next_instance` methods
- **Tests**: Comprehensive edge case testing in place

### API Documentation Enhanced ✅
- **OpenAPI Metadata**: Added comprehensive app-level documentation
- **Endpoint Documentation**: All REST endpoints now have detailed descriptions, examples, and response codes
- **Schema Documentation**: Pydantic models enhanced with field descriptions and examples
- **Authentication Flow**: Documented complete auth flow in OpenAPI description
- **HTML Endpoints**: Documented HTMX endpoints for approve/edit forms
- **Deprecation Fixes**: Updated to Pydantic v2 field validators and json_schema_extra

### Latest CI Fixes (December 24, 2024) ✅
- **Rate Limiting Decorators**: Added missing `request: Request` parameter to `@limit_update` and `@limit_delete` decorated endpoints
- **Test Error Handling**: Fixed validation error response handling in tests (supporting both string and list error messages)
- **Unit of Work Tests**: Modified to use test database session factory instead of production MySQL connection
  - Fixed async/sync mismatch by using lambda function instead of async factory
  - Fixed DetachedInstanceError by storing IDs and re-fetching objects after UnitOfWork context
- **Schema Validation**: Added missing description field in test data to satisfy NOT NULL constraint

### Current Test Status
- **Total**: 223 tests
- **Passing**: 223 (100%) ✅
- **Skipped**: 15 ✅ (reduced from 21)
- **Coverage**: 43% overall (but >75% for critical business logic)

## Tech Stack

- **Backend**: FastAPI (Python 3.11) with async support
- **Database**: MySQL 5.7 with SQLAlchemy 2.0 ORM (async)
- **Frontend**: Jinja2 HTML templates with HTMX for dynamic updates
- **Authentication**: JWT tokens with OAuth2 Password Bearer flow
- **Development**: Docker Compose, Tilt for hot-reloading
- **Testing**: pytest with async support and coverage reporting

## Local Testing

For comprehensive local testing instructions, including:
- Docker-based setup (recommended)
- Direct Python setup for faster iteration
- API testing with curl/HTTPie examples
- Accessing the enhanced API documentation
- Troubleshooting common issues

**See [LOCAL_TESTING.md](./LOCAL_TESTING.md) for the complete guide.**

## Development Commands

### Initial Setup

```bash
# Create environment file from template
cp .env.sample .env

# Generate secret key for JWT
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Start development environment with Docker Compose
docker-compose up

# Or use Tilt for hot-reloading
tilt up
```

### Database Operations

```bash
# Run migrations (automatic on startup via docker-entrypoint.sh)
docker compose exec api python -m alembic -c backend/alembic.ini upgrade head

# Create new migration
docker compose exec api python -m alembic -c backend/alembic.ini revision --autogenerate -m "migration description"

# Check migration history
docker compose exec api python -m alembic -c backend/alembic.ini history

# Downgrade one revision
docker compose exec api python -m alembic -c backend/alembic.ini downgrade -1
```

### Testing

```bash
# Run all tests
docker compose exec api python -m pytest

# Run with verbose output and print statements
docker compose exec api python -m pytest -vv -s

# Run specific test file
docker compose exec api python -m pytest backend/tests/api/v1/test_chores.py

# Run specific test
docker compose exec api python -m pytest backend/tests/api/v1/test_chores.py::test_create_chore

# Run tests matching pattern
docker compose exec api python -m pytest -k "test_create"

# Run with coverage
docker compose exec api python -m pytest --cov=backend/app --cov-report=html

# Stop on first failure
docker compose exec api python -m pytest -x

# Rerun failed tests
docker compose exec api python -m pytest --lf

# Run tests excluding rate limiting tests
docker compose exec api python -m pytest -m "not rate_limit"

# Run only rate limiting tests
docker compose exec api python -m pytest -m rate_limit
```

### Utility Scripts

```bash
# List all users
docker compose exec api python -m backend.app.scripts.list_users

# Reset a user password
docker compose exec api python -m backend.app.scripts.reset_password

# Delete all users (careful!)
docker compose exec api python -m backend.app.scripts.delete_all_users

# Validate password
docker compose exec api python -m backend.app.scripts.validate_password
```

### Development Workflow

```bash
# View logs
docker compose logs -f api

# Access API shell
docker compose exec api bash

# Access MySQL shell
docker compose exec db mysql -u root -p

# Rebuild containers
docker compose down && docker compose build && docker compose up

# Clean rebuild (remove volumes)
docker compose down -v && docker compose up --build

# Check API health
curl http://localhost:8000/health

# View API documentation
open http://localhost:8000/docs
```

## Architecture

### API Design

The application uses a **dual API approach**:

1. **RESTful JSON APIs** (`/api/v1/users/`, `/api/v1/chores/`) - Traditional CRUD operations
2. **HTML Component APIs** (`/api/v1/html/`) - HTMX-powered dynamic UI updates

Both API types share the same business logic through the service layer.

### Core Components

1. **Authentication Flow**
   - JWT tokens via OAuth2 Password Bearer
   - Parent/child role-based access control
   - Token stored in localStorage, sent via Authorization header
   - Dependency injection pattern for current user

2. **Data Access Layer**
   - Service layer for business logic
   - Repository pattern with async support
   - Type-safe generics using Python TypeVar
   - Base repository for common CRUD operations
   - Domain-specific extensions for data access

3. **Chore Workflow State Machine**
   - **Created**: Parent creates and assigns to child
   - **Pending**: Child marks complete, awaits approval
   - **Approved**: Parent approves with reward amount
   - **Cooldown**: Recurring chores enter cooldown period
   - **Disabled**: Soft delete for inactive chores

4. **HTMX Integration**
   - Server-side rendering with component templates
   - Progressive enhancement with JavaScript
   - Real-time updates via HTMX swaps
   - Mixed content type handling (JSON/form data)

### Key Patterns

- **Dependency Injection**: Extensive use of FastAPI's `Depends()`
- **Async-First**: All database operations are async
- **Schema Separation**: Pydantic models separate from ORM models
- **Template Inheritance**: Base layout with blocks
- **Role-Based UI**: Different views for parents vs children

### Business Rules

- Only parents can create, approve, and disable chores
- Only assigned children can mark chores complete
- Range rewards require exact amount during approval
- Cooldown periods prevent immediate re-completion
- Children only see their own assigned chores

## Environment Variables

Required variables (see `.env.sample`):

- `MYSQL_HOST`: Database host
- `MYSQL_USER`: Database user
- `MYSQL_PASSWORD`: Database password
- `MYSQL_DATABASE`: Database name
- `SECRET_KEY`: JWT signing key
- `ALGORITHM`: JWT algorithm (default: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration

## Future Development - Pending Phases

### Phase 2: Medium Priority Items ✅
1. ~~**Unit of Work Pattern** - Transaction management (COMPLETED)~~
2. ~~**API Documentation** - Enhanced OpenAPI specs (COMPLETED)~~

### Remaining Phase 2 Items ⏳
1. **Refresh Tokens** - Enhanced security with token rotation
2. **Rate Limiting** - Already implemented, needs testing
3. **Database Optimization** - Add indexes, query caching

### Phase 3: Low Priority Items ⏳
1. **Extract HTML Templates** - Move inline HTML to files
2. **Monitoring** - Add OpenTelemetry
3. **Performance** - Add Redis caching
4. **WebSocket Support** - Real-time updates for chore completions

See `MODERNIZATION_ROADMAP.md` for detailed implementation plans.