"""API v2 Router - JSON-only standardized endpoints."""
from fastapi import APIRouter
from .endpoints import auth, users, chores

api_v2_router = APIRouter()

# Include routers with v2 prefixes
api_v2_router.include_router(auth.router, prefix="/auth", tags=["auth-v2"])
api_v2_router.include_router(users.router, prefix="/users", tags=["users-v2"])
api_v2_router.include_router(chores.router, prefix="/chores", tags=["chores-v2"])