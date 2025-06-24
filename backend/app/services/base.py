"""
Base service class with common functionality.
"""
from typing import Generic, TypeVar, Type, Union, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.base_class import Base
from ..repositories.base import BaseRepository

ModelType = TypeVar("ModelType", bound=Base)
RepositoryType = TypeVar("RepositoryType", bound=BaseRepository)


class BaseService(Generic[ModelType, RepositoryType]):
    """Base service class with common business logic."""
    
    def __init__(self, repository: RepositoryType):
        """Initialize service with repository."""
        self.repository = repository
    
    async def get(self, db: AsyncSession, *, id: int) -> Optional[ModelType]:
        """Get a single record by ID."""
        return await self.repository.get(db, id=id)
    
    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """Get multiple records."""
        return await self.repository.get_multi(db, skip=skip, limit=limit)
    
    async def create(self, db: AsyncSession, *, obj_in: dict) -> ModelType:
        """Create a new record."""
        return await self.repository.create(db, obj_in=obj_in)
    
    async def update(
        self, db: AsyncSession, *, id: int, obj_in: dict
    ) -> Optional[ModelType]:
        """Update a record."""
        return await self.repository.update(db, id=id, obj_in=obj_in)
    
    async def delete(self, db: AsyncSession, *, id: int) -> None:
        """Delete a record."""
        return await self.repository.delete(db, id=id)