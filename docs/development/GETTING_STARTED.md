# Getting Started - Developer Onboarding

**Target Time**: 30 minutes to first code change
**Last Updated**: January 23, 2026

---

## Welcome to Chores Tracker!

This guide will get you from zero to making your first code change, writing your first test, and submitting your first pull request in about 30 minutes.

## Table of Contents
- [Prerequisites](#prerequisites)
- [30-Minute Quick Start](#30-minute-quick-start)
- [Your First Code Change](#your-first-code-change)
- [Writing Your First Test](#writing-your-first-test)
- [Submitting Your First PR](#submitting-your-first-pr)
- [Development Workflow](#development-workflow)
- [Getting Help](#getting-help)

---

## Prerequisites

Before you begin, ensure you have:

### Required
- **Docker Desktop** 20.10+ and **Docker Compose** 2.0+
  - [Download Docker Desktop](https://www.docker.com/products/docker-desktop)
  - Verify: `docker --version` and `docker compose version`
- **Node.js** 18+ and **npm** 9+
  - [Download Node.js](https://nodejs.org/)
  - Verify: `node --version` and `npm --version`
- **Git** for version control
  - Verify: `git --version`

### Optional but Recommended
- **VS Code** with extensions:
  - Python (ms-python.python)
  - TypeScript React Native Tools
  - Docker
  - GitLens
- **Tilt** for hot-reloading development
  - [Install Tilt](https://docs.tilt.dev/install.html)

### Knowledge Prerequisites
- Basic Python (we use FastAPI and async/await)
- Basic React/TypeScript (for frontend work)
- Basic SQL/databases (we use MySQL and SQLAlchemy)
- Basic Docker concepts

---

## 30-Minute Quick Start

### Step 1: Clone and Setup (5 minutes)

```bash
# Clone the repository
git clone https://github.com/arigsela/chores-tracker.git
cd chores-tracker

# Create your environment file
cp .env.sample .env

# Generate a secure secret key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# Copy the output and add to .env as SECRET_KEY=<your-key-here>
```

**Edit `.env`** with minimal required values:
```bash
SECRET_KEY=<your-generated-key>
MYSQL_ROOT_PASSWORD=devpassword
MYSQL_DATABASE=chores_tracker
MYSQL_USER=chores_user
MYSQL_PASSWORD=devpassword
DATABASE_URL=mysql+aiomysql://chores_user:devpassword@mysql:3306/chores_tracker
```

### Step 2: Start the Backend (5 minutes)

```bash
# Start MySQL and FastAPI backend
docker compose up -d

# Wait for MySQL to be ready (about 30 seconds)
docker compose logs mysql | grep "ready for connections"

# Run database migrations
docker compose exec api python -m alembic -c backend/alembic.ini upgrade head

# Verify backend is running
curl http://localhost:8000/health
# Should return: {"status": "healthy"}
```

**Check the interactive API docs**: Open http://localhost:8000/docs in your browser

### Step 3: Start the Frontend (5 minutes)

```bash
# In a new terminal window
cd frontend

# Install dependencies (first time only)
npm install

# Start the development server
npm run web
```

**Access the application**: Open http://localhost:8081 in your browser

### Step 4: Create Your First User (5 minutes)

**Option A: Using the Web UI**
1. Navigate to http://localhost:8081
2. Click "Register"
3. Create a parent account with:
   - Username: `testparent`
   - Email: `parent@example.com`
   - Password: `password123`
   - Check "I am a parent"

**Option B: Using the CLI**
```bash
docker compose exec api python -m backend.app.scripts.create_parent_user
# Follow the prompts to create a parent user
```

**Login** with your new credentials and explore the dashboard!

### Step 5: Run the Tests (5 minutes)

```bash
# Backend tests
docker compose exec api python -m pytest -v

# Frontend tests
cd frontend
npm test

# You should see all tests passing ✅
```

**Congratulations!** You now have a fully functional local development environment.

### Step 6: Understand the Architecture (5 minutes)

**Quick Architecture Overview:**
```
Frontend (http://localhost:8081)
    ↓ REST API calls
Backend (http://localhost:8000)
    ↓ SQL queries
MySQL Database (port 3306)
```

**Key Directories:**
- `backend/app/` - FastAPI application code
  - `models/` - Database models (SQLAlchemy)
  - `schemas/` - Request/response validation (Pydantic)
  - `services/` - Business logic
  - `repositories/` - Data access layer
  - `api/api_v1/endpoints/` - API route handlers
- `frontend/src/` - React Native Web application
  - `screens/` - Main application views
  - `components/` - Reusable UI components
  - `navigation/` - App navigation structure

**Read Next:**
- [BACKEND_ARCHITECTURE.md](/Users/arisela/git/chores-tracker/docs/architecture/BACKEND_ARCHITECTURE.md) for detailed backend architecture
- [CODEBASE_OVERVIEW.md](/Users/arisela/git/chores-tracker/docs/architecture/CODEBASE_OVERVIEW.md) for complete codebase walkthrough

---

## Your First Code Change

Let's make a simple but meaningful change: adding a new field to display the user's creation date on the dashboard.

### Backend Change: Add Created Date to User Response

**File**: `backend/app/schemas/user.py`

```python
# Find the UserResponse schema (around line 40)
class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    is_active: bool
    balance: Optional[float] = 0.0
    created_at: datetime  # ADD THIS LINE
```

The `created_at` field already exists in the database model (`backend/app/models/user.py`), so we're just exposing it in the API response.

### Test Your Change

```bash
# Restart the backend to pick up code changes
docker compose restart api

# Check the API docs
# Open http://localhost:8000/docs
# Navigate to GET /api/v1/users/me
# Click "Try it out" → "Execute"
# You should now see "created_at" in the response
```

### Frontend Change: Display Creation Date

**File**: `frontend/src/screens/DashboardScreen.tsx`

Find the user info section (around line 50) and add:

```typescript
<Text style={styles.infoText}>
  Member since: {new Date(user.created_at).toLocaleDateString()}
</Text>
```

### Test Your Frontend Change

```bash
# The frontend hot-reloads automatically
# Refresh http://localhost:8081
# You should see "Member since: [date]" on the dashboard
```

**Congratulations!** You just made your first full-stack change.

---

## Writing Your First Test

Let's write a test for the change you just made.

### Backend Test: Verify Created Date in Response

**File**: `backend/tests/api/v1/test_users.py`

Add this test function:

```python
import pytest
from datetime import datetime

@pytest.mark.asyncio
async def test_user_response_includes_created_at(client, test_parent_user, parent_auth_headers):
    """Test that user response includes created_at field."""
    response = await client.get("/api/v1/users/me", headers=parent_auth_headers)

    assert response.status_code == 200
    data = response.json()

    # Verify created_at is present
    assert "created_at" in data

    # Verify it's a valid ISO datetime string
    created_at = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
    assert isinstance(created_at, datetime)

    # Verify it's a recent date (within last hour)
    now = datetime.now()
    time_diff = (now - created_at).total_seconds()
    assert time_diff < 3600  # Less than 1 hour ago
```

### Run Your New Test

```bash
docker compose exec api python -m pytest backend/tests/api/v1/test_users.py::test_user_response_includes_created_at -v
```

You should see:
```
backend/tests/api/v1/test_users.py::test_user_response_includes_created_at PASSED
```

### Frontend Test: Verify Date Display

**File**: `frontend/src/screens/__tests__/DashboardScreen.test.tsx`

```typescript
import { render, screen } from '@testing-library/react-native';
import DashboardScreen from '../DashboardScreen';

describe('DashboardScreen', () => {
  it('displays user creation date', () => {
    const mockUser = {
      id: 1,
      username: 'testuser',
      created_at: '2026-01-01T00:00:00Z',
      // ... other required fields
    };

    render(<DashboardScreen user={mockUser} />);

    expect(screen.getByText(/Member since:/)).toBeTruthy();
  });
});
```

### Run Frontend Tests

```bash
cd frontend
npm test -- DashboardScreen.test.tsx
```

**Testing Best Practices:**
- Write tests BEFORE making changes (TDD approach)
- Test both success and error cases
- Keep tests focused and independent
- Use descriptive test names

**Learn More**: See [TESTING_STRATEGY.md](/Users/arisela/git/chores-tracker/docs/development/TESTING_STRATEGY.md)

---

## Submitting Your First PR

### Step 1: Create a Feature Branch

```bash
# Make sure you're on main and up to date
git checkout main
git pull origin main

# Create a feature branch
git checkout -b feature/add-user-creation-date

# Verify you're on the new branch
git branch
```

**Branch Naming Convention:**
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring

### Step 2: Commit Your Changes

```bash
# Add your changes
git add backend/app/schemas/user.py
git add frontend/src/screens/DashboardScreen.tsx
git add backend/tests/api/v1/test_users.py
git add frontend/src/screens/__tests__/DashboardScreen.test.tsx

# Commit with a descriptive message
git commit -m "feat: add user creation date to dashboard

- Add created_at field to UserResponse schema
- Display 'Member since' date on dashboard
- Add backend test for created_at in API response
- Add frontend test for date display component

Closes #123"
```

**Commit Message Format:**
```
<type>: <short summary>

<detailed description>

<footer with issue references>
```

**Types**: `feat`, `fix`, `docs`, `test`, `refactor`, `style`, `chore`

### Step 3: Push Your Branch

```bash
# Push to your fork (or origin if you have write access)
git push origin feature/add-user-creation-date
```

### Step 4: Create Pull Request

1. Go to https://github.com/arigsela/chores-tracker/pulls
2. Click "New Pull Request"
3. Select your branch: `feature/add-user-creation-date`
4. Fill in the PR template:

```markdown
## Summary
Adds user creation date display to the dashboard, allowing users to see when they joined.

## Changes
- Added `created_at` field to UserResponse schema
- Updated DashboardScreen to display "Member since" date
- Added backend and frontend tests for new functionality

## Type of Change
- [x] New feature
- [ ] Bug fix
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [x] Backend tests pass (`pytest`)
- [x] Frontend tests pass (`npm test`)
- [x] Manually tested on local environment
- [x] Verified in browser at http://localhost:8081

## Screenshots
[Add a screenshot of the dashboard showing the new date]

## Checklist
- [x] Code follows project style guidelines
- [x] Tests added for new functionality
- [x] Documentation updated (if needed)
- [x] No breaking changes introduced
```

### Step 5: Wait for Review

- **CI/CD checks** will run automatically
- A maintainer will review your PR
- Address any feedback with additional commits
- Once approved, your PR will be merged!

**PR Best Practices:**
- Keep PRs small and focused (< 400 lines changed)
- Write clear descriptions
- Respond to review comments promptly
- Don't force-push after review starts

---

## Development Workflow

### Daily Development Cycle

```bash
# 1. Start your day
git checkout main
git pull origin main

# 2. Create feature branch
git checkout -b feature/my-new-feature

# 3. Start development environment
docker compose up -d
cd frontend && npm run web

# 4. Make changes
# - Edit code in your IDE
# - Backend: Save files, Docker auto-reloads
# - Frontend: Save files, browser auto-refreshes

# 5. Test frequently
docker compose exec api python -m pytest backend/tests/test_myfeature.py
cd frontend && npm test

# 6. Commit when ready
git add .
git commit -m "feat: implement my feature"

# 7. Push and create PR
git push origin feature/my-new-feature
```

### Common Development Tasks

**View Logs:**
```bash
# Backend logs
docker compose logs api -f

# Database logs
docker compose logs mysql -f

# All services
docker compose logs -f
```

**Database Operations:**
```bash
# Access MySQL shell
docker compose exec mysql mysql -u root -p

# Run migrations
docker compose exec api python -m alembic -c backend/alembic.ini upgrade head

# Create new migration
docker compose exec api python -m alembic -c backend/alembic.ini revision --autogenerate -m "add new field"
```

**Reset Everything:**
```bash
# Stop all services
docker compose down

# Remove all data (fresh start)
docker compose down -v

# Rebuild and start
docker compose up --build
```

**Run Specific Tests:**
```bash
# Single test file
docker compose exec api python -m pytest backend/tests/test_services.py -v

# Single test function
docker compose exec api python -m pytest backend/tests/test_services.py::test_create_chore -v

# Tests matching pattern
docker compose exec api python -m pytest -k "chore" -v

# With coverage
docker compose exec api python -m pytest --cov=backend/app --cov-report=html
```

### IDE Setup (VS Code)

**Recommended Settings** (`.vscode/settings.json`):
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/backend/.venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "typescript.tsdk": "frontend/node_modules/typescript/lib"
}
```

**Recommended Extensions:**
- Python (ms-python.python)
- Pylance (ms-python.vscode-pylance)
- Docker (ms-azuretools.vscode-docker)
- ESLint (dbaeumer.vscode-eslint)
- React Native Tools (msjsdiag.vscode-react-native)
- GitLens (eamodio.gitlens)

### Debugging

**Backend Debugging:**
```python
# Add breakpoints with pdb
import pdb; pdb.set_trace()

# Or use VS Code debugger
# See .vscode/launch.json for configuration
```

**Frontend Debugging:**
- Use browser DevTools (F12)
- React DevTools extension
- Network tab for API calls
- Console for logs

**API Debugging:**
- Use http://localhost:8000/docs (Swagger UI)
- Test endpoints interactively
- See request/response schemas
- Copy curl commands

---

## Getting Help

### Documentation Resources

**Essential Docs:**
- [README.md](/Users/arisela/git/chores-tracker/README.md) - Project overview
- [CLAUDE.md](/Users/arisela/git/chores-tracker/CLAUDE.md) - Development commands reference
- [BACKEND_ARCHITECTURE.md](/Users/arisela/git/chores-tracker/docs/architecture/BACKEND_ARCHITECTURE.md) - Backend architecture deep dive
- [GLOSSARY.md](/Users/arisela/git/chores-tracker/docs/GLOSSARY.md) - Domain terminology

**API Documentation:**
- Interactive: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- [JWT_AUTH_EXPLAINER.md](/Users/arisela/git/chores-tracker/docs/api/JWT_AUTH_EXPLAINER.md) - Authentication guide

**Development Guides:**
- [ENVIRONMENT_SETUP.md](/Users/arisela/git/chores-tracker/docs/development/ENVIRONMENT_SETUP.md) - Detailed environment setup
- [PYTHON_FASTAPI_CONCEPTS.md](/Users/arisela/git/chores-tracker/docs/development/PYTHON_FASTAPI_CONCEPTS.md) - FastAPI patterns
- [TESTING_STRATEGY.md](/Users/arisela/git/chores-tracker/docs/development/TESTING_STRATEGY.md) - Testing guidelines

### Common Issues and Solutions

**"Port already in use" error:**
```bash
# Find what's using the port
lsof -i :8000  # Backend
lsof -i :8081  # Frontend

# Kill the process or stop Docker
docker compose down
```

**"Database connection failed":**
```bash
# Check if MySQL is running
docker compose ps mysql

# Check MySQL logs
docker compose logs mysql

# Restart MySQL
docker compose restart mysql
```

**"Module not found" errors (Python):**
```bash
# Rebuild the container
docker compose up --build api
```

**"Module not found" errors (Node):**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Tests failing:**
```bash
# Run with verbose output
docker compose exec api python -m pytest -vv

# Check for environment issues
docker compose exec api env | grep TESTING
# Should show TESTING=true
```

### Getting Support

**Before Asking for Help:**
1. Check the error message carefully
2. Search existing documentation
3. Check GitHub issues for similar problems
4. Try the "Common Issues" section above

**Where to Ask:**
- GitHub Issues: https://github.com/arigsela/chores-tracker/issues
- GitHub Discussions: For questions and ideas
- Code Reviews: PR comments for code-specific questions

**When Reporting Issues:**
- Include error messages (full stack trace)
- Describe what you were trying to do
- Share relevant code snippets
- Mention your environment (OS, Docker version, etc.)

---

## Next Steps

Now that you've completed the quick start, consider:

1. **Explore the Codebase:**
   - Read [CODEBASE_OVERVIEW.md](/Users/arisela/git/chores-tracker/docs/architecture/CODEBASE_OVERVIEW.md)
   - Understand the multi-assignment chore system
   - Review the service layer architecture

2. **Pick a Real Issue:**
   - Browse [Good First Issues](https://github.com/arigsela/chores-tracker/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)
   - Try implementing a small feature
   - Fix a bug or add a test

3. **Learn the Stack:**
   - [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)
   - [React Native Web Docs](https://necolas.github.io/react-native-web/)
   - [SQLAlchemy 2.0 Tutorial](https://docs.sqlalchemy.org/en/20/tutorial/)

4. **Understand the Workflows:**
   - Read [RELEASING.md](/Users/arisela/git/chores-tracker/RELEASING.md) for release process
   - Review CI/CD pipeline in `.github/workflows/`
   - Learn about our deployment to Kubernetes

**Welcome to the team! Happy coding! 🚀**

---

**Last Updated**: January 23, 2026
**Maintainer**: Development Team
**Feedback**: Open an issue or PR to improve this guide
