"""
Unit of Work pattern implementation for transaction management.

This module provides a Unit of Work pattern to ensure data consistency
across multiple repository operations within a single transaction.
"""

from typing import Type, TypeVar, Optional, AsyncContextManager
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager

from ..db.base import AsyncSessionLocal
from ..repositories.user import UserRepository
from ..repositories.chore import ChoreRepository
from ..repositories.chore_assignment import ChoreAssignmentRepository


class UnitOfWork:
    """
    Unit of Work pattern implementation for managing database transactions.
    
    This class ensures that all database operations within its context
    are part of the same transaction. If any operation fails, all changes
    are rolled back.
    
    Example usage:
        async with UnitOfWork() as uow:
            user = await uow.users.create(db=uow.session, obj_in=user_data)
            chore = await uow.chores.create(db=uow.session, obj_in=chore_data)
            await uow.commit()
    """
    
    def __init__(self, session_factory=None):
        self.session_factory = session_factory or AsyncSessionLocal
        self.session: Optional[AsyncSession] = None
        self._users: Optional[UserRepository] = None
        self._chores: Optional[ChoreRepository] = None
        self._assignments: Optional[ChoreAssignmentRepository] = None
    
    async def __aenter__(self):
        """Enter the async context manager."""
        self.session = self.session_factory()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the async context manager."""
        if exc_type:
            # If there was an exception, rollback
            await self.rollback()
        await self.close()
    
    @property
    def users(self) -> UserRepository:
        """Get the user repository instance."""
        if self._users is None:
            self._users = UserRepository()
        return self._users
    
    @property
    def chores(self) -> ChoreRepository:
        """Get the chore repository instance."""
        if self._chores is None:
            self._chores = ChoreRepository()
        return self._chores

    @property
    def assignments(self) -> ChoreAssignmentRepository:
        """Get the chore assignment repository instance."""
        if self._assignments is None:
            self._assignments = ChoreAssignmentRepository()
        return self._assignments

    async def commit(self):
        """Commit the current transaction."""
        if self.session:
            await self.session.commit()
    
    async def rollback(self):
        """Rollback the current transaction."""
        if self.session:
            await self.session.rollback()
    
    async def close(self):
        """Close the session."""
        if self.session:
            await self.session.close()
            self.session = None


@asynccontextmanager
async def get_unit_of_work():
    """
    Dependency injection function for Unit of Work.
    
    This can be used in FastAPI endpoints or services that need
    transactional behavior.
    
    Example:
        @router.post("/users")
        async def create_user_with_chores(
            user_data: UserCreate,
            uow: UnitOfWork = Depends(get_unit_of_work)
        ):
            async with uow:
                user = await uow.users.create(uow.session, obj_in=user_data)
                # Create initial chores...
                await uow.commit()
    """
    async with UnitOfWork() as uow:
        yield uow