from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pathlib import Path
from datetime import datetime
import os

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

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the index page."""
    return templates.TemplateResponse("pages/index.html", {"request": request})

@app.get("/pages/{page_name}", response_class=HTMLResponse)
async def get_page(request: Request, page_name: str):
    """Render a page by name."""
    return templates.TemplateResponse(f"pages/{page_name}.html", {"request": request})

@app.get("/components/{component_name}", response_class=HTMLResponse)
async def get_component(request: Request, component_name: str):
    """Render a component by name."""
    return templates.TemplateResponse(f"components/{component_name}.html", {"request": request})