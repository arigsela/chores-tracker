# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Chores Tracker** is a full-stack family chore management application with:
- **Backend**: FastAPI (Python 3.11) with SQLAlchemy 2.0, MySQL database
- **Frontend**: React Native Web frontend with 90% feature parity
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

### Frontend (React Native Web)

- **Location**: `frontend/` directory
- **Technology**: React Native Web with Expo
- **Components**: (`frontend/src/components/`): Reusable React components
- **Screens**: (`frontend/src/screens/`): Main application screens
- **Navigation**: React Navigation with stack/tab navigators
- **State**: Context API for authentication and global state
- **API Integration**: Axios client with JWT token management
- **Styling**: React Native StyleSheet and custom styles

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
# Backend API: http://localhost:8000
# Frontend Web: http://localhost:8081
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

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run web

# Run tests
npm test

# Type checking
npm run type-check

# Linting
npm run lint

# Build for production
npm run build
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

### Performance & Monitoring

```bash
# Run tests with coverage
docker compose exec api python -m pytest --cov=backend/app --cov-report=html

# Check database connection health
docker compose exec mysql mysqladmin ping -h localhost -u root -p

# View application logs
docker compose logs api -f
docker compose logs mysql -f

# Monitor container resources
docker compose top
```

## Testing Strategy

### Backend Testing
- **Unit tests**: Test services, repositories in isolation
- **Integration tests**: Test API endpoints with test database
- **Test database**: Uses SQLite in-memory for speed
- **Fixtures**: See `backend/tests/conftest.py` for common test fixtures
- **Coverage target**: >70% for critical business logic

### Frontend Testing
- **Unit tests**: Components and utility functions
- **Integration tests**: API integration and user workflows
- **Test framework**: Jest with React Native Testing Library
- **Coverage**: Available with `npm run test:coverage`

### Key Test Patterns
```bash
# Backend testing
TESTING=true python3 -m pytest
python -m pytest -v  # Verbose
python -m pytest --tb=short  # Short traceback
python -m pytest -x  # Stop on first failure

# Frontend testing
cd frontend
npm test  # Run all tests
npm run test:watch  # Watch mode
npm run test:coverage  # With coverage
npm run test:unit  # Unit tests only
npm run test:integration  # Integration tests only
```

## Important Implementation Details

### React Native Web Frontend
The frontend uses React Native Web for cross-platform compatibility:
```typescript
// API client configuration
const apiClient = axios.create({
  baseURL: process.env.NODE_ENV === 'development' 
    ? 'http://localhost:8000/api/v1'
    : '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});
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

## Migration Status (August 2025)

**HTMX Frontend Retirement Complete**: The original HTMX/server-side rendered UI has been fully deprecated and removed in favor of React Native Web frontend.

### Architecture Changes
- Backend now serves JSON-only API responses (no HTML rendering)
- Frontend runs as separate React Native Web application on port 8081
- Mobile app and web frontend share common React Native components
- 90% feature parity achieved with original HTMX implementation

### Development Impact
- **Two-server setup**: Backend (8000) + Frontend (8081)
- **API-first approach**: All business logic exposed via REST endpoints
- **Unified codebase**: Mobile and web share components and logic

## Common Troubleshooting

### Frontend Can't Connect to Backend
- Ensure backend is running on http://localhost:8000
- Check CORS settings in backend/app/main.py
- Verify API_URL configuration in frontend config

### Authentication Issues
- Check JWT token storage in frontend
- Verify token expiry (8-day default)
- Ensure proper Authorization header format

### Database Connection Issues
Ensure MySQL is healthy: `docker compose exec mysql mysqladmin ping -h localhost -u root -p`

### Mobile App Can't Connect to Backend
- Use `API_URL=http://localhost:8000/api/v1` for local development
- Check CORS settings in backend
- For iOS simulator, use localhost; for device, use computer's IP address

## Domain Concepts

### User Hierarchy
- **Parents**: Can create children, chores, approve completions
- **Children**: Can view assigned chores, mark complete, view balance

### Multi-Assignment Chore System

The application supports three distinct chore assignment patterns to accommodate different family chore scenarios:

#### Assignment Modes

**1. Single Assignment** (`assignment_mode='single'`)
- **Use Case**: Traditional one-child-one-chore assignment (backward compatible)
- **Requirements**: Exactly 1 assignee_id required
- **Example**: "Clean the garage" assigned to Alice
- **Behavior**:
  - Only the assigned child sees the chore
  - Child completes → parent approves → child's balance increases
  - For recurring chores: assignment resets after cooldown period

**2. Multi-Independent** (`assignment_mode='multi_independent'`)
- **Use Case**: Personal chores where each child does their own version
- **Requirements**: 1 or more assignee_ids required
- **Example**: "Clean your room" assigned to Alice, Bob, and Charlie
- **Behavior**:
  - Each child sees the chore in their list
  - Each child completes independently
  - Parent approves each completion separately
  - Each child's balance increases independently
  - For recurring: each assignment resets independently after cooldown

**3. Unassigned Pool** (`assignment_mode='unassigned'`)
- **Use Case**: Shared household chores, first-come-first-served
- **Requirements**: 0 assignee_ids (no initial assignment)
- **Example**: "Walk the dog", "Take out trash"
- **Behavior**:
  - All children in family see chore in "Available Pool"
  - First child to complete "claims" the chore (creates assignment)
  - Other children no longer see it
  - Parent approves → child's balance increases
  - For recurring: assignment deleted after cooldown, returns to pool

#### Assignment Lifecycle

```
Create Chore → Assignment(s) Created → Child Completes → Parent Approves → Balance Updated
                                                             ↓
                                                    (Recurring chores)
                                                             ↓
                                              Cooldown Period → Reset/Return to Pool
```

#### Database Schema

- **chores** table: Contains `assignment_mode` field
- **chore_assignments** junction table: Many-to-many relationship
  - `chore_id`: Foreign key to chores
  - `assignee_id`: Foreign key to users (children)
  - `is_completed`: Completion status per-assignment
  - `is_approved`: Approval status per-assignment
  - `completion_date`: When child completed
  - `approval_date`: When parent approved
  - `approval_reward`: Final reward amount (for range rewards)
  - `rejection_reason`: If parent rejected, why

#### API Examples

**Creating a Single Mode Chore**:
```python
POST /api/v1/chores/
{
  "title": "Mow the lawn",
  "description": "Front and back yard",
  "reward": 15.0,
  "assignment_mode": "single",
  "assignee_ids": [child_id]
}
```

**Creating a Multi-Independent Chore**:
```python
POST /api/v1/chores/
{
  "title": "Clean your room",
  "description": "Organize, vacuum, dust",
  "reward": 5.0,
  "is_recurring": true,
  "cooldown_days": 7,
  "assignment_mode": "multi_independent",
  "assignee_ids": [child1_id, child2_id, child3_id]
}
```

**Creating an Unassigned Pool Chore**:
```python
POST /api/v1/chores/
{
  "title": "Walk the dog",
  "description": "30 minute walk",
  "reward": 3.0,
  "is_recurring": true,
  "cooldown_days": 1,
  "assignment_mode": "unassigned",
  "assignee_ids": []
}
```

**Range Rewards** (all modes):
```python
POST /api/v1/chores/
{
  "title": "Help with homework",
  "reward": 5.0,  # Default/suggested amount
  "is_range_reward": true,
  "min_reward": 3.0,
  "max_reward": 10.0,
  "assignment_mode": "single",
  "assignee_ids": [child_id]
}

# Parent sets final reward on approval
POST /api/v1/assignments/{assignment_id}/approve
{
  "reward_value": 7.5  # Must be between min_reward and max_reward
}
```

#### Service Layer Patterns

**ChoreService Methods**:
- `create_chore(db, creator_id, chore_data)`: Creates chore + assignments based on mode
- `complete_chore(db, chore_id, user_id)`: Marks assignment complete (or claims for pool)
- `approve_assignment(db, assignment_id, parent_id, reward_value?)`: Approves specific assignment
- `reject_assignment(db, assignment_id, parent_id, rejection_reason)`: Rejects with feedback
- `get_available_chores(db, child_id)`: Returns `{assigned: [...], pool: [...]}`
- `get_pending_approval(db, parent_id)`: Returns assignment-level data

**Repository Pattern**:
- `ChoreRepository`: CRUD for chores, queries by creator/family
- `ChoreAssignmentRepository`: CRUD for assignments, cooldown logic, availability queries
- `UserRepository`: User management, get_children()

### Chore Lifecycle (Updated)
1. Parent creates chore with assignment mode and assignee(s)
2. Assignment(s) created automatically based on mode
3. Child(ren) mark assignments as completed
4. Parent approves/rejects each assignment individually
5. Approved assignments increase child's balance
6. Recurring chores reset after cooldown (mode-specific behavior)

### Reward Adjustments
Parents can manually adjust child balances for bonuses/penalties outside normal chore flow

## Code Style Guidelines

- **Python**: Follow PEP 8, use type hints, async/await patterns
- **SQL**: Use SQLAlchemy 2.0 async patterns
- **TypeScript**: Use strict typing, interface definitions
- **React Native**: Functional components with hooks, consistent styling patterns

## Security Considerations

- JWT tokens expire after 8 days
- Passwords hashed with bcrypt
- Role-based access control (parent/child)
- Rate limiting on auth endpoints
- Input validation with Pydantic