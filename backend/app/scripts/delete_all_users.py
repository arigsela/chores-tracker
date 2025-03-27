import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import AsyncSessionLocal
from app.models.user import User

async def delete_all_users():
    """Delete all users from the database."""
    async with AsyncSessionLocal() as session:
        # Delete all users
        await session.execute(User.__table__.delete())
        await session.commit()
        print("All users have been deleted successfully.")

if __name__ == "__main__":
    asyncio.run(delete_all_users()) 