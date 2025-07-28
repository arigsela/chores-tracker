"""API V2 router configuration."""
from fastapi import APIRouter

from .endpoints import chores, visibility

api_v2_router = APIRouter()

api_v2_router.include_router(chores.router, prefix="/chores", tags=["chores-v2"])
api_v2_router.include_router(visibility.router, prefix="/chores", tags=["visibility-v2"])