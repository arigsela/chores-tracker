# FastAPI Project Structure Guide

## Table of Contents
1. [Project Overview](#project-overview)
2. [Directory Structure](#directory-structure)
3. [Layered Architecture](#layered-architecture)
4. [Step-by-Step Guides](#step-by-step-guides)
   - [Adding a New Endpoint](#adding-a-new-endpoint)
   - [Adding a New Model/Table](#adding-a-new-modeltable)
   - [Adding a New Service](#adding-a-new-service)
   - [Adding a New Repository Method](#adding-a-new-repository-method)
5. [File Organization Patterns](#file-organization-patterns)
6. [Import Conventions](#import-conventions)
7. [Code Organization Best Practices](#code-organization-best-practices)

---

## Project Overview

The chores-tracker backend follows a **clean layered architecture** pattern that separates concerns and makes code maintainable and testable.

```
┌─────────────────────────────────────────────┐
│          API Layer (Endpoints)              │  ← HTTP concerns, routing
├─────────────────────────────────────────────┤
│          Service Layer                      │  ← Business logic
├─────────────────────────────────────────────┤
│          Repository Layer                   │  ← Data access
├─────────────────────────────────────────────┤
│          Model Layer (ORM)                  │  ← Database schema
└─────────────────────────────────────────────┘
```

**Data flow**:
- **Incoming**: API → Service → Repository → Database
- **Outgoing**: Database → Repository → Service → API

---

## Directory Structure

```
backend/
├── alembic/                      # Database migrations
│   ├── versions/                 # Migration version files
│   │   └── 001_initial.py
│   └── env.py                    # Alembic environment config
├── alembic.ini                   # Alembic configuration
├── app/                          # Main application code
│   ├── __init__.py
│   ├── main.py                   # Application entry point, FastAPI app instance
│   │
│   ├── api/                      # API layer
│   │   └── api_v1/
│   │       ├── api.py            # Router aggregation
│   │       └── endpoints/        # API endpoint modules
│   │           ├── __init__.py
│   │           ├── chores.py     # Chore endpoints
│   │           ├── users.py      # User endpoints
│   │           ├── families.py   # Family endpoints
│   │           └── health.py     # Health check endpoints
│   │
│   ├── core/                     # Core utilities and configuration
│   │   ├── __init__.py
│   │   ├── config.py             # Application settings (env vars)
│   │   ├── logging.py            # Logging configuration
│   │   ├── metrics.py            # Prometheus metrics
│   │   ├── metrics_auth.py       # Metrics endpoint authentication
│   │   ├── exceptions.py         # Custom exceptions
│   │   ├── registration_codes.py # Registration code utilities
│   │   ├── unit_of_work.py       # Transaction management pattern
│   │   └── security/             # Security utilities
│   │       ├── __init__.py
│   │       ├── jwt.py            # JWT token creation/verification
│   │       └── password.py       # Password hashing
│   │
│   ├── db/                       # Database configuration
│   │   ├── __init__.py
│   │   ├── base.py               # Session management, get_db dependency
│   │   └── base_class.py         # SQLAlchemy declarative base
│   │
│   ├── dependencies/             # FastAPI dependency injection
│   │   ├── __init__.py
│   │   ├── auth.py               # Authentication dependencies
│   │   └── services.py           # Service layer dependencies
│   │
│   ├── middleware/               # Middleware components
│   │   ├── __init__.py
│   │   ├── rate_limit.py         # Rate limiting
│   │   └── request_validation.py # Request validation
│   │
│   ├── models/                   # SQLAlchemy ORM models (database schema)
│   │   ├── __init__.py
│   │   ├── activity.py           # Activity audit log model
│   │   ├── chore.py              # Chore model
│   │   ├── chore_assignment.py   # ChoreAssignment junction table
│   │   ├── family.py             # Family model
│   │   ├── reward_adjustment.py  # RewardAdjustment model
│   │   └── user.py               # User model
│   │
│   ├── repositories/             # Data access layer (CRUD operations)
│   │   ├── __init__.py
│   │   ├── base.py               # Generic repository base class
│   │   ├── activity.py           # Activity repository
│   │   ├── chore.py              # Chore repository
│   │   ├── chore_assignment.py   # ChoreAssignment repository
│   │   ├── family.py             # Family repository
│   │   ├── reward_adjustment.py  # RewardAdjustment repository
│   │   └── user.py               # User repository
│   │
│   ├── schemas/                  # Pydantic models (validation/serialization)
│   │   ├── __init__.py
│   │   ├── activity.py           # Activity schemas
│   │   ├── assignment.py         # ChoreAssignment schemas
│   │   ├── chore.py              # Chore schemas
│   │   ├── family.py             # Family schemas
│   │   ├── health.py             # Health check schemas
│   │   ├── reward_adjustment.py  # RewardAdjustment schemas
│   │   ├── token.py              # JWT token schemas
│   │   └── user.py               # User schemas
│   │
│   ├── services/                 # Business logic layer
│   │   ├── __init__.py
│   │   ├── base.py               # Base service class
│   │   ├── activity_service.py   # Activity logging service
│   │   ├── chore_service.py      # Chore business logic
│   │   ├── family_service.py     # Family business logic
│   │   └── user_service.py       # User business logic
│   │
│   └── scripts/                  # Utility scripts
│       ├── create_parent_user.py
│       ├── create_test_child.py
│       ├── list_users.py
│       └── reset_password.py
│
└── tests/                        # Test suite
    ├── __init__.py
    ├── conftest.py               # Pytest fixtures
    ├── test_api/                 # API endpoint tests
    │   ├── test_chores.py
    │   ├── test_users.py
    │   └── test_families.py
    ├── test_services/            # Service layer tests
    │   ├── test_chore_service.py
    │   └── test_user_service.py
    ├── test_repositories.py      # Repository tests
    └── test_metrics.py           # Metrics tests
```

---

## Layered Architecture

### Layer 1: Models (Database Schema)

**Purpose**: Define database tables using SQLAlchemy ORM.

**Location**: `backend/app/models/`

**Example**: `backend/app/models/chore.py`
```python
from sqlalchemy import String, Float, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..db.base_class import Base

class Chore(Base):
    __tablename__ = "chores"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    reward: Mapped[float] = mapped_column(Float, default=0.0)
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # Relationships
    creator: Mapped["User"] = relationship("User", back_populates="chores_created")
```

**When to modify**:
- Adding a new table
- Adding/removing columns
- Changing column types
- Defining relationships

---

### Layer 2: Schemas (Validation & Serialization)

**Purpose**: Define data validation and API contracts using Pydantic.

**Location**: `backend/app/schemas/`

**Three types of schemas**:

1. **Base Schema**: Shared fields
```python
# backend/app/schemas/chore.py
class ChoreBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    reward: float = Field(0.0, ge=0, le=1000)
```

2. **Create Schema**: What API accepts when creating
```python
class ChoreCreate(ChoreBase):
    assignee_ids: List[int] = Field(default_factory=list)
    assignment_mode: Literal['single', 'multi_independent', 'unassigned'] = 'single'
```

3. **Response Schema**: What API returns
```python
class ChoreResponse(ChoreBase):
    id: int
    creator_id: int
    created_at: datetime
    is_completed: bool

    model_config = ConfigDict(from_attributes=True)  # Allow ORM model conversion
```

**When to modify**:
- Adding new API endpoints (create corresponding schemas)
- Changing validation rules
- Adding/removing fields from API contracts

---

### Layer 3: Repositories (Data Access)

**Purpose**: Encapsulate database queries and CRUD operations.

**Location**: `backend/app/repositories/`

**Base repository** (`backend/app/repositories/base.py`):
```python
class BaseRepository(Generic[ModelType]):
    """Generic CRUD operations for all models."""

    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        """Get record by ID."""
        query = select(self.model).where(self.model.id == id)
        result = await db.execute(query)
        return result.scalars().first()

    async def get_multi(self, db: AsyncSession, *, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Get multiple records."""
        result = await db.execute(select(self.model).offset(skip).limit(limit))
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: Dict[str, Any]) -> ModelType:
        """Create a new record."""
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
```

**Specialized repository** (`backend/app/repositories/chore.py`):
```python
class ChoreRepository(BaseRepository[Chore]):
    """Chore-specific data access operations."""

    def __init__(self):
        super().__init__(Chore)

    async def get_by_creator(self, db: AsyncSession, creator_id: int) -> List[Chore]:
        """Get all chores created by a specific user."""
        stmt = select(Chore).where(Chore.creator_id == creator_id)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_active_chores(self, db: AsyncSession, creator_id: int) -> List[Chore]:
        """Get non-disabled chores for a creator."""
        stmt = select(Chore).where(
            Chore.creator_id == creator_id,
            Chore.is_disabled == False
        )
        result = await db.execute(stmt)
        return result.scalars().all()
```

**When to modify**:
- Adding new database queries
- Creating specialized query methods
- Optimizing database access patterns

---

### Layer 4: Services (Business Logic)

**Purpose**: Implement business rules, orchestrate multiple repositories, handle complex operations.

**Location**: `backend/app/services/`

**Example** (`backend/app/services/chore_service.py`):
```python
class ChoreService(BaseService[Chore, ChoreRepository]):
    """Chore business logic."""

    def __init__(self):
        super().__init__(ChoreRepository())
        self.user_repo = UserRepository()
        self.assignment_repo = ChoreAssignmentRepository()
        self.activity_service = ActivityService()

    async def create_chore(
        self,
        db: AsyncSession,
        *,
        creator_id: int,
        chore_data: Dict[str, Any]
    ) -> Chore:
        """
        Create a new chore with business logic validation.

        Business rules:
        1. Only parents can create chores
        2. Assignees must be children in the same family
        3. Validate reward ranges
        4. Create assignments based on assignment mode
        5. Log activity
        """
        # 1. Validate creator exists and is a parent
        creator = await self.user_repo.get(db, id=creator_id)
        if not creator:
            raise HTTPException(404, "Creator not found")
        if not creator.is_parent:
            raise HTTPException(403, "Only parents can create chores")

        # 2. Validate assignees
        assignee_ids = chore_data.get("assignee_ids", [])
        for assignee_id in assignee_ids:
            assignee = await self.user_repo.get(db, id=assignee_id)
            if not assignee:
                raise HTTPException(404, f"Assignee {assignee_id} not found")
            if assignee.family_id != creator.family_id:
                raise HTTPException(403, "Assignee not in your family")

        # 3. Create chore
        chore = await self.repository.create(db, obj_in=chore_data)

        # 4. Create assignments
        for assignee_id in assignee_ids:
            await self.assignment_repo.create(db, obj_in={
                "chore_id": chore.id,
                "assignee_id": assignee_id
            })

        # 5. Log activity
        await self.activity_service.log_chore_created(db, chore_id=chore.id, creator_id=creator_id)

        return chore
```

**When to modify**:
- Implementing new business logic
- Adding validation rules
- Orchestrating multiple repositories
- Handling complex workflows

---

### Layer 5: API Endpoints (HTTP Interface)

**Purpose**: Handle HTTP requests, call services, return responses.

**Location**: `backend/app/api/api_v1/endpoints/`

**Example** (`backend/app/api/api_v1/endpoints/chores.py`):
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from ....db.base import get_db
from ....schemas.chore import ChoreCreate, ChoreResponse
from ....dependencies.auth import get_current_user, get_current_parent
from ....dependencies.services import ChoreServiceDep
from ....models.user import User

router = APIRouter()

@router.post(
    "",
    response_model=ChoreResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new chore",
    description="Create a new chore and assign it to children. Parents only.",
)
async def create_chore(
    chore_data: ChoreCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_parent),
    chore_service: ChoreServiceDep = None,
):
    """Create a new chore."""
    return await chore_service.create_chore(
        db,
        creator_id=current_user.id,
        chore_data=chore_data.dict()
    )

@router.get(
    "",
    response_model=List[ChoreResponse],
    summary="List chores",
    description="Get all chores created by the current user.",
)
async def list_chores(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    chore_service: ChoreServiceDep = None,
):
    """List all chores for the current user."""
    return await chore_service.get_user_chores(db, user_id=current_user.id)

@router.get(
    "/{chore_id}",
    response_model=ChoreResponse,
    summary="Get chore details",
)
async def get_chore(
    chore_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    chore_service: ChoreServiceDep = None,
):
    """Get a specific chore by ID."""
    chore = await chore_service.get_chore(db, chore_id=chore_id, user_id=current_user.id)
    if not chore:
        raise HTTPException(status_code=404, detail="Chore not found")
    return chore
```

**Router aggregation** (`backend/app/api/api_v1/api.py`):
```python
from fastapi import APIRouter
from .endpoints import chores, users, families, health

api_router = APIRouter()

api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(chores.router, prefix="/chores", tags=["chores"])
api_router.include_router(families.router, prefix="/families", tags=["families"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
```

**When to modify**:
- Adding new API endpoints
- Changing endpoint paths or HTTP methods
- Updating API documentation
- Adding new query parameters

---

## Step-by-Step Guides

### Adding a New Endpoint

**Scenario**: Add a `GET /api/v1/chores/stats` endpoint to get chore statistics.

**Step 1: Create the response schema**

File: `backend/app/schemas/chore.py`
```python
class ChoreStatsResponse(BaseModel):
    """Statistics about chores."""
    total_chores: int = Field(..., description="Total number of chores")
    completed_chores: int = Field(..., description="Number of completed chores")
    pending_chores: int = Field(..., description="Number of pending chores")
    total_rewards: float = Field(..., description="Total rewards earned")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_chores": 50,
                "completed_chores": 35,
                "pending_chores": 15,
                "total_rewards": 175.50
            }
        }
    )
```

**Step 2: Add repository method (if needed)**

File: `backend/app/repositories/chore.py`
```python
class ChoreRepository(BaseRepository[Chore]):
    async def get_chore_stats(self, db: AsyncSession, creator_id: int) -> Dict[str, Any]:
        """Get chore statistics for a creator."""
        from sqlalchemy import func, select

        stmt = select(
            func.count(Chore.id).label('total_chores'),
            func.sum(case((Chore.is_completed == True, 1), else_=0)).label('completed_chores'),
            func.sum(case((Chore.is_completed == False, 1), else_=0)).label('pending_chores'),
            func.sum(Chore.reward).label('total_rewards')
        ).where(Chore.creator_id == creator_id)

        result = await db.execute(stmt)
        row = result.first()

        return {
            "total_chores": row.total_chores or 0,
            "completed_chores": row.completed_chores or 0,
            "pending_chores": row.pending_chores or 0,
            "total_rewards": row.total_rewards or 0.0
        }
```

**Step 3: Add service method**

File: `backend/app/services/chore_service.py`
```python
class ChoreService(BaseService[Chore, ChoreRepository]):
    async def get_chore_statistics(
        self,
        db: AsyncSession,
        user_id: int
    ) -> Dict[str, Any]:
        """Get chore statistics for a user."""
        # Validate user exists
        user = await self.user_repo.get(db, id=user_id)
        if not user:
            raise HTTPException(404, "User not found")

        # Get stats from repository
        stats = await self.repository.get_chore_stats(db, creator_id=user_id)

        return stats
```

**Step 4: Add endpoint**

File: `backend/app/api/api_v1/endpoints/chores.py`
```python
@router.get(
    "/stats",
    response_model=ChoreStatsResponse,
    summary="Get chore statistics",
    description="Get statistics about chores created by the current user.",
)
async def get_chore_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    chore_service: ChoreServiceDep = None,
):
    """Get chore statistics."""
    stats = await chore_service.get_chore_statistics(db, user_id=current_user.id)
    return stats
```

**Step 5: Test the endpoint**

File: `backend/tests/test_api/test_chores.py`
```python
@pytest.mark.asyncio
async def test_get_chore_stats(client, test_parent_token):
    """Test getting chore statistics."""
    response = await client.get(
        "/api/v1/chores/stats",
        headers={"Authorization": f"Bearer {test_parent_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "total_chores" in data
    assert "completed_chores" in data
    assert "pending_chores" in data
    assert "total_rewards" in data
```

---

### Adding a New Model/Table

**Scenario**: Add a `Badge` model for achievement badges.

**Step 1: Create the model**

File: `backend/app/models/badge.py`
```python
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from ..db.base_class import Base

if TYPE_CHECKING:
    from .user import User

class Badge(Base):
    """User achievement badge model."""
    __tablename__ = "badges"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    description: Mapped[str] = mapped_column(Text)
    icon: Mapped[str] = mapped_column(String(50))  # Icon name/emoji
    points_required: Mapped[int] = mapped_column(Integer, default=0)

    # Foreign keys
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # Timestamps
    earned_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="badges")

    def __repr__(self) -> str:
        return f"<Badge(id={self.id}, name='{self.name}', user_id={self.user_id})>"
```

**Step 2: Update related models**

File: `backend/app/models/user.py`
```python
# Add to User model
from typing import List
from .badge import Badge

class User(Base):
    # ... existing fields ...

    # Add relationship
    badges: Mapped[List["Badge"]] = relationship(
        "Badge",
        back_populates="user",
        cascade="all, delete-orphan"
    )
```

**Step 3: Import in db/base.py**

File: `backend/app/db/base.py`
```python
from .base_class import Base  # noqa
from ..models.user import User  # noqa
from ..models.chore import Chore  # noqa
from ..models.badge import Badge  # noqa - ADD THIS
```

**Step 4: Create database migration**

```bash
# Generate migration
docker compose exec api python -m alembic -c backend/alembic.ini revision --autogenerate -m "add_badges_table"

# Review the generated migration in backend/alembic/versions/
# Then apply it
docker compose exec api python -m alembic -c backend/alembic.ini upgrade head
```

**Step 5: Create schemas**

File: `backend/app/schemas/badge.py`
```python
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional

class BadgeBase(BaseModel):
    """Base badge schema."""
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., max_length=500)
    icon: str = Field(..., max_length=50)
    points_required: int = Field(0, ge=0)

class BadgeCreate(BadgeBase):
    """Schema for creating a badge."""
    user_id: int

class BadgeResponse(BadgeBase):
    """Schema for badge response."""
    id: int
    user_id: int
    earned_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

**Step 6: Create repository**

File: `backend/app/repositories/badge.py`
```python
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.badge import Badge
from .base import BaseRepository

class BadgeRepository(BaseRepository[Badge]):
    """Badge data access operations."""

    def __init__(self):
        super().__init__(Badge)

    async def get_by_user(self, db: AsyncSession, user_id: int) -> List[Badge]:
        """Get all badges for a user."""
        stmt = select(Badge).where(Badge.user_id == user_id).order_by(Badge.earned_at.desc())
        result = await db.execute(stmt)
        return result.scalars().all()
```

**Step 7: Create service (optional, if business logic needed)**

File: `backend/app/services/badge_service.py`
```python
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.badge import Badge
from ..repositories.badge import BadgeRepository
from ..repositories.user import UserRepository
from .base import BaseService

class BadgeService(BaseService[Badge, BadgeRepository]):
    """Badge business logic."""

    def __init__(self):
        super().__init__(BadgeRepository())
        self.user_repo = UserRepository()

    async def award_badge(
        self,
        db: AsyncSession,
        user_id: int,
        badge_name: str,
        description: str,
        icon: str,
        points_required: int = 0
    ) -> Badge:
        """Award a badge to a user."""
        # Validate user exists
        user = await self.user_repo.get(db, id=user_id)
        if not user:
            raise ValueError("User not found")

        # Create badge
        badge = await self.repository.create(db, obj_in={
            "name": badge_name,
            "description": description,
            "icon": icon,
            "points_required": points_required,
            "user_id": user_id
        })

        return badge
```

**Step 8: Create endpoints**

File: `backend/app/api/api_v1/endpoints/badges.py`
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from ....db.base import get_db
from ....schemas.badge import BadgeResponse
from ....dependencies.auth import get_current_user
from ....models.user import User
from ....repositories.badge import BadgeRepository

router = APIRouter()

@router.get("", response_model=List[BadgeResponse])
async def list_my_badges(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all badges for the current user."""
    badge_repo = BadgeRepository()
    badges = await badge_repo.get_by_user(db, user_id=current_user.id)
    return badges
```

**Step 9: Register router**

File: `backend/app/api/api_v1/api.py`
```python
from .endpoints import chores, users, families, health, badges  # Add badges

api_router = APIRouter()

# ... existing routers ...
api_router.include_router(badges.router, prefix="/badges", tags=["badges"])
```

---

### Adding a New Service

**Scenario**: Create a notification service to send notifications.

**Step 1: Create service file**

File: `backend/app/services/notification_service.py`
```python
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from ..repositories.user import UserRepository
from ..models.user import User

class NotificationService:
    """Service for sending notifications to users."""

    def __init__(self):
        self.user_repo = UserRepository()

    async def notify_chore_approved(
        self,
        db: AsyncSession,
        child_id: int,
        chore_title: str,
        reward_amount: float
    ) -> None:
        """
        Send notification when a chore is approved.

        In a real app, this would send email/push notification.
        For now, it just logs the event.
        """
        child = await self.user_repo.get(db, id=child_id)
        if not child:
            return

        # In production: send actual notification
        print(f"📬 Notification to {child.username}: "
              f"Your chore '{chore_title}' was approved! "
              f"You earned ${reward_amount:.2f}")

    async def notify_new_chore(
        self,
        db: AsyncSession,
        child_id: int,
        chore_title: str
    ) -> None:
        """Send notification when a new chore is assigned."""
        child = await self.user_repo.get(db, id=child_id)
        if not child:
            return

        print(f"📬 Notification to {child.username}: "
              f"New chore assigned: '{chore_title}'")

    async def bulk_notify(
        self,
        db: AsyncSession,
        user_ids: List[int],
        message: str
    ) -> None:
        """Send the same notification to multiple users."""
        for user_id in user_ids:
            user = await self.user_repo.get(db, id=user_id)
            if user:
                print(f"📬 Notification to {user.username}: {message}")
```

**Step 2: Use the service in other services**

File: `backend/app/services/chore_service.py`
```python
from .notification_service import NotificationService

class ChoreService(BaseService[Chore, ChoreRepository]):
    def __init__(self):
        super().__init__(ChoreRepository())
        self.user_repo = UserRepository()
        self.assignment_repo = ChoreAssignmentRepository()
        self.notification_service = NotificationService()  # Add this

    async def approve_assignment(
        self,
        db: AsyncSession,
        assignment_id: int,
        parent_id: int,
        reward_value: Optional[float] = None
    ) -> ChoreAssignment:
        """Approve a chore assignment."""
        # ... existing approval logic ...

        # Send notification
        await self.notification_service.notify_chore_approved(
            db,
            child_id=assignment.assignee_id,
            chore_title=assignment.chore.title,
            reward_amount=final_reward
        )

        return assignment
```

**Step 3: Create dependency (optional)**

File: `backend/app/dependencies/services.py`
```python
from typing import Annotated
from fastapi import Depends
from ..services.notification_service import NotificationService

NotificationServiceDep = Annotated[
    NotificationService,
    Depends(lambda: NotificationService())
]
```

**Step 4: Use in endpoints (if needed)**

```python
@router.post("/chores/{chore_id}/send-reminder")
async def send_chore_reminder(
    chore_id: int,
    db: AsyncSession = Depends(get_db),
    notification_service: NotificationServiceDep = None,
):
    """Send reminder notification for a chore."""
    # ... get chore and child ...
    await notification_service.notify_new_chore(
        db,
        child_id=child.id,
        chore_title=chore.title
    )
    return {"status": "notification sent"}
```

---

### Adding a New Repository Method

**Scenario**: Add a method to get chores that are overdue.

File: `backend/app/repositories/chore.py`
```python
from datetime import datetime, timedelta
from sqlalchemy import select, and_

class ChoreRepository(BaseRepository[Chore]):
    async def get_overdue_chores(
        self,
        db: AsyncSession,
        days_overdue: int = 7
    ) -> List[Chore]:
        """
        Get chores that are overdue (created more than N days ago, not completed).

        Args:
            db: Database session
            days_overdue: Number of days to consider overdue (default 7)

        Returns:
            List of overdue chores
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_overdue)

        stmt = select(Chore).where(
            and_(
                Chore.created_at < cutoff_date,
                Chore.is_completed == False,
                Chore.is_disabled == False
            )
        ).order_by(Chore.created_at.asc())

        result = await db.execute(stmt)
        return result.scalars().all()
```

---

## File Organization Patterns

### Naming Conventions

**Files**:
- Models: `backend/app/models/chore.py` (singular, lowercase)
- Schemas: `backend/app/schemas/chore.py` (match model name)
- Repositories: `backend/app/repositories/chore.py` (match model name)
- Services: `backend/app/services/chore_service.py` (model name + `_service`)
- Endpoints: `backend/app/api/api_v1/endpoints/chores.py` (plural, lowercase)

**Classes**:
- Models: `Chore` (singular, PascalCase)
- Schemas: `ChoreCreate`, `ChoreResponse`, `ChoreUpdate` (Model + Action)
- Repositories: `ChoreRepository` (Model + Repository)
- Services: `ChoreService` (Model + Service)

**Methods**:
- Repositories: `get`, `get_multi`, `create`, `update`, `delete` (CRUD operations)
- Services: `create_chore`, `approve_assignment`, `get_user_chores` (business operations)
- Endpoints: `create_chore`, `list_chores`, `get_chore` (REST operations)

### Code Organization Within Files

**Model file structure**:
```python
# 1. Imports
from typing import Optional, List
from datetime import datetime
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

# 2. Type checking imports
if TYPE_CHECKING:
    from .user import User

# 3. Model class
class Chore(Base):
    __tablename__ = "chores"

    # 3a. Primary key
    id: Mapped[int] = mapped_column(primary_key=True)

    # 3b. Required fields
    title: Mapped[str] = mapped_column(String(255))

    # 3c. Optional fields
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 3d. Fields with defaults
    reward: Mapped[float] = mapped_column(Float, default=0.0)

    # 3e. Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # 3f. Foreign keys
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # 3g. Relationships
    creator: Mapped["User"] = relationship("User", back_populates="chores")

    # 3h. Properties
    @property
    def is_new(self) -> bool:
        return datetime.utcnow() - self.created_at < timedelta(hours=1)

    # 3i. Methods
    def __repr__(self) -> str:
        return f"<Chore(id={self.id}, title='{self.title}')>"
```

**Endpoint file structure**:
```python
# 1. Imports (grouped)
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

# 2. Internal imports (relative)
from ....db.base import get_db
from ....schemas.chore import ChoreCreate, ChoreResponse
from ....dependencies.auth import get_current_user
from ....models.user import User

# 3. Router creation
router = APIRouter()

# 4. Endpoints (group by resource/operation)
# 4a. POST endpoints
@router.post("")
async def create_chore(...):
    pass

# 4b. GET endpoints
@router.get("")
async def list_chores(...):
    pass

@router.get("/{chore_id}")
async def get_chore(...):
    pass

# 4c. PUT/PATCH endpoints
@router.put("/{chore_id}")
async def update_chore(...):
    pass

# 4d. DELETE endpoints
@router.delete("/{chore_id}")
async def delete_chore(...):
    pass
```

---

## Import Conventions

### Absolute vs Relative Imports

**In model files**: Use relative imports for same-package modules
```python
# backend/app/models/chore.py
from ..db.base_class import Base  # Relative (preferred)
from backend.app.db.base_class import Base  # Absolute (avoid)
```

**In endpoint files**: Use relative imports (4 levels up from endpoints)
```python
# backend/app/api/api_v1/endpoints/chores.py
from ....db.base import get_db  # 4 levels: endpoints → api_v1 → api → app → db
from ....schemas.chore import ChoreCreate
from ....dependencies.auth import get_current_user
```

**In service files**: Use relative imports
```python
# backend/app/services/chore_service.py
from ..repositories.chore import ChoreRepository
from ..models.chore import Chore
```

### Import Order

Follow this order:
1. Standard library imports
2. Third-party library imports
3. Local application imports

```python
# 1. Standard library
from typing import List, Optional
from datetime import datetime

# 2. Third-party
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

# 3. Local
from ....db.base import get_db
from ....schemas.chore import ChoreCreate
from ....dependencies.auth import get_current_user
```

---

## Code Organization Best Practices

### 1. Keep Layers Separate

❌ **Don't**: Put business logic in endpoints
```python
@router.post("/chores/")
async def create_chore(chore_data: ChoreCreate, db: AsyncSession = Depends(get_db)):
    # Business logic in endpoint - BAD!
    if not current_user.is_parent:
        raise HTTPException(403, "Only parents can create chores")

    for assignee_id in chore_data.assignee_ids:
        assignee = await user_repo.get(db, id=assignee_id)
        if assignee.family_id != current_user.family_id:
            raise HTTPException(403, "Not in family")

    chore = await chore_repo.create(db, obj_in=chore_data.dict())
    return chore
```

✅ **Do**: Put business logic in services
```python
# Endpoint
@router.post("/chores/")
async def create_chore(
    chore_data: ChoreCreate,
    current_user: User = Depends(get_current_parent),
    chore_service: ChoreServiceDep = None
):
    return await chore_service.create_chore(db, creator_id=current_user.id, chore_data=chore_data.dict())

# Service
class ChoreService:
    async def create_chore(self, db, creator_id, chore_data):
        # All business logic here
        pass
```

### 2. Use Dependency Injection

❌ **Don't**: Create instances manually
```python
@router.post("/chores/")
async def create_chore(...):
    chore_service = ChoreService()  # Manual instantiation - BAD
    return await chore_service.create_chore(...)
```

✅ **Do**: Use FastAPI's dependency injection
```python
@router.post("/chores/")
async def create_chore(
    chore_service: ChoreServiceDep = None  # Injected automatically
):
    return await chore_service.create_chore(...)
```

### 3. Write Docstrings

```python
async def create_chore(
    self,
    db: AsyncSession,
    *,
    creator_id: int,
    chore_data: Dict[str, Any]
) -> Chore:
    """
    Create a new chore with multi-assignment support.

    Business rules:
    - Only parents can create chores
    - Assignees must be children in the same family as creator
    - Validate reward ranges for range rewards
    - Create assignments based on assignment mode

    Args:
        db: Database session
        creator_id: ID of the user creating the chore (must be a parent)
        chore_data: Dictionary containing chore fields and assignee_ids

    Returns:
        Created Chore instance with assignments

    Raises:
        HTTPException: 404 if creator or assignee not found
        HTTPException: 403 if creator is not a parent or assignee not in family
        HTTPException: 422 if assignment mode validation fails
    """
    pass
```

### 4. Handle Errors at the Right Layer

- **Repositories**: Return `None` if not found, raise on database errors
- **Services**: Validate business rules, raise `HTTPException` with appropriate status codes
- **Endpoints**: Minimal error handling, mostly for unexpected cases

### 5. Keep Files Focused

- Each file should have a single responsibility
- If a file exceeds 300-400 lines, consider splitting it
- Group related functionality together

### 6. Use Type Hints Everywhere

```python
# Good
async def get_user(db: AsyncSession, user_id: int) -> Optional[User]:
    pass

# Bad
async def get_user(db, user_id):
    pass
```

---

## Quick Reference

### When to Create a New...

**Model**:
- Adding a new database table
- Adding a new entity to the domain

**Schema**:
- Creating a new API endpoint
- Changing validation rules
- Adding new response formats

**Repository**:
- Adding a new model
- Creating specialized database queries

**Service**:
- Implementing new business logic
- Orchestrating multiple repositories
- Adding complex workflows

**Endpoint**:
- Exposing new API functionality
- Creating new HTTP routes

---

## Next Steps

- Read `PYTHON_FASTAPI_CONCEPTS.md` for FastAPI fundamentals
- See `docs/architecture/BACKEND_ARCHITECTURE.md` for architecture deep dive
- Review existing code in `backend/app/` for real-world examples
- Check tests in `backend/tests/` for usage patterns

---

**Remember**: The key to maintainable code is **separation of concerns**. Keep each layer focused on its responsibility, and use the layer above it through well-defined interfaces.
