# FastAPI Concepts for Python Developers

## Table of Contents
1. [Introduction](#introduction)
2. [Async/Await Fundamentals](#asyncawait-fundamentals)
3. [Dependency Injection with Depends()](#dependency-injection-with-depends)
4. [Pydantic v2 Models](#pydantic-v2-models)
5. [SQLAlchemy 2.0 Async Patterns](#sqlalchemy-20-async-patterns)
6. [Request/Response Lifecycle](#requestresponse-lifecycle)
7. [Error Handling](#error-handling)
8. [Testing Async Endpoints](#testing-async-endpoints)
9. [Common Pitfalls](#common-pitfalls)
10. [Best Practices](#best-practices)

---

## Introduction

FastAPI is a modern, high-performance web framework for building APIs with Python 3.11+. This guide covers core concepts using real examples from the chores-tracker application.

**Key Features**:
- Built on modern Python type hints
- Automatic API documentation (OpenAPI/Swagger)
- Fast performance (comparable to Node.js and Go)
- Built-in data validation with Pydantic
- Native async/await support
- Dependency injection system

**Prerequisites**:
- Python 3.11+ knowledge
- Basic understanding of HTTP and REST APIs
- Familiarity with type hints

---

## Async/Await Fundamentals

### What is Async/Await?

Async/await allows non-blocking I/O operations. While one request waits for the database, other requests can be processed.

**Traditional synchronous code** (blocking):
```python
def get_user(user_id: int):
    user = database.query(User).filter(User.id == user_id).first()  # BLOCKS
    return user
```

**Async code** (non-blocking):
```python
async def get_user(user_id: int):
    user = await database.query(User).filter(User.id == user_id).first()  # NON-BLOCKING
    return user
```

### When to Use Async

**Use async when**:
- Making database queries (SQLAlchemy async)
- Calling external APIs (httpx)
- File I/O operations
- Any I/O-bound operation

**Don't use async when**:
- Doing CPU-intensive calculations (use threads/processes instead)
- Working with synchronous libraries (can block event loop)

### Real Example from Chores Tracker

```python
# backend/app/dependencies/auth.py
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get the current authenticated user."""
    # verify_token is CPU-bound, so it's synchronous (no await)
    user_id = verify_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Database query is I/O-bound, so we await it
    user = await user_repo.get(db, id=int(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
```

### Async Context Managers

Use `async with` for async context managers:

```python
# backend/app/db/base.py
async def get_db():
    """Dependency that provides a database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

### Common Async Patterns

**Pattern 1: Await multiple operations concurrently**
```python
import asyncio

# Sequential (slow)
user = await get_user(user_id)
chores = await get_chores(user_id)
# Total time: time(get_user) + time(get_chores)

# Concurrent (fast)
user, chores = await asyncio.gather(
    get_user(user_id),
    get_chores(user_id)
)
# Total time: max(time(get_user), time(get_chores))
```

**Pattern 2: Async loops**
```python
# DON'T do this (runs sequentially):
for assignee_id in assignee_ids:
    user = await get_user(assignee_id)

# DO this (runs concurrently):
users = await asyncio.gather(
    *[get_user(assignee_id) for assignee_id in assignee_ids]
)
```

---

## Dependency Injection with Depends()

### What is Dependency Injection?

Dependency injection provides shared resources (database sessions, authentication, configuration) to your endpoint functions automatically.

### Basic Dependency

```python
from fastapi import Depends, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from ..db.base import get_db

router = APIRouter()

@router.get("/users/me")
async def read_users_me(
    db: AsyncSession = Depends(get_db)  # Database session injected
):
    """Get current user."""
    # db is ready to use - no need to create/close it manually
    result = await db.execute(select(User))
    return result.scalars().first()
```

### Chained Dependencies

Dependencies can depend on other dependencies:

```python
# backend/app/dependencies/auth.py

# Level 1: Get database session
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

# Level 2: Get authenticated user (depends on get_db)
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)  # Depends on get_db
) -> User:
    user_id = verify_token(token)
    user = await user_repo.get(db, id=int(user_id))
    return user

# Level 3: Get parent user (depends on get_current_user)
async def get_current_parent(
    current_user: User = Depends(get_current_user)  # Depends on get_current_user
) -> User:
    if not current_user.is_parent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This operation requires parent privileges"
        )
    return current_user

# Usage in endpoint
@router.post("/chores/")
async def create_chore(
    chore_data: ChoreCreate,
    current_user: User = Depends(get_current_parent)  # All dependencies executed automatically
):
    # current_user is guaranteed to be an authenticated parent
    pass
```

### Dependency Execution Flow

When you call an endpoint with `Depends(get_current_parent)`:
1. FastAPI calls `get_db()` → provides `db` session
2. FastAPI calls `get_current_user(db=db)` → provides authenticated `User`
3. FastAPI calls `get_current_parent(current_user=user)` → validates parent role
4. Your endpoint receives the parent `User`

### Class-Based Dependencies

```python
# backend/app/dependencies/services.py
from typing import Annotated
from fastapi import Depends

class ChoreServiceDep:
    """Dependency for chore service injection."""
    pass

# Type alias for cleaner code
ChoreServiceDep = Annotated[ChoreService, Depends(lambda: ChoreService())]

# Usage
@router.post("/chores/")
async def create_chore(
    chore_data: ChoreCreate,
    chore_service: ChoreServiceDep = None  # Service injected automatically
):
    return await chore_service.create_chore(...)
```

### Dependency Caching

FastAPI caches dependency results **within a single request**:

```python
@router.get("/example")
async def example(
    user1: User = Depends(get_current_user),
    user2: User = Depends(get_current_user)  # Same instance as user1
):
    assert user1 is user2  # True - cached within request
```

---

## Pydantic v2 Models

### What is Pydantic?

Pydantic validates incoming data using Python type hints. FastAPI uses Pydantic for:
- Request body validation
- Response serialization
- Automatic API documentation

### Basic Schema Definition

```python
# backend/app/schemas/chore.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Literal
from datetime import datetime

class ChoreBase(BaseModel):
    """Base chore schema with common fields."""
    title: str = Field(
        ...,  # Required field
        description="Title of the chore",
        min_length=1,
        max_length=200,
        json_schema_extra={"example": "Clean the kitchen"}
    )
    description: Optional[str] = Field(
        None,  # Optional field
        description="Detailed description of what needs to be done",
        max_length=1000,
        json_schema_extra={"example": "Wipe counters, wash dishes, sweep floor"}
    )
    reward: float = Field(
        0.0,  # Default value
        description="Fixed reward amount",
        ge=0,  # Greater than or equal to 0
        le=1000,  # Less than or equal to 1000
        json_schema_extra={"example": 5.0}
    )
```

### Schema Inheritance

```python
# Base schema with common fields
class ChoreBase(BaseModel):
    title: str
    description: Optional[str] = None
    reward: float = 0.0

# Create schema (what the API accepts)
class ChoreCreate(ChoreBase):
    assignee_ids: List[int] = Field(
        default_factory=list,
        description="List of child user IDs to assign this chore to"
    )
    assignment_mode: Literal['single', 'multi_independent', 'unassigned'] = 'single'

# Response schema (what the API returns)
class ChoreResponse(ChoreBase):
    id: int
    creator_id: int
    created_at: datetime
    is_completed: bool

    model_config = ConfigDict(from_attributes=True)  # Pydantic v2 syntax
```

### Field Validation

**Built-in validators**:
```python
from pydantic import BaseModel, Field, EmailStr, field_validator

class UserCreate(BaseModel):
    email: EmailStr  # Validates email format
    username: str = Field(min_length=3, max_length=50, pattern="^[a-zA-Z0-9_]+$")
    age: int = Field(ge=0, le=120)  # 0 <= age <= 120
```

**Custom validators**:
```python
class ChoreBase(BaseModel):
    min_reward: Optional[float] = None
    max_reward: Optional[float] = None

    @field_validator('max_reward')
    @classmethod
    def validate_reward_range(cls, v, info):
        """Validate that max_reward > min_reward."""
        if v is not None and 'min_reward' in info.data and info.data['min_reward'] is not None:
            if v < info.data['min_reward']:
                raise ValueError('max_reward must be greater than min_reward')
        return v
```

### Configuration

Pydantic v2 uses `model_config` instead of nested `Config` class:

```python
from pydantic import BaseModel, ConfigDict

# Pydantic v2 (chores-tracker uses this)
class UserResponse(BaseModel):
    id: int
    username: str
    email: str

    model_config = ConfigDict(
        from_attributes=True,  # Allow creating from ORM models
        json_schema_extra={
            "example": {
                "id": 1,
                "username": "parent_user",
                "email": "parent@example.com"
            }
        }
    )
```

### Using Schemas in Endpoints

```python
@router.post("/chores/", response_model=ChoreResponse)
async def create_chore(
    chore_data: ChoreCreate,  # Request body validated against ChoreCreate
    db: AsyncSession = Depends(get_db)
) -> ChoreResponse:  # Response validated against ChoreResponse
    """
    FastAPI automatically:
    1. Validates incoming JSON against ChoreCreate schema
    2. Converts validated data to ChoreCreate instance
    3. Validates return value against ChoreResponse
    4. Serializes ChoreResponse to JSON
    """
    chore = await chore_service.create_chore(db, chore_data)
    return chore  # Converted to JSON automatically
```

---

## SQLAlchemy 2.0 Async Patterns

### ORM Model Definition

```python
# backend/app/models/chore.py
from typing import Optional, List
from datetime import datetime
from sqlalchemy import String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from ..db.base_class import Base

class Chore(Base):
    __tablename__ = "chores"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Required fields
    title: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str] = mapped_column(Text)

    # Optional fields (nullable)
    min_reward: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_reward: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Fields with defaults
    reward: Mapped[float] = mapped_column(Float, default=0.0)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )

    # Foreign keys
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # Relationships
    creator: Mapped["User"] = relationship("User", back_populates="chores_created")
    assignments: Mapped[List["ChoreAssignment"]] = relationship(
        "ChoreAssignment",
        back_populates="chore",
        cascade="all, delete-orphan"
    )
```

### Basic CRUD Operations

**Repository pattern** (recommended approach):

```python
# backend/app/repositories/base.py
from typing import Generic, TypeVar, Type, Optional, List, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    """Base repository with common CRUD operations."""

    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        """Get a record by ID."""
        query = select(self.model).where(self.model.id == id)
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
        await db.execute(
            update(self.model)
            .where(self.model.id == id)
            .values(**obj_in)
        )
        await db.commit()
        return await self.get(db, id)

    async def delete(self, db: AsyncSession, *, id: Any) -> None:
        """Delete a record."""
        await db.execute(delete(self.model).where(self.model.id == id))
        await db.commit()
```

### Querying Patterns

**Simple select**:
```python
from sqlalchemy import select

async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    return result.scalars().first()
```

**Multiple conditions**:
```python
async def get_active_chores(db: AsyncSession, creator_id: int) -> List[Chore]:
    stmt = select(Chore).where(
        Chore.creator_id == creator_id,
        Chore.is_disabled == False
    )
    result = await db.execute(stmt)
    return result.scalars().all()
```

**Joins**:
```python
from sqlalchemy.orm import joinedload

async def get_chore_with_creator(db: AsyncSession, chore_id: int) -> Optional[Chore]:
    """Get chore with creator relationship loaded (avoid N+1 queries)."""
    stmt = select(Chore).where(Chore.id == chore_id).options(
        joinedload(Chore.creator)  # Eager load relationship
    )
    result = await db.execute(stmt)
    return result.scalars().first()
```

**Aggregations**:
```python
from sqlalchemy import func, select

async def count_pending_approvals(db: AsyncSession) -> int:
    stmt = select(func.count()).select_from(ChoreAssignment).where(
        ChoreAssignment.is_completed == True,
        ChoreAssignment.is_approved == False
    )
    result = await db.execute(stmt)
    return result.scalar()
```

### Transaction Management

**Unit of Work pattern**:

```python
# backend/app/core/unit_of_work.py
class UnitOfWork:
    """Manages database transactions across multiple repositories."""

    async def __aenter__(self):
        self.session = AsyncSessionLocal()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.rollback()
        await self.close()

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()

    async def close(self):
        await self.session.close()

# Usage
async with UnitOfWork() as uow:
    # Create user
    user = await uow.users.create(db=uow.session, obj_in=user_data)

    # Create initial chore
    chore = await uow.chores.create(db=uow.session, obj_in=chore_data)

    # Commit both operations together
    await uow.commit()
    # If any operation fails, both are rolled back
```

---

## Request/Response Lifecycle

### Complete Request Flow

```
1. Client sends HTTP request
   ↓
2. FastAPI middleware (CORS, rate limiting)
   ↓
3. Route matching
   ↓
4. Dependency injection (execute all Depends() functions)
   ↓
5. Request validation (Pydantic schema)
   ↓
6. Endpoint function execution
   ↓
7. Response validation (Pydantic schema)
   ↓
8. Response serialization to JSON
   ↓
9. Middleware processing (reverse order)
   ↓
10. HTTP response sent to client
```

### Example Endpoint Lifecycle

```python
@router.post("/chores/", response_model=ChoreResponse)
async def create_chore(
    chore_data: ChoreCreate,  # Step 5: Validated
    db: AsyncSession = Depends(get_db),  # Step 4a: Injected
    current_user: User = Depends(get_current_parent),  # Step 4b: Injected & validated
) -> ChoreResponse:  # Step 7: Return type validated
    # Step 6: Your code executes here
    chore = await chore_service.create_chore(db, creator_id=current_user.id, chore_data=chore_data.dict())
    return chore  # Step 8: Serialized to JSON
```

**What FastAPI does automatically**:
1. Validates `chore_data` matches `ChoreCreate` schema
2. Returns 422 if validation fails
3. Creates database session via `get_db()`
4. Authenticates user via `get_current_parent()`
5. Returns 401/403 if auth fails
6. Validates return value matches `ChoreResponse`
7. Serializes `ChoreResponse` to JSON
8. Closes database session

### Request Data Sources

```python
from fastapi import Path, Query, Body, Header, Cookie, Form

@router.get("/chores/{chore_id}")
async def get_chore(
    # Path parameter
    chore_id: int = Path(..., description="Chore ID", ge=1),

    # Query parameter (?include_disabled=true)
    include_disabled: bool = Query(False, description="Include disabled chores"),

    # Header
    user_agent: str = Header(None, alias="User-Agent"),

    # Cookie
    session_id: str = Cookie(None),
):
    pass

@router.post("/chores/")
async def create_chore(
    # JSON body
    chore_data: ChoreCreate = Body(...),

    # Or form data
    title: str = Form(...),
    description: str = Form(None),
):
    pass
```

---

## Error Handling

### HTTP Exceptions

```python
from fastapi import HTTPException, status

@router.get("/chores/{chore_id}")
async def get_chore(
    chore_id: int,
    db: AsyncSession = Depends(get_db)
):
    chore = await chore_repo.get(db, id=chore_id)

    if not chore:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chore not found"
        )

    if chore.is_disabled:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Chore has been disabled",
            headers={"X-Disabled-At": str(chore.updated_at)}
        )

    return chore
```

### Custom Exception Handlers

```python
# backend/app/core/exceptions.py
from fastapi import Request
from fastapi.responses import JSONResponse

class ChoreNotAvailableError(Exception):
    """Raised when a chore is not available for completion."""
    def __init__(self, message: str):
        self.message = message

# Register handler in main.py
@app.exception_handler(ChoreNotAvailableError)
async def chore_not_available_handler(request: Request, exc: ChoreNotAvailableError):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": exc.message}
    )
```

### Validation Error Responses

FastAPI automatically returns detailed validation errors:

```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "title"],
      "msg": "String should have at least 1 character",
      "input": "",
      "ctx": {"min_length": 1}
    },
    {
      "type": "greater_than_equal",
      "loc": ["body", "reward"],
      "msg": "Input should be greater than or equal to 0",
      "input": -5.0,
      "ctx": {"ge": 0.0}
    }
  ]
}
```

---

## Testing Async Endpoints

### Test Setup

```python
# backend/tests/conftest.py
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Create a fresh database for each test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    """Return a FastAPI test client with overridden dependencies."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
```

### Writing Tests

```python
import pytest

@pytest.mark.asyncio
async def test_create_chore(client, test_parent_token):
    """Test creating a chore."""
    response = await client.post(
        "/api/v1/chores/",
        json={
            "title": "Clean Room",
            "description": "Organize and vacuum",
            "reward": 5.0,
            "assignee_ids": [2]
        },
        headers={"Authorization": f"Bearer {test_parent_token}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Clean Room"
    assert data["reward"] == 5.0

@pytest.mark.asyncio
async def test_unauthorized_access(client):
    """Test that endpoints require authentication."""
    response = await client.get("/api/v1/chores/")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_validation_error(client, test_parent_token):
    """Test that validation errors are returned."""
    response = await client.post(
        "/api/v1/chores/",
        json={
            "title": "",  # Too short
            "reward": -5.0,  # Negative
        },
        headers={"Authorization": f"Bearer {test_parent_token}"}
    )

    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any(e["loc"] == ["body", "title"] for e in errors)
    assert any(e["loc"] == ["body", "reward"] for e in errors)
```

---

## Common Pitfalls

### 1. Forgetting `await`

❌ **Wrong**:
```python
async def get_user(db: AsyncSession, user_id: int):
    user = user_repo.get(db, id=user_id)  # Missing await!
    return user
# Returns a coroutine object, not a User
```

✅ **Correct**:
```python
async def get_user(db: AsyncSession, user_id: int):
    user = await user_repo.get(db, id=user_id)
    return user
```

### 2. Using Sync Code in Async Functions

❌ **Wrong**:
```python
import time

async def slow_endpoint():
    time.sleep(5)  # BLOCKS the entire event loop!
    return {"status": "done"}
```

✅ **Correct**:
```python
import asyncio

async def slow_endpoint():
    await asyncio.sleep(5)  # Non-blocking
    return {"status": "done"}
```

### 3. Session Management Issues

❌ **Wrong**:
```python
async def get_user_chores(db: AsyncSession, user_id: int):
    user = await user_repo.get(db, id=user_id)
    await db.close()  # Session closed!
    return user.chores  # Lazy loading fails - session is closed
```

✅ **Correct**:
```python
from sqlalchemy.orm import joinedload

async def get_user_chores(db: AsyncSession, user_id: int):
    stmt = select(User).where(User.id == user_id).options(
        joinedload(User.chores)  # Eager load
    )
    result = await db.execute(stmt)
    user = result.scalars().first()
    return user.chores  # Already loaded
```

### 4. N+1 Query Problem

❌ **Wrong**:
```python
async def get_all_chores_with_creators(db: AsyncSession):
    chores = await chore_repo.get_multi(db)
    result = []
    for chore in chores:
        creator = await user_repo.get(db, id=chore.creator_id)  # N queries!
        result.append({
            "chore": chore,
            "creator": creator
        })
    return result
```

✅ **Correct**:
```python
from sqlalchemy.orm import joinedload

async def get_all_chores_with_creators(db: AsyncSession):
    stmt = select(Chore).options(joinedload(Chore.creator))  # 1 query with JOIN
    result = await db.execute(stmt)
    chores = result.scalars().all()
    return chores  # creator already loaded for each chore
```

### 5. Mutable Default Arguments

❌ **Wrong**:
```python
class ChoreCreate(BaseModel):
    assignee_ids: List[int] = []  # Mutable default!
```

✅ **Correct**:
```python
from typing import List
from pydantic import Field

class ChoreCreate(BaseModel):
    assignee_ids: List[int] = Field(default_factory=list)
```

### 6. Not Handling Optional Fields

❌ **Wrong**:
```python
@router.post("/chores/")
async def create_chore(chore: ChoreCreate):
    reward = chore.min_reward + chore.max_reward  # NoneType error if not set!
```

✅ **Correct**:
```python
@router.post("/chores/")
async def create_chore(chore: ChoreCreate):
    if chore.is_range_reward and chore.min_reward and chore.max_reward:
        avg_reward = (chore.min_reward + chore.max_reward) / 2
    else:
        avg_reward = chore.reward
```

---

## Best Practices

### 1. Use Type Hints Everywhere

```python
# Good
async def create_chore(
    db: AsyncSession,
    creator_id: int,
    chore_data: Dict[str, Any]
) -> Chore:
    pass

# Bad
async def create_chore(db, creator_id, chore_data):
    pass
```

### 2. Separate Concerns with Layers

```
Endpoint (API) → Service (Business Logic) → Repository (Data Access) → Model (Database)
```

```python
# Endpoint: Handle HTTP concerns
@router.post("/chores/")
async def create_chore(
    chore_data: ChoreCreate,
    current_user: User = Depends(get_current_parent),
    chore_service: ChoreServiceDep = None
):
    return await chore_service.create_chore(db, creator_id=current_user.id, chore_data=chore_data.dict())

# Service: Business logic
class ChoreService:
    async def create_chore(self, db: AsyncSession, creator_id: int, chore_data: Dict) -> Chore:
        # Validate business rules
        # Create chore
        # Create assignments
        # Log activity
        pass

# Repository: Data access
class ChoreRepository:
    async def create(self, db: AsyncSession, obj_in: Dict) -> Chore:
        # Simple CRUD operation
        pass
```

### 3. Use Pydantic for All Data Validation

```python
# Don't validate manually
if not 0 <= chore_data["reward"] <= 1000:
    raise HTTPException(400, "Invalid reward")

# Let Pydantic handle it
class ChoreCreate(BaseModel):
    reward: float = Field(ge=0, le=1000)
```

### 4. Document Your Endpoints

```python
@router.post(
    "/chores/",
    response_model=ChoreResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new chore",
    description="""
    Create a new chore and assign it to children.

    **Access**: Parents only

    **Reward Types**:
    - Fixed reward: Single amount
    - Range reward: Min/max, parent chooses during approval
    """,
    responses={
        201: {"description": "Chore created successfully"},
        403: {"description": "Only parents can create chores"},
        404: {"description": "Assignee not found"}
    }
)
async def create_chore(...):
    """Create a new chore and assign it to a child."""
    pass
```

### 5. Use Environment Variables for Configuration

```python
# backend/app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Chores Tracker API"
    DATABASE_URL: str
    SECRET_KEY: str

    class Config:
        env_file = ".env"

settings = Settings()
```

### 6. Handle Errors Gracefully

```python
async def approve_assignment(db: AsyncSession, assignment_id: int, parent_id: int):
    assignment = await assignment_repo.get(db, id=assignment_id)

    if not assignment:
        raise HTTPException(404, "Assignment not found")

    if assignment.is_approved:
        raise HTTPException(409, "Assignment already approved")

    if not assignment.is_completed:
        raise HTTPException(400, "Cannot approve incomplete assignment")

    # Business logic here
```

### 7. Test Business Logic, Not Just Endpoints

```python
# Test service layer directly
@pytest.mark.asyncio
async def test_chore_service_validates_family_access(db_session):
    service = ChoreService()

    with pytest.raises(HTTPException) as exc_info:
        await service.create_chore(
            db=db_session,
            creator_id=1,  # Parent from family A
            chore_data={"assignee_ids": [99]}  # Child from family B
        )

    assert exc_info.value.status_code == 403
```

### 8. Use Meaningful Variable Names

```python
# Bad
u = await get_user(db, id=1)
c = await create_chore(db, u.id, cd)

# Good
current_user = await get_user(db, id=1)
new_chore = await create_chore(db, current_user.id, chore_data)
```

---

## Additional Resources

- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **Pydantic Documentation**: https://docs.pydantic.dev/
- **SQLAlchemy 2.0 Documentation**: https://docs.sqlalchemy.org/en/20/
- **Async Python Guide**: https://realpython.com/async-io-python/
- **Backend Architecture**: See `docs/architecture/BACKEND_ARCHITECTURE.md` for architecture deep dive
- **Project Structure**: See `docs/development/PYTHON_FASTAPI_STRUCTURE.md` for code organization

---

**Next Steps**: Read `PYTHON_FASTAPI_STRUCTURE.md` to learn how to organize code and add new features to the chores-tracker project.
