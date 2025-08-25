from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import os

from .dependencies.auth import get_current_user
from . import models, schemas
from sqlalchemy.ext.asyncio import AsyncSession
from .db.base import get_db
from typing import Optional

from .core.config import settings
from .middleware.rate_limit import setup_rate_limiting
from .middleware.request_validation import RequestValidationMiddleware
from .core.logging import setup_query_logging, setup_connection_pool_logging

from .api.api_v1.api import api_router

app = FastAPI(
    title=settings.APP_NAME,
    redirect_slashes=False,  # Disable automatic trailing slash redirects
    description="""
# Chores Tracker API

A comprehensive API for managing household chores, rewards, and family task assignments.

## Features

* **User Management** - Register and authenticate parents and children
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
app.include_router(api_router, prefix="/api/v1")

# Setup query logging if enabled
if os.getenv("LOG_QUERIES") == "true":
    setup_query_logging()

# Setup connection pool logging if enabled  
if os.getenv("LOG_CONNECTION_POOL") == "true":
    setup_connection_pool_logging()

@app.on_event("startup")
async def startup_event():
    """Initialize the application."""
    print(f"Starting {settings.APP_NAME}...")
    print(f"Database URL: {settings.DATABASE_URL}")
    print(f"CORS Origins: {settings.BACKEND_CORS_ORIGINS}")
    print(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    print(f"Shutting down {settings.APP_NAME}...")

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
    """Health check endpoint."""
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
    
    # Reuse the balance calculation logic from the summary endpoint
    from .repositories.chore import ChoreRepository
    from .repositories.reward_adjustment import RewardAdjustmentRepository
    chore_repo = ChoreRepository()
    adjustment_repo = RewardAdjustmentRepository()
    
    # Get chores for the current user
    chores = await chore_repo.get_by_assignee(db, assignee_id=current_user.id)
    
    # Helper function to get final reward amount (matches frontend logic)
    def get_final_reward_amount(chore):
        # For approved chores, prioritize approval_reward field
        if chore.approval_reward is not None:
            return chore.approval_reward
        # Fallback to reward field (legacy and fixed rewards)
        return chore.reward or 0
    
    # Calculate totals using correct reward amounts
    total_earned = sum(get_final_reward_amount(c) for c in chores if c.is_completed and c.is_approved)
    pending_chores_value = sum(get_final_reward_amount(c) for c in chores if c.is_completed and not c.is_approved)
    
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