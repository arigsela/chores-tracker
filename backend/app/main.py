"""
Main FastAPI application entry point.
"""
from fastapi import FastAPI, Request, Depends, HTTPException, status, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from pathlib import Path
from datetime import datetime, timedelta
import os
from starlette.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer
from .dependencies.auth import get_current_user
from . import models, schemas
from sqlalchemy.ext.asyncio import AsyncSession
from .db.base import get_db
from typing import Optional, List, Dict, Any, Union
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Form, File, UploadFile

from .core.config import settings
from .middleware.rate_limit import setup_rate_limiting
from .core.logging import setup_query_logging, setup_connection_pool_logging

from .api.api_v1.api import api_router

app = FastAPI(
    title=settings.APP_NAME,
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

### Parents Can:
- Create and manage child accounts
- Create, update, and delete chores
- Approve completed chores and set final rewards
- View all chores they created
- Reset child passwords

### Children Can:
- View chores assigned to them
- Mark chores as completed
- View their completion history
- Cannot create or modify chores

## Rate Limiting

API endpoints are rate-limited to prevent abuse:
- Login: 5 requests per minute per IP
- Registration: 3 requests per minute per IP
- API endpoints: 100 requests per minute per IP
- Create operations: 30 requests per minute per IP
- Update operations: 60 requests per minute per IP
- Delete operations: 20 requests per minute per IP
    """,
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    terms_of_service="https://chores-tracker.example.com/terms/",
    contact={
        "name": "Chores Tracker Support",
        "email": "support@chores-tracker.example.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_tags=[
        {
            "name": "users",
            "description": "User registration, authentication, and management",
        },
        {
            "name": "chores",
            "description": "Chore creation, assignment, completion, and approval",
        },
        {
            "name": "payments",
            "description": "Payment management, balance adjustments, and history tracking",
        },
        {
            "name": "auth",
            "description": "Authentication endpoints",
        },
        {
            "name": "html",
            "description": "HTML/HTMX endpoints for dynamic UI updates",
        }
    ]
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up rate limiting
setup_rate_limiting(app)

# Enable query logging
if settings.DEBUG:
    setup_query_logging()
    setup_connection_pool_logging()

# Set up static files
app.mount("/static", StaticFiles(directory="backend/app/static"), name="static")

# Set up templates
templates = Jinja2Templates(directory="backend/app/templates")

# Include routers
app.include_router(api_router, prefix=settings.API_V1_STR)

# Root endpoint
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Redirect to the dashboard if logged in, otherwise return index page."""
    return templates.TemplateResponse("pages/index.html", {"request": request})

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "time": datetime.now().isoformat()}

@app.get("/api/v1/html/children-options", response_class=HTMLResponse)
async def get_children_options(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get HTML options for selecting children."""
    if not current_user.is_parent:
        return templates.TemplateResponse(
            "components/not_authorized.html",
            {"request": request, "format": "paragraph"}
        )
    
    from .repositories.user import UserRepository
    user_repo = UserRepository()
    
    children = await user_repo.get_children(db, parent_id=current_user.id)
    
    return templates.TemplateResponse(
        "components/children_options.html",
        {"request": request, "children": children}
    )

@app.get("/api/v1/users/summary", response_class=HTMLResponse)
async def get_allowance_summary(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get allowance summary for children."""
    if not current_user.is_parent:
        return templates.TemplateResponse(
            "components/not_authorized.html",
            {"request": request, "format": "paragraph"}
        )
    
    from .repositories.user import UserRepository
    from .repositories.chore import ChoreRepository
    from .repositories.payment import PaymentRepository
    user_repo = UserRepository()
    chore_repo = ChoreRepository()
    payment_repo = PaymentRepository()
    
    children = await user_repo.get_children(db, parent_id=current_user.id)
    
    # Get summary data for each child
    summary_data = []
    for child in children:
        chores = await chore_repo.get_by_assignee(db, assignee_id=child.id)
        
        completed_chores = len([c for c in chores if c.is_completed and c.is_approved])
        total_earned = sum(c.reward for c in chores if c.is_completed and c.is_approved)
        
        # Get total payments and adjustments
        total_payments = await payment_repo.get_total_payments(db, child_id=child.id)
        total_adjustments = await payment_repo.get_total_adjustments(db, child_id=child.id)
        
        # Calculate balance due
        paid_out = abs(total_payments)
        balance_due = total_earned + total_adjustments - paid_out
        
        summary_data.append({
            "id": child.id,
            "username": child.username,
            "completed_chores": completed_chores,
            "total_earned": f"{total_earned:.2f}",
            "paid_out": f"{paid_out:.2f}",
            "total_adjustments": f"{total_adjustments:.2f}",
            "balance_due": f"{balance_due:.2f}"
        })
    
    return templates.TemplateResponse(
        "components/allowance_summary.html", 
        {"request": request, "children": summary_data}
    )

@app.get("/api/v1/html/payments/adjust-form/{child_id}", response_class=HTMLResponse)
async def get_adjustment_form(
    request: Request,
    child_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get HTML form for adjusting a child's balance."""
    # Only parents can adjust balances
    if not current_user.is_parent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can adjust balances"
        )
    
    # Get the child
    from .repositories.user import UserRepository
    user_repo = UserRepository()
    child = await user_repo.get(db, id=child_id)
    
    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found"
        )
    
    # Ensure the child belongs to the parent
    if child.parent_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not your child"
        )
    
    # Render adjustment form
    return templates.TemplateResponse(
        "components/balance_adjustment_form.html",
        {"request": request, "child": child}
    )

@app.get("/api/v1/html/payments/history/{child_id}", response_class=HTMLResponse)
async def get_payment_history_html(
    request: Request,
    child_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get HTML for payment history."""
    # Only parents can view payment history
    if not current_user.is_parent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can view payment history"
        )
    
    # Get the child
    from .repositories.user import UserRepository
    user_repo = UserRepository()
    child = await user_repo.get(db, id=child_id)
    
    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found"
        )
    
    # Ensure the child belongs to the parent
    if child.parent_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not your child"
        )
    
    # Get payment history
    from .repositories.payment import PaymentRepository
    payment_repo = PaymentRepository()
    payments = await payment_repo.get_by_child(db, child_id=child_id)
    
    # Render payment history
    return templates.TemplateResponse(
        "components/payment_history.html",
        {"request": request, "child": child, "payments": payments}
    )