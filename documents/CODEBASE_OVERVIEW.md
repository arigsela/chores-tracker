## Chores Tracker — Codebase Overview and Functionality

This document explains what the application does, how it is structured, and how the main parts work together. It links core user flows (parents/children), API endpoints, data models, services/repositories, templates/HTMX, mobile app, and infrastructure.

### What the app does
- **Family chore management** with two roles:
  - **Parents**: create/assign chores, approve completed chores (set rewards), manage children, apply reward adjustments.
  - **Children**: view assigned chores, complete them, see their earned balance.
- **Rewards**: fixed or range-based (parent picks the final amount upon approval).
- **Recurring chores**: cooldown-driven recurrence (e.g., daily/weekly via `cooldown_days`).
- **Balances**: derived from approved chores + adjustments − paid out (paid out is a placeholder for now).
- **Web UI**: server-rendered HTML with HTMX for partial updates.
- **Mobile app**: React Native client consuming the same API.

---

## Architecture at a glance
- **Backend**: FastAPI + SQLAlchemy 2.0 (async) + Pydantic v2
  - Service-layer + repository pattern
  - JWT authentication, rate limiting, request validation middleware
- **Web UI**: Jinja2 templates with HTMX partial rendering and progressive enhancement
- **Mobile**: React Native app (`mobile`) with navigation, AsyncStorage, Axios
- **Infra**: Docker Compose for local dev; CI/CD and deployment scripts in repo

Key directories:
- `backend/app/`
  - `main.py`: app wiring, routers, HTML endpoints, and some JSON endpoints
  - `api/api_v1/`: versioned JSON API routers/endpoints
  - `models/`: SQLAlchemy ORM models (`user.py`, `chore.py`, `reward_adjustment.py`)
  - `schemas/`: Pydantic models for request/response validation
  - `repositories/`: data access layer
  - `services/`: business logic layer
  - `dependencies/`: DI providers (services, auth)
  - `middleware/`: rate limiting and request validation
  - `db/`: engine/session setup and base class
  - `templates/`: Jinja2 pages/components used by HTMX endpoints
- `mobile/`: React Native application
- `docs/` and `documents/`: documentation

---

## Data model
- `User`
  - Fields: `id`, `email`, `username`, `hashed_password`, `is_active`, `is_parent`, `parent_id`
  - Relationships: `children`, `parent`, `chores_assigned`, `chores_created`, adjustments (`adjustments_received`, `adjustments_created`)
- `Chore`
  - Fields: `id`, `title`, `description`, reward fields (`reward`, `min_reward`, `max_reward`, `is_range_reward`), recurrence (`cooldown_days`, `is_recurring`, `frequency`), lifecycle (`is_completed`, `is_approved`, `is_disabled`, `completion_date`), `assignee_id`, `creator_id`, timestamps
- `RewardAdjustment`
  - Fields: `id`, `child_id`, `parent_id`, `amount` (Decimal), `reason`, `created_at`

Notes:
- Recurring chores are driven by `cooldown_days` (e.g., 1 day ≈ daily, 7 days ≈ weekly). Approval sets `completion_date`; child availability respects cooldown.
- Range rewards require a final `reward_value` during approval.

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
  - `POST /`: Create a chore (form or JSON) — parents only
  - `GET /`: Chores visible to current user (parents: chores they created; children: their chores)
  - `GET /available`: Available chores for child (children only)
  - `GET /pending-approval`: Completed but unapproved chores (parents only)
  - `GET /child/{child_id}` and `/child/{child_id}/completed`: Parent views of a child’s chores
  - `GET /{chore_id}`: Chore details with access checks
  - `PUT /{chore_id}`: Update chore (parent creator only)
  - `DELETE /{chore_id}`: Hard delete (parent creator only)
  - `POST /{chore_id}/complete`: Mark complete (assignee child only; cooldown checks)
  - `POST /{chore_id}/approve`: Approve completed chore (parent creator only; range reward validation)
  - `POST /{chore_id}/disable`: Soft delete (parent creator only)

- `adjustments` (`/api/v1/adjustments`)
  - `POST /`: Create a reward adjustment (parent only; amount non-zero; only own children)
  - `GET /child/{child_id}`: Adjustments for a child (parent only, must be own child)
  - `GET /total/{child_id}`: Sum of a child’s adjustments (parent only)

- Misc in `main.py`
  - `GET /api/v1/healthcheck`: health probe
  - `GET /api/v1/users/me`: current user
  - `GET /api/v1/users/me/balance`: child’s balance snapshot (derived)
  - `GET /api/v1/reports/potential-earnings`: parent HTML report of recurring-chores potential

### HTML/HTMX endpoints (server-rendered)
Rendered fragments power the UI without heavy client-side JS.
- Chore lists for various states: `/api/v1/html/chores/*`
- Approval/edit modals and forms: `/chores/{id}/approve-form`, `/chores/{id}/edit-form`
- Create chore: `/api/v1/html/chores/create` (form-submit + fragment response)
- User lists/cards and balance card: `/api/v1/html/users/*`
- Adjustments UI: `/api/v1/html/adjustments/*`

Pages:
- `GET /`, `GET /dashboard`, `GET /chores`, `GET /users`, `GET /reports`

---

## Services and repositories
- `repositories/base.py`: generic CRUD with async `AsyncSession` and optional eager loading
- `repositories/user.py`: auth helpers, children, password reset
- `repositories/chore.py`: role-based queries, availability, completion/approval, enable/disable, cooldown filtering
- `repositories/reward_adjustment.py`: listing and totals
- `services/user_service.py`: registration constraints, authentication checks, parent/child validations, family registration workflow, password reset
- `services/chore_service.py`: chore creation/updates, access control, approve/complete rules, bulk assign, transactional recurring-approval pattern via `UnitOfWork`
- `services/reward_adjustment_service.py`: parent-only validations, permissions, totals
- `core/unit_of_work.py`: transactional coordination across repositories

Business rules (highlights):
- Only parents create/update/disable/delete/approve chores they created.
- Only the assigned child completes a chore; cooldown enforced for recurring chores.
- Range rewards must be approved with a value within `[min_reward, max_reward]`.
- Parents can only adjust/view their own children’s adjustments.

---

## Authentication, rate limiting, validation
- **JWT**: `create_access_token`, `verify_token`; `dependencies/auth.py` resolves current user
- **Rate limiting**: `middleware/rate_limit.py` with SlowAPI
  - Stricter on auth; moderate for API; disabled in tests via no-op decorators
- **Request validation**: `middleware/request_validation.py`
  - Content-type, size limits, early JSON parse, basic sanitization helpers

---

## Templates and HTMX behavior
- Templates live in `backend/app/templates/` under `pages/`, `components/`, `layouts/`
- Pages load fragments via HTMX using an auth header taken from `localStorage` token
- Role-based UI:
  - Parents see child lists/cards, approval queues, admin tools, allowance summaries
  - Children see available/pending chores and a balance card that refreshes on events
- Typical pattern: fragments at `/api/v1/html/...` return HTML partials; JS sets `Authorization` header for HTMX requests and handles 401/403

Notable components/pages:
- `pages/dashboard.html`, `pages/chores.html`, `pages/users.html`, `pages/login.html`, `pages/register.html`, `pages/reports.html`
- Chore list/item components, approve forms, edit modal, balance card, allowance summary

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
docker-compose up
# Web UI: http://localhost:8000
# API docs: http://localhost:8000/docs
```

Common backend dev tasks (inside the API container):
```bash
docker compose exec api python -m pytest
docker compose exec api python -m alembic -c backend/alembic.ini upgrade head
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
  - Parent creates children (form or `POST /api/v1/users` JSON)
- Login
  - `POST /api/v1/users/login` returns JWT; stored in `localStorage`; used by HTMX/JS
- Chore lifecycle
  1) Parent creates a chore (fixed or range reward)
  2) Child completes it (moves to pending approval)
  3) Parent approves
     - Fixed reward: preset `reward`
     - Range reward: parent supplies `reward_value` within `[min_reward, max_reward]`
  4) If recurring: cooldown starts; chore becomes available again after cooldown
- Adjustments
  - Parent creates positive/negative adjustments with a reason; totals used in balance views
- Balances
  - Child balance = approved earned + adjustments − paid out (paid out currently 0 in code)

---

## Extensibility notes
- Add payouts: persist payouts and subtract from balances
- Add admin role and audit logging for sensitive operations
- Add caching/global rate limits and distributed limit storage
- Add refresh tokens and 2FA
- Expand reporting (monthly statements, payout history)

---

## References to key files
- App entrypoint and routes: `backend/app/main.py`, `backend/app/api/api_v1/api.py`
- Endpoints: `backend/app/api/api_v1/endpoints/*.py`
- Models: `backend/app/models/*.py`
- Schemas: `backend/app/schemas/*.py`
- Services: `backend/app/services/*.py`
- Repositories: `backend/app/repositories/*.py`
- Auth: `backend/app/dependencies/auth.py`, `backend/app/core/security/jwt.py`, `backend/app/core/security/password.py`
- Middleware: `backend/app/middleware/*.py`
- Templates: `backend/app/templates/**`
- Mobile: `mobile/`
- Compose: `docker-compose.yml`

This overview should give you a clear map of how the system is structured and how key features are implemented across the stack.