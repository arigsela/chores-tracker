from fastapi import APIRouter
from .endpoints import users, chores

api_router = APIRouter()
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(chores.router, prefix="/chores", tags=["chores"])