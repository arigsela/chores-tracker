## Chores Tracker — Codebase Overview and Functionality

This document explains what the application does, how it is structured, and how the main parts work together. It covers core user flows (parents/children), API endpoints, data models, services/repositories, frontend (React Native Web), mobile app, and infrastructure.

### What the app does
- **Family chore management** with two roles:
  - **Parents**: create/assign chores, approve completed chores (set rewards), manage children, apply reward adjustments.
  - **Children**: view assigned chores, complete them, see their earned balance.
- **Rewards**: fixed or range-based (parent picks the final amount upon approval).
- **Recurring chores**: cooldown-driven recurrence (e.g., daily/weekly via `cooldown_days`).
- **Balances**: derived from approved chores + adjustments − paid out (paid out is a placeholder for now).
- **Web UI**: React Native Web frontend with responsive design.
- **Mobile app**: React Native client for iOS/Android sharing components with web.

---

## Architecture at a glance
- **Backend**: FastAPI + SQLAlchemy 2.0 (async) + Pydantic v2
  - Service-layer + repository pattern
  - JWT authentication, rate limiting, request validation middleware
  - Prometheus metrics for monitoring and observability
- **Web UI**: React Native Web (`frontend/`) with Expo, running on port 8081
- **Mobile**: React Native app (`mobile/`) for iOS/Android with 90% code sharing with web
- **Infra**: Docker Compose for local dev; CI/CD and deployment scripts in repo

Key directories:
- `backend/app/`
  - `main.py`: app wiring, routers, and JSON API endpoints
  - `api/api_v1/`: versioned JSON API routers/endpoints
  - `models/`: SQLAlchemy ORM models (`user.py`, `chore.py`, `chore_assignment.py`, `family.py`, `activity.py`, `reward_adjustment.py`)
  - `schemas/`: Pydantic models for request/response validation
  - `repositories/`: data access layer
  - `services/`: business logic layer
  - `dependencies/`: DI providers (services, auth)
  - `middleware/`: rate limiting and request validation
  - `db/`: engine/session setup and base class
  - `core/`: metrics, security, configuration
- `frontend/`: React Native Web application
  - `src/components/`: reusable UI components
  - `src/screens/`: main application screens
  - `src/navigation/`: React Navigation setup
  - `src/contexts/`: React Context for state management
- `mobile/`: React Native mobile application
- `docs/`: architecture and implementation documentation

---

## Data model
- `User`
  - Fields: `id`, `email`, `username`, `hashed_password`, `is_active`, `is_parent`, `parent_id`, `family_id`, `registration_code`
  - Relationships: `children`, `parent`, `family`, `assignments`, `chores_created`, `adjustments_received`, `adjustments_created`, `activities`
- `Chore`
  - Fields: `id`, `title`, `description`, `assignment_mode` (single/multi_independent/unassigned), reward fields (`reward`, `min_reward`, `max_reward`, `is_range_reward`), recurrence (`cooldown_days`, `is_recurring`, `frequency`), lifecycle (`is_disabled`, `completion_date`), `creator_id`, `family_id`, timestamps
  - Relationships: `assignments` (many-to-many through ChoreAssignment), `creator`, `family`
- `ChoreAssignment` (junction table for many-to-many)
  - Fields: `id`, `chore_id`, `assignee_id`, `is_completed`, `is_approved`, `completion_date`, `approval_date`, `approval_reward`, `rejection_reason`, timestamps
  - Purpose: Tracks individual assignments in multi-assignment system
- `Family`
  - Fields: `id`, `name`, `invite_code` (unique), `created_by_id`, timestamps
  - Relationships: `members` (users), `chores`, `creator`
  - Purpose: Groups users and chores for multi-family support
- `Activity`
  - Fields: `id`, `user_id`, `activity_type`, `description`, `metadata` (JSON), `timestamp`
  - Purpose: Audit log for all system actions
- `RewardAdjustment`
  - Fields: `id`, `child_id`, `parent_id`, `amount` (Decimal), `reason`, `created_at`

Notes:
- **Multi-assignment system**: Chores support three modes via `assignment_mode` field and ChoreAssignment junction table
- Recurring chores are driven by `cooldown_days` (e.g., 1 day ≈ daily, 7 days ≈ weekly). Approval sets `approval_date`; child availability respects cooldown.
- Range rewards require a final `approval_reward` during approval via ChoreAssignment.
- Families enable multi-family deployments with invite codes for joining.

---

## API layers

### Auth
- JWT-based via `OAuth2PasswordBearer` and `verify_token`
- Login endpoint returns a token; set `Authorization: Bearer <token>` for subsequent calls.

### Versioned JSON API (under `settings.API_V1_STR`, default `/api/v1`)
Routers are defined in `backend/app/api/api_v1/` and wired in `backend/app/main.py`.

- `users` (`/api/v1/users`)
  - `POST /register` (form): Parent or child registration (child requires parent context)
  - `POST /login` (form-encoded): Returns JWT
  - `POST /` (JSON): Create user (parents only; used to create children via API)
  - `GET /`: List users (dev convenience)
  - `GET /children/{parent_id}`: Children for a parent (dev convenience)
  - `POST /children/{child_id}/reset-password` (JSON): Reset child password (parent only)

- `chores` (`/api/v1/chores`)
  - `POST /`: Create a chore with assignment_mode (JSON) — parents only
  - `GET /`: Chores visible to current user (parents: chores they created; children: their chores)
  - `GET /available`: Available chores for child (children only)
  - `GET /pending-approval`: Completed but unapproved chores (parents only)
  - `GET /child/{child_id}`: Parent views of a child's chores
  - `GET /{chore_id}`: Chore details with access checks
  - `PUT /{chore_id}`: Update chore (parent creator only)
  - `DELETE /{chore_id}`: Hard delete (parent creator only)
  - `POST /{chore_id}/complete`: Mark complete or claim unassigned chore (child only; cooldown checks)
  - `POST /{chore_id}/disable`: Soft delete (parent creator only)

- `assignments` (`/api/v1/assignments`)
  - `GET /`: List all assignments for current user
  - `GET /{assignment_id}`: Get specific assignment details
  - `POST /{assignment_id}/approve`: Approve assignment (parent only; range reward validation)
  - `POST /{assignment_id}/reject`: Reject assignment with reason (parent only)
  - `DELETE /{assignment_id}`: Delete assignment (admin only)

- `families` (`/api/v1/families`)
  - `POST /`: Create a new family (parent only)
  - `GET /`: Get current user's family
  - `POST /join`: Join family via invite code
  - `GET /{family_id}/members`: List family members (family member only)
  - `PUT /{family_id}`: Update family details (creator only)

- `activities` (`/api/v1/activities`)
  - `GET /`: List activities for current user (paginated)
  - `GET /family`: List activities for entire family (parent only)
  - `GET /{activity_id}`: Get specific activity details

- `adjustments` (`/api/v1/adjustments`)
  - `POST /`: Create a reward adjustment (parent only; amount non-zero; only own children)
  - `GET /child/{child_id}`: Adjustments for a child (parent only, must be own child)
  - `GET /total/{child_id}`: Sum of a child's adjustments (parent only)

- `statistics` (`/api/v1/statistics`)
  - `GET /family`: Family-wide statistics (parent only)
  - `GET /child/{child_id}`: Child-specific statistics

- `health` (`/api/v1/health`)
  - `GET /`: Basic health check
  - `GET /detailed`: Detailed health with database status

- Misc in `main.py`
  - `GET /api/v1/healthcheck`: legacy health probe (redirects to /health)
  - `GET /api/v1/users/me`: current user
  - `GET /api/v1/users/me/balance`: child's balance snapshot (derived)
  - `GET /metrics`: Prometheus metrics endpoint (restricted access)

---

## Services and repositories
- `repositories/base.py`: generic CRUD with async `AsyncSession` and optional eager loading
- `repositories/user.py`: auth helpers, children, password reset, family membership
- `repositories/chore.py`: role-based queries, availability, enable/disable, cooldown filtering, multi-assignment support
- `repositories/chore_assignment.py`: assignment CRUD, approval/rejection, cooldown logic, availability queries
- `repositories/family.py`: family CRUD, invite code generation/validation, member management
- `repositories/activity.py`: activity logging, queries by user/family/type
- `repositories/reward_adjustment.py`: listing and totals
- `services/user_service.py`: registration constraints, authentication checks, parent/child validations, family registration workflow, password reset
- `services/chore_service.py`: chore creation with assignment_mode, access control, complete rules (including pool claiming), bulk operations, transactional patterns via `UnitOfWork`
- `services/chore_assignment_service.py`: assignment lifecycle, approval/rejection with range reward validation, cooldown enforcement
- `services/family_service.py`: family creation, invite code management, member joining
- `services/activity_service.py`: activity logging for audit trail
- `services/reward_adjustment_service.py`: parent-only validations, permissions, totals
- `core/unit_of_work.py`: transactional coordination across repositories
- `core/metrics.py`: Prometheus metrics instrumentation

Business rules (highlights):
- Only parents create/update/disable/delete chores they created.
- Multi-assignment system: single (1 assignee), multi_independent (multiple), unassigned (pool, first-come-first-served)
- Only the assigned child completes a chore; for unassigned pool, completion creates the assignment (claiming)
- Cooldown enforced for recurring chores at the assignment level
- Range rewards must be approved with a value within `[min_reward, max_reward]` via ChoreAssignment
- Parents can only adjust/view their own children's adjustments
- Family isolation: users only see/interact with chores/users in their family

---

## Authentication, rate limiting, validation
- **JWT**: `create_access_token`, `verify_token`; `dependencies/auth.py` resolves current user
- **Rate limiting**: `middleware/rate_limit.py` with SlowAPI
  - Stricter on auth; moderate for API; disabled in tests via no-op decorators
- **Request validation**: `middleware/request_validation.py`
  - Content-type, size limits, early JSON parse, basic sanitization helpers

---

## Frontend Architecture (React Native Web)

> **Historical Note**: The backend previously supported server-side HTML rendering with Jinja2 templates and HTMX (deprecated August 2024). The current architecture uses React Native Web for the web UI.

### Current Frontend Setup
- **Location**: `frontend/` directory (separate from backend)
- **Port**: 8081 (development server)
- **Technology Stack**:
  - React Native Web with Expo
  - React Navigation for routing
  - React Context API for state management
  - Axios for API communication
  - AsyncStorage for token persistence

### Key Components
- **Screens**: `src/screens/` - Main application views (Dashboard, Chores, Users, etc.)
- **Components**: `src/components/` - Reusable UI elements (ChoreCard, UserCard, etc.)
- **Navigation**: `src/navigation/` - Stack and tab navigators
- **Contexts**: `src/contexts/` - AuthContext for global auth state
- **API Client**: `src/api/` - Axios client with JWT token management

### Role-Based UI
- Parents see: child lists, approval queues, admin tools, family management, statistics
- Children see: available/pending chores, balance display, activity feed

### Authentication Flow
- JWT token stored in AsyncStorage (web) or localStorage (web fallback)
- Authorization header automatically added to all API requests
- Automatic token refresh and logout on 401/403

---

## Database and migrations
- **Engine/session**: `db/base.py` creates async engine and `AsyncSessionLocal`
- **Models**: imported by `db/base.py` before Alembic
- **Migrations**: Alembic configs in `backend/alembic.ini` and versions under `backend/alembic/versions/`

---

## Mobile app (React Native)
- Located in `mobile/` with `package.json`
- Uses React Navigation, AsyncStorage, Axios
- Dev scripts:
  - `npm run backend` to bring up Docker backend (from repo root)
  - `npm run dev:simulator` sets `API_URL=http://localhost:8000/api/v1` and runs iOS simulator
- Responsibilities:
  - Mirror core flows (auth, chores viewing/completing), with offline persistence helpers

---

## Infrastructure and local development
- `docker-compose.yml`: MySQL 5.7 + API service; maps `backend` volume for live code reload
- `Dockerfile`, `docker-entrypoint.sh`: containerized API
- `Tiltfile`: optional hot-reload dev experience
- Top-level `README.md`: quick start, testing, CI/CD overview, and recent feature highlights

Bring up the stack locally:
```bash
# Start backend (MySQL + API on port 8000)
docker-compose up

# In another terminal, start frontend (port 8081)
cd frontend
npm install
npm run web

# Access the application
# Web UI: http://localhost:8081
# Backend API: http://localhost:8000
# API docs: http://localhost:8000/docs
# Metrics: http://localhost:8000/metrics
```

Common backend dev tasks (inside the API container):
```bash
docker compose exec api python -m pytest
docker compose exec api python -m alembic -c backend/alembic.ini upgrade head
```

Common frontend dev tasks:
```bash
cd frontend
npm run web          # Start web development server
npm test             # Run tests
npm run type-check   # TypeScript type checking
npm run lint         # ESLint
```

---

## Security and permissions
- Passwords hashed with bcrypt (`passlib`)
- JWT tokens expire after 8 days (configurable)
- Role checks in endpoints and services enforce parent/child constraints
- Rate limiting on sensitive and write endpoints
- Request validation middleware for safer inputs

---

## Core user flows
- Registration
  - Parent self-registers (`POST /api/v1/users/register` with `is_parent=true`)
  - Creates or joins a family (via invite code)
  - Parent creates children (`POST /api/v1/users` JSON)
- Login
  - `POST /api/v1/users/login` returns JWT; stored in AsyncStorage; used by frontend API client
- Chore lifecycle (multi-assignment system)
  1) Parent creates a chore with `assignment_mode`:
     - **single**: one assignee, traditional workflow
     - **multi_independent**: multiple assignees, each completes independently
     - **unassigned**: pool chore, first child to complete claims it
  2) Child completes assignment (or claims from pool)
     - Creates/updates ChoreAssignment record
     - Activity logged for audit trail
  3) Parent approves via ChoreAssignment
     - Fixed reward: uses preset `reward`
     - Range reward: parent supplies `approval_reward` within `[min_reward, max_reward]`
  4) If recurring: cooldown starts at assignment level; becomes available again after cooldown
- Adjustments
  - Parent creates positive/negative adjustments with a reason; totals used in balance views
- Balances
  - Child balance = sum of approved ChoreAssignment.approval_reward + adjustments − paid out (paid out currently 0 in code)
- Activity logging
  - All actions logged to Activity table for audit trail and family feed

---

## Extensibility notes
- Add payouts: persist payouts and subtract from balances
- Add admin role and audit logging for sensitive operations
- Add caching/global rate limits and distributed limit storage
- Add refresh tokens and 2FA
- Expand reporting (monthly statements, payout history)

---

## References to key files

### Backend
- App entrypoint and routes: `backend/app/main.py`, `backend/app/api/api_v1/api.py`
- Endpoints: `backend/app/api/api_v1/endpoints/*.py`
- Models: `backend/app/models/*.py` (user, chore, chore_assignment, family, activity, reward_adjustment)
- Schemas: `backend/app/schemas/*.py`
- Services: `backend/app/services/*.py`
- Repositories: `backend/app/repositories/*.py`
- Auth: `backend/app/dependencies/auth.py`, `backend/app/core/security/jwt.py`, `backend/app/core/security/password.py`
- Middleware: `backend/app/middleware/*.py`
- Metrics: `backend/app/core/metrics.py`

### Frontend
- Web app: `frontend/src/`
- Components: `frontend/src/components/*.tsx`
- Screens: `frontend/src/screens/*.tsx`
- Navigation: `frontend/src/navigation/`
- API client: `frontend/src/api/`
- Contexts: `frontend/src/contexts/`

### Mobile
- Mobile app: `mobile/src/`
- Shared components with web where possible

### Infrastructure
- Docker: `docker-compose.yml`, `Dockerfile`, `docker-entrypoint.sh`
- Tilt: `Tiltfile`
- Database migrations: `backend/alembic/`

This overview should give you a clear map of how the system is structured and how key features are implemented across the stack.