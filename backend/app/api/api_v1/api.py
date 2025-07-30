from fastapi import APIRouter
from .endpoints import users, chores, payments

api_router = APIRouter()
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(chores.router, prefix="/chores", tags=["chores"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])