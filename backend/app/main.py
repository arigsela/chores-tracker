print("Starting main.py import...")
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import os
from contextlib import asynccontextmanager

print("Importing dependencies...")
from .dependencies.auth import get_current_user
from . import models, schemas
from sqlalchemy.ext.asyncio import AsyncSession
from .db.base import get_db
from typing import Optional

print("Importing config...")
from .core.config import settings
print("Config imported")
from .middleware.rate_limit import setup_rate_limiting
from .middleware.request_validation import RequestValidationMiddleware
from .core.logging import setup_query_logging, setup_connection_pool_logging

print("Importing API router...")
from .api.api_v1.api import api_router
print("API router imported")

# Prometheus monitoring
print("Importing Prometheus instrumentator...")
from prometheus_fastapi_instrumentator import Instrumentator
print("Instrumentator imported")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown events."""
    # Startup
    print(f"Starting {settings.APP_NAME}...")
    print(f"Database URL: {settings.DATABASE_URL}")
    print(f"CORS Origins: {settings.BACKEND_CORS_ORIGINS}")
    print(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")

    # Setup query logging if enabled
    if os.getenv("LOG_QUERIES") == "true":
        setup_query_logging()

    # Setup connection pool logging if enabled
    if os.getenv("LOG_CONNECTION_POOL") == "true":
        setup_connection_pool_logging()

    print(f"Application startup complete.")

    yield

    # Shutdown
    print(f"Shutting down {settings.APP_NAME}...")


app = FastAPI(
    title=settings.APP_NAME,
    redirect_slashes=False,  # Disable automatic trailing slash redirects
    lifespan=lifespan,
    description="""
# Chores Tracker API

A comprehensive API for managing household chores, rewards, and family task assignments.

## Features

* **User Management** - Register and authenticate parents and children
* **Family Management** - Multi-parent families with invite code system
* **Chore Management** - Create, assign, and track household chores
* **Reward System** - Set fixed or range-based rewards for completed tasks
* **Approval Workflow** - Children complete chores, parents approve and set rewards
* **Recurring Tasks** - Support for daily, weekly, or custom recurring chores

## Authentication Flow

### 1. Registration
Parents can self-register at `/api/v1/users/register`:
```json
{
  "username": "parent_user",
  "password": "SecurePassword123",
  "email": "parent@example.com",
  "is_parent": true
}
```

Children must be registered by their parent (requires parent authentication).

### 2. Login
Obtain a JWT token at `/api/v1/users/login`:
```
POST /api/v1/users/login
Content-Type: application/x-www-form-urlencoded

username=parent_user&password=SecurePassword123
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 3. Using the Token
Include the token in subsequent requests:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Tokens expire after 8 days by default.

## User Roles

### Parents
- Create and manage child accounts
- Create and assign chores
- Approve completed chores and set final rewards
- View all family chores and balances
- Make balance adjustments (bonuses/penalties)

### Children  
- View assigned chores
- Mark chores as complete
- View their balance and earnings
- See approval status of completed chores

## Reward Types

### Fixed Rewards
Single amount set when creating the chore.

### Range Rewards
Min/max range defined at creation. Parent sets final amount on approval.

## Family Management System

### Multi-Parent Families
- Both parents can manage children and chores within the same family
- Family creation generates 8-character invite codes
- Parents can invite other parents to join their family
- Children automatically inherit family membership from parents

### Family Invite Flow
1. **Create Family**: First parent creates family at `/api/v1/families/create`
2. **Generate Invite**: Get invite code from family creation or generate new one
3. **Join Family**: Second parent uses code at `/api/v1/families/join`
4. **Manage Together**: Both parents can now manage all family members and chores

### Family Endpoints
- `GET /api/v1/families/context` - Get user's family information
- `POST /api/v1/families/create` - Create new family
- `POST /api/v1/families/join` - Join family with invite code
- `GET /api/v1/families/members` - List all family members
- `POST /api/v1/families/invite-code` - Generate new invite code

## API Rate Limiting

- Authentication endpoints: 5 requests per minute
- General endpoints: 100 requests per minute
- Bulk operations: 10 requests per minute
""",
    version="3.0.0",
    openapi_tags=[
        {"name": "users", "description": "User management and authentication"},
        {"name": "chores", "description": "Chore management operations"},
        {"name": "adjustments", "description": "Balance adjustments"},
        {"name": "families", "description": "Family management and multi-parent operations"},
        {"name": "admin", "description": "Administrative operations"},
    ]
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup rate limiting
setup_rate_limiting(app)

# Add request validation middleware
app.add_middleware(RequestValidationMiddleware)

# Add API documentation routes before including the main API router
@app.get("/api/v1/docs")
async def api_docs():
    """Redirect to the OpenAPI documentation."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs")

@app.get("/api/v1/redoc")
async def api_redoc():
    """Redirect to the ReDoc documentation."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/redoc")

# Include API router
print("Including API router...")
app.include_router(api_router, prefix="/api/v1")
print("API router included")

# Setup Prometheus metrics instrumentation
# This will expose automatic HTTP metrics at /metrics endpoint
print("Creating Prometheus instrumentator...")
instrumentator = Instrumentator(
    should_group_status_codes=False,  # Keep detailed status codes
    should_ignore_untemplated=True,   # Ignore non-templated routes
    should_respect_env_var=False,     # Always enable metrics (set to True to use ENABLE_METRICS env var)
    should_instrument_requests_inprogress=True,  # Track active requests
    excluded_handlers=["/metrics", "/health", "/"],  # Don't track these endpoints
    env_var_name="ENABLE_METRICS",
    inprogress_name="http_requests_inprogress",
    inprogress_labels=True,
)
print("Instrumentator created")

# Instrument the app and expose the /metrics endpoint
print("Instrumenting app with Prometheus...")
instrumentator.instrument(app).expose(app, endpoint="/metrics", include_in_schema=True)
print("Prometheus instrumentation complete")

@app.get("/")
async def root():
    """Root endpoint - returns API information."""
    return {
        "name": settings.APP_NAME,
        "version": "3.0.0",
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "frontend": "React Native Web application (separate deployment)"
    }

@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Legacy health check endpoint for backward compatibility.

    Note: New health check endpoints are available at:
    - GET /api/v1/health (basic liveness)
    - GET /api/v1/health/ready (readiness with DB check)
    - GET /api/v1/health/detailed (component diagnostics)
    """
    try:
        # Try to execute a simple query
        from sqlalchemy import text
        result = await db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy", "database": "disconnected", "error": str(e)}
        )

# Additional API endpoints that were mixed with HTML endpoints

@app.get("/api/v1/users/me", response_model=schemas.UserResponse)
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    """Get current user."""
    return current_user

@app.get("/api/v1/users/me/balance", response_model=schemas.UserBalanceResponse)
async def get_my_balance(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get current user's balance information.
    
    Returns balance details for the authenticated user (child accounts only).
    Parents should use the /summary endpoint instead.
    """
    if current_user.is_parent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Parents should use /api/v1/users/summary endpoint"
        )
    
    # Use assignment-based balance calculation (multi-assignment architecture)
    from .repositories.chore_assignment import ChoreAssignmentRepository
    from .repositories.reward_adjustment import RewardAdjustmentRepository
    assignment_repo = ChoreAssignmentRepository()
    adjustment_repo = RewardAdjustmentRepository()

    # Get assignments for the current user (not chores)
    assignments = await assignment_repo.get_by_assignee(db, assignee_id=current_user.id)

    # Helper function to get final reward amount from assignment
    def get_assignment_reward(assignment):
        # For approved assignments, use approval_reward if set (range rewards)
        if assignment.approval_reward is not None:
            return assignment.approval_reward
        # Fallback to chore's base reward (fixed rewards)
        return assignment.chore.reward or 0

    # Calculate totals using assignment-level data
    total_earned = sum(get_assignment_reward(a) for a in assignments if a.is_completed and a.is_approved)
    pending_chores_value = sum(get_assignment_reward(a) for a in assignments if a.is_completed and not a.is_approved)
    
    # Get total adjustments
    total_adjustments = await adjustment_repo.calculate_total_adjustments(db, child_id=current_user.id)
    
    # For now, assume no payments made yet (same as parent summary)
    paid_out = 0
    balance = total_earned + float(total_adjustments) - paid_out
    
    return schemas.UserBalanceResponse(
        balance=balance,
        total_earned=total_earned,
        adjustments=float(total_adjustments),
        paid_out=paid_out,
        pending_chores_value=pending_chores_value
    )