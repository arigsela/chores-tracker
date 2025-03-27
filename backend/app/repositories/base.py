from typing import Generic, TypeVar, Type, Optional, List, Any, Dict, Union
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from ..db.base import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    """Base class for all repositories."""
    
    def __init__(self, model: Type[ModelType]):
        self.model = model
    
    async def get(self, db: AsyncSession, id: Any, eager_load_relations: List[str] = None) -> Optional[ModelType]:
        """Get a record by ID."""
        query = select(self.model).where(self.model.id == id)
        
        # Add eager loading if requested
        if eager_load_relations:
            for relation in eager_load_relations:
                relation_attr = getattr(self.model, relation)
                query = query.options(joinedload(relation_attr))
                
        result = await db.execute(query)
        return result.scalars().first()
    
    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """Get multiple records."""
        result = await db.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return result.scalars().all()
    
    async def create(self, db: AsyncSession, *, obj_in: Dict[str, Any]) -> ModelType:
        """Create a new record."""
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def update(
        self, db: AsyncSession, *, id: Any, obj_in: Dict[str, Any]
    ) -> Optional[ModelType]:
        """Update a record."""
        # Execute the update operation
        await db.execute(
            update(self.model)
            .where(self.model.id == id)
            .values(**obj_in)
        )
        # Commit the changes
        await db.commit()
        # Retrieve the updated object (without eager loading by default)
        return await self.get(db, id)
    
    async def delete(self, db: AsyncSession, *, id: Any) -> None:
        """Delete a record."""
        await db.execute(delete(self.model).where(self.model.id == id))
        await db.commit()