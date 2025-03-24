from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pathlib import Path
from datetime import datetime
import os
from starlette.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer
from .dependencies.auth import get_current_user
from . import models, schemas
from sqlalchemy.ext.asyncio import AsyncSession
from .db.base import get_db

from .core.config import settings

from .api.api_v1.api import api_router

app = FastAPI(
    title=settings.APP_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(api_router, prefix=settings.API_V1_STR)

# Static files
static_dir = Path(__file__).parent / "static"
if not static_dir.exists():
    static_dir.mkdir(parents=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Templates
templates = Jinja2Templates(directory=settings.TEMPLATES_DIR)
templates.env.globals["now"] = lambda: datetime.now()

# Modify the root endpoint to redirect to the dashboard if authenticated
@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("pages/index.html", {"request": request})

# Add a specific route for the dashboard
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Display dashboard page."""
    return templates.TemplateResponse("pages/dashboard.html", {"request": request})

# Add routes for chores and users pages
@app.get("/chores", response_class=HTMLResponse)
async def chores_page(request: Request):
    """Display chores page."""
    return templates.TemplateResponse("pages/chores.html", {"request": request})

@app.get("/users", response_class=HTMLResponse)
async def users_page(request: Request):
    """Display users page."""
    return templates.TemplateResponse("pages/users.html", {"request": request})

@app.get("/pages/{page_name}", response_class=HTMLResponse)
async def get_page(request: Request, page_name: str):
    """Render a page by name."""
    return templates.TemplateResponse(f"pages/{page_name}.html", {"request": request})

@app.get("/components/{component_name}", response_class=HTMLResponse)
async def get_component(request: Request, component_name: str):
    """Render a component by name."""
    return templates.TemplateResponse(f"components/{component_name}.html", {"request": request})

# Add this to backend/app/main.py after the existing endpoint definitions

@app.get("/api/v1/users/me", response_model=schemas.UserResponse)
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    """Get current user."""
    return current_user

@app.get("/api/v1/users/children", response_class=HTMLResponse)
async def get_children_options(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get options for children dropdown."""
    from .repositories.user import UserRepository
    user_repo = UserRepository()
    
    if not current_user.is_parent:
        return HTMLResponse("<option value=''>Not authorized</option>")
    
    children = await user_repo.get_children(db, parent_id=current_user.id)
    
    html = "<option value=''>Select a child</option>"
    for child in children:
        html += f"<option value='{child.id}'>{child.username}</option>"
    
    return HTMLResponse(html)

@app.get("/api/v1/users/summary", response_class=HTMLResponse)
async def get_allowance_summary(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get allowance summary for children."""
    if not current_user.is_parent:
        return HTMLResponse("<p>Not authorized</p>")
    
    from .repositories.user import UserRepository
    from .repositories.chore import ChoreRepository
    user_repo = UserRepository()
    chore_repo = ChoreRepository()
    
    children = await user_repo.get_children(db, parent_id=current_user.id)
    
    # Get summary data for each child
    summary_data = []
    for child in children:
        chores = await chore_repo.get_by_assignee(db, assignee_id=child.id)
        
        completed_chores = len([c for c in chores if c.is_completed and c.is_approved])
        total_earned = sum(c.reward for c in chores if c.is_completed and c.is_approved)
        
        # For now, assume no payments made yet
        paid_out = 0
        balance_due = total_earned - paid_out
        
        summary_data.append({
            "id": child.id,
            "username": child.username,
            "completed_chores": completed_chores,
            "total_earned": f"{total_earned:.2f}",
            "paid_out": f"{paid_out:.2f}",
            "balance_due": f"{balance_due:.2f}"
        })
    
    return templates.TemplateResponse(
        "components/allowance_summary.html", 
        {"request": request, "children": summary_data}
    )

@app.get("/api/v1/chores", response_class=HTMLResponse)
async def get_chores_html(
    request: Request,
    status: str = None,
    assignee_id: int = None,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get chores as HTML components."""
    from .repositories.chore import ChoreRepository
    chore_repo = ChoreRepository()
    
    # Get base chores based on user role
    if current_user.is_parent:
        if assignee_id:
            chores = await chore_repo.get_by_assignee(db, assignee_id=assignee_id)
        else:
            chores = await chore_repo.get_by_creator(db, creator_id=current_user.id)
    else:
        chores = await chore_repo.get_by_assignee(db, assignee_id=current_user.id)
    
    # Filter by status if specified
    if status:
        if status == "pending":
            chores = [c for c in chores if c.is_completed and not c.is_approved]
        elif status == "active":
            chores = [c for c in chores if not c.is_completed]
        elif status == "completed":
            chores = [c for c in chores if c.is_completed and c.is_approved]
    
    return templates.TemplateResponse(
        "components/chore_list.html", 
        {"request": request, "chores": chores}
    )