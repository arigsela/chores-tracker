from fastapi import APIRouter
from .endpoints import users, chores, assignments, adjustments, activities, reports, statistics, families

api_router = APIRouter()
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(chores.router, prefix="/chores", tags=["chores"])
api_router.include_router(assignments.router, prefix="/assignments", tags=["assignments"])
api_router.include_router(adjustments.router, prefix="/adjustments", tags=["adjustments"])
api_router.include_router(activities.router, prefix="/activities", tags=["activities"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(statistics.router, prefix="/statistics", tags=["statistics"])
api_router.include_router(families.router, prefix="/families", tags=["families"])