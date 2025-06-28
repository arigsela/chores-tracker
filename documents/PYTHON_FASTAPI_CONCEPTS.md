# Python and FastAPI Concepts Explained

This document explains key Python and FastAPI concepts with examples, building from fundamental concepts to more advanced patterns.

## Table of Contents
1. [Python Decorators](#python-decorators)
2. [Async/Await](#asyncawait)
3. [Type Hints](#type-hints)
4. [Pydantic](#pydantic)
5. [Dependency Injection](#dependency-injection)
6. [CORS Middleware](#cors-middleware)
7. [Repository Layer Pattern](#repository-layer-pattern)
8. [Package Managers](#package-managers)

## Python Decorators

Decorators are a powerful Python feature that allows you to modify or enhance functions without changing their source code. They use the `@` symbol and are placed above function definitions.

### Basic Decorator Example

```python
# A simple decorator that logs function calls
def log_function_call(func):
    def wrapper(*args, **kwargs):
        print(f"Calling function: {func.__name__}")
        result = func(*args, **kwargs)
        print(f"Function {func.__name__} completed")
        return result
    return wrapper

# Using the decorator
@log_function_call
def greet(name):
    return f"Hello, {name}!"

# When you call greet("Alice"), it prints:
# Calling function: greet
# Function greet completed
# And returns: "Hello, Alice!"
```

### Decorator with Arguments

```python
# A decorator that retries a function on failure
def retry(max_attempts=3):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    print(f"Attempt {attempt + 1} failed, retrying...")
            return None
        return wrapper
    return decorator

@retry(max_attempts=5)
def unstable_network_call():
    # Some network operation that might fail
    pass
```

### Real-World FastAPI Example

```python
from fastapi import FastAPI, Depends, HTTPException
from functools import wraps

# Custom decorator for rate limiting
def rate_limit(calls: int = 10, period: int = 60):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Rate limiting logic here
            return await func(*args, **kwargs)
        return wrapper
    return decorator

app = FastAPI()

@app.get("/api/data")
@rate_limit(calls=5, period=60)  # Allow 5 calls per minute
async def get_data():
    return {"data": "example"}
```

## Async/Await

Async/await is Python's way of handling asynchronous programming, allowing code to run concurrently without blocking.

### Basic Concepts

```python
import asyncio

# Synchronous (blocking) code
def fetch_data_sync():
    # This blocks the entire program for 2 seconds
    time.sleep(2)
    return "data"

# Asynchronous (non-blocking) code
async def fetch_data_async():
    # This allows other code to run during the 2-second wait
    await asyncio.sleep(2)
    return "data"

# Running async code
async def main():
    # Run multiple async operations concurrently
    results = await asyncio.gather(
        fetch_data_async(),
        fetch_data_async(),
        fetch_data_async()
    )
    # This takes ~2 seconds total, not 6 seconds!
    return results
```

### How It Works

1. **Event Loop**: Python runs an event loop that manages async tasks
2. **Coroutines**: Functions defined with `async def` are coroutines
3. **Await**: The `await` keyword pauses the coroutine and allows others to run
4. **Non-blocking**: While one coroutine waits (e.g., for I/O), others can execute

### FastAPI Example

```python
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

app = FastAPI()

# Async route handler
@app.get("/users/{user_id}")
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    # Async database query
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user

# Multiple async operations
@app.post("/process-order")
async def process_order(order: OrderCreate):
    # These operations run concurrently
    results = await asyncio.gather(
        validate_inventory(order.items),
        check_user_credit(order.user_id),
        calculate_shipping(order.address)
    )
    
    # Process results...
    return {"status": "processed"}
```

## Type Hints

Type hints are Python's way of indicating expected types for variables, function parameters, and return values. They improve code readability and enable better IDE support.

### Basic Type Hints

```python
# Basic types
name: str = "Alice"
age: int = 25
height: float = 5.6
is_student: bool = True

# Function with type hints
def greet(name: str, age: int) -> str:
    return f"{name} is {age} years old"

# Collections
from typing import List, Dict, Optional, Union

# List of integers
numbers: List[int] = [1, 2, 3]

# Dictionary with string keys and integer values
scores: Dict[str, int] = {"Alice": 95, "Bob": 87}

# Optional (can be None)
middle_name: Optional[str] = None  # Same as: str | None in Python 3.10+

# Union (multiple possible types)
id_value: Union[int, str] = "ABC123"  # Can be int or str
```

### Advanced Type Hints

```python
from typing import TypeVar, Generic, Callable, Tuple

# Type variables for generics
T = TypeVar('T')

# Generic function
def first_item(items: List[T]) -> Optional[T]:
    return items[0] if items else None

# Callable type hint
def apply_function(
    func: Callable[[int, int], int],
    a: int,
    b: int
) -> int:
    return func(a, b)

# Tuple with specific types
coordinates: Tuple[float, float] = (10.5, 20.3)

# Type alias
UserId = int
UserScores = Dict[UserId, int]

def get_top_scorer(scores: UserScores) -> UserId:
    return max(scores, key=scores.get)
```

## Pydantic

Pydantic is a data validation library that uses Python type annotations to validate data and serialize/deserialize between Python objects and JSON.

### Basic Pydantic Model

```python
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List

# Basic model
class User(BaseModel):
    id: int
    name: str
    email: str
    age: int = Field(gt=0, le=150)  # Constraints: greater than 0, less than or equal to 150
    is_active: bool = True  # Default value

# Usage
user_data = {
    "id": 1,
    "name": "Alice",
    "email": "alice@example.com",
    "age": 25
}

user = User(**user_data)  # Validates and creates User instance
print(user.json())  # Converts to JSON string
print(user.dict())  # Converts to dictionary
```

### Advanced Pydantic Features

```python
from pydantic import BaseModel, validator, root_validator
from typing import Optional
from datetime import date

class ChoreCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    assignee_id: int
    reward_type: str = Field(..., regex="^(fixed|range)$")
    reward_amount: float = Field(gt=0)
    max_reward: Optional[float] = None
    due_date: Optional[date] = None
    recurrence_pattern: Optional[str] = None
    
    # Field validator
    @validator('title')
    def title_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty or just whitespace')
        return v.strip()
    
    # Root validator (validates entire model)
    @root_validator
    def validate_reward_range(cls, values):
        reward_type = values.get('reward_type')
        reward_amount = values.get('reward_amount')
        max_reward = values.get('max_reward')
        
        if reward_type == 'range' and max_reward is None:
            raise ValueError('max_reward is required for range rewards')
        
        if reward_type == 'range' and max_reward and max_reward <= reward_amount:
            raise ValueError('max_reward must be greater than reward_amount')
        
        return values

    # Pydantic v2 configuration
    class Config:
        # Allow using the model with ORM objects
        from_attributes = True
        # Custom JSON schema modifications
        json_schema_extra = {
            "example": {
                "title": "Clean your room",
                "description": "Make bed, vacuum, organize desk",
                "assignee_id": 2,
                "reward_type": "fixed",
                "reward_amount": 5.00
            }
        }
```

### Pydantic with FastAPI

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI()

class ItemCreate(BaseModel):
    name: str
    price: float
    quantity: int = 1

class ItemResponse(BaseModel):
    id: int
    name: str
    price: float
    quantity: int
    total_value: float
    
    @property
    def total_value(self) -> float:
        return self.price * self.quantity

@app.post("/items", response_model=ItemResponse)
async def create_item(item: ItemCreate):
    # FastAPI automatically:
    # 1. Validates the request body against ItemCreate
    # 2. Converts JSON to Python object
    # 3. Returns 422 error if validation fails
    
    # Create item in database...
    new_item = {
        "id": 1,
        **item.dict()
    }
    
    # FastAPI automatically:
    # 1. Validates response against ItemResponse
    # 2. Converts Python object to JSON
    # 3. Generates OpenAPI schema
    return ItemResponse(**new_item)
```

## Dependency Injection

Dependency Injection (DI) is a design pattern where dependencies are provided to an object rather than the object creating them itself.

### General Concept

```python
# Without Dependency Injection (tightly coupled)
class EmailService:
    def send(self, message):
        # Send email via SMTP
        pass

class UserService:
    def __init__(self):
        # Creating dependency inside the class (tight coupling)
        self.email_service = EmailService()
    
    def register_user(self, user_data):
        # Register user...
        self.email_service.send("Welcome!")

# With Dependency Injection (loosely coupled)
class UserService:
    def __init__(self, email_service):
        # Dependency is injected from outside
        self.email_service = email_service
    
    def register_user(self, user_data):
        # Register user...
        self.email_service.send("Welcome!")

# Usage
email_service = EmailService()
user_service = UserService(email_service)  # Inject dependency

# Benefits:
# 1. Easy to test (can inject mock email service)
# 2. Flexible (can swap email service implementation)
# 3. Clear dependencies
```

### FastAPI Dependency Injection

FastAPI has a powerful built-in DI system using the `Depends` function:

```python
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

app = FastAPI()

# Database session dependency
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Current user dependency
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    # Validate token
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    user_id = payload.get("sub")
    
    # Get user from database
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

# Using dependencies in routes
@app.get("/profile")
async def get_profile(
    current_user: User = Depends(get_current_user)
):
    return current_user

@app.get("/chores")
async def get_user_chores(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 10
):
    # Dependencies are automatically resolved
    query = select(Chore).where(Chore.assignee_id == current_user.id)
    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()
```

### Function-Based Dependency Injection

Function-based DI uses functions as factories to create dependencies:

```python
from fastapi import Depends
from typing import Optional

# Simple function dependency
def get_query_params(
    q: Optional[str] = None,
    skip: int = 0,
    limit: int = 10
) -> dict:
    return {"q": q, "skip": skip, "limit": limit}

# Dependency with sub-dependencies
def get_user_service(
    db: AsyncSession = Depends(get_db),
    cache: Redis = Depends(get_cache)
) -> UserService:
    return UserService(db, cache)

# Class-based dependency (callable class)
class RateLimiter:
    def __init__(self, calls: int = 10, period: int = 60):
        self.calls = calls
        self.period = period
    
    async def __call__(self, request: Request) -> bool:
        # Check rate limit
        client_ip = request.client.host
        # Rate limiting logic...
        return True

# Using dependencies
@app.get("/search")
async def search(
    params: dict = Depends(get_query_params),
    user_service: UserService = Depends(get_user_service),
    rate_limit_ok: bool = Depends(RateLimiter(calls=5, period=60))
):
    if not rate_limit_ok:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    return await user_service.search(**params)

# Dependency override for testing
app.dependency_overrides[get_db] = get_test_db
```

## CORS Middleware

CORS (Cross-Origin Resource Sharing) is a security feature implemented by web browsers to control access to resources from different domains.

### Understanding CORS

```python
# The Problem:
# Frontend: https://myapp.com
# Backend API: https://api.myapp.com
# 
# Without CORS, the browser blocks the frontend from accessing the API
# because they're on different origins (different domains/ports/protocols)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    # Which origins can access your API
    allow_origins=[
        "http://localhost:3000",  # Local development
        "https://myapp.com",      # Production frontend
        "https://www.myapp.com"   # WWW version
    ],
    # Or allow all origins (not recommended for production)
    # allow_origins=["*"],
    
    # Allow cookies to be sent with requests
    allow_credentials=True,
    
    # Which HTTP methods are allowed
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    
    # Which headers can be sent with requests
    allow_headers=["*"],
    
    # Which headers the browser can access from the response
    expose_headers=["X-Total-Count", "X-Page-Number"]
)
```

### How CORS Works

1. **Preflight Request**: For complex requests, the browser first sends an OPTIONS request
2. **CORS Headers**: The server responds with headers indicating what's allowed
3. **Actual Request**: If allowed, the browser sends the actual request

```python
# CORS Headers Example
# Browser sends:
OPTIONS /api/users HTTP/1.1
Origin: https://myapp.com
Access-Control-Request-Method: POST
Access-Control-Request-Headers: Content-Type, Authorization

# Server responds:
HTTP/1.1 200 OK
Access-Control-Allow-Origin: https://myapp.com
Access-Control-Allow-Methods: GET, POST, PUT, DELETE
Access-Control-Allow-Headers: Content-Type, Authorization
Access-Control-Allow-Credentials: true
Access-Control-Max-Age: 86400  # Cache preflight for 24 hours
```

### Common CORS Scenarios

```python
# Development setup (allow all origins)
if settings.DEBUG:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Production setup (restrict origins)
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )

# Dynamic origin validation
@app.middleware("http")
async def validate_origin(request: Request, call_next):
    origin = request.headers.get("origin")
    
    # Custom origin validation logic
    if origin and is_valid_origin(origin):
        response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = origin
        return response
    
    return await call_next(request)
```

## Repository Layer Pattern

The Repository pattern is a layer of abstraction over data access logic, providing a more object-oriented view of the persistence layer.

### Concept and Relationship to 3-Tier Architecture

```
Traditional 3-Tier Architecture:
┌─────────────────┐
│ Presentation    │  (UI - HTML, React, etc.)
├─────────────────┤
│ Business Logic  │  (Services, Use Cases)
├─────────────────┤
│ Data Access     │  (Direct database queries)
└─────────────────┘

With Repository Pattern:
┌─────────────────┐
│ Presentation    │  (UI - Controllers/Routes)
├─────────────────┤
│ Business Logic  │  (Services)
├─────────────────┤
│ Repository      │  (Abstraction layer)
├─────────────────┤
│ Data Access     │  (ORM/Database)
└─────────────────┘
```

### Basic Repository Implementation

```python
from typing import Generic, TypeVar, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

T = TypeVar('T')

class BaseRepository(Generic[T]):
    """Base repository providing common CRUD operations"""
    
    def __init__(self, model: T, db: AsyncSession):
        self.model = model
        self.db = db
    
    async def get(self, id: int) -> Optional[T]:
        """Get a single record by ID"""
        return await self.db.get(self.model, id)
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all records with pagination"""
        result = await self.db.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return result.scalars().all()
    
    async def create(self, **kwargs) -> T:
        """Create a new record"""
        db_obj = self.model(**kwargs)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj
    
    async def update(self, id: int, **kwargs) -> Optional[T]:
        """Update an existing record"""
        db_obj = await self.get(id)
        if db_obj:
            for key, value in kwargs.items():
                setattr(db_obj, key, value)
            await self.db.commit()
            await self.db.refresh(db_obj)
        return db_obj
    
    async def delete(self, id: int) -> bool:
        """Delete a record"""
        db_obj = await self.get(id)
        if db_obj:
            await self.db.delete(db_obj)
            await self.db.commit()
            return True
        return False
```

### Specific Repository Implementation

```python
from typing import List, Optional
from sqlalchemy import select, and_
from datetime import datetime

class ChoreRepository(BaseRepository[Chore]):
    """Repository for Chore-specific operations"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(Chore, db)
    
    async def get_by_assignee(
        self, 
        assignee_id: int, 
        include_disabled: bool = False
    ) -> List[Chore]:
        """Get all chores for a specific assignee"""
        query = select(Chore).where(Chore.assignee_id == assignee_id)
        
        if not include_disabled:
            query = query.where(Chore.is_disabled == False)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_pending_approvals(self, parent_id: int) -> List[Chore]:
        """Get chores pending approval for a parent"""
        query = select(Chore).join(User).where(
            and_(
                User.parent_id == parent_id,
                Chore.status == ChoreStatus.PENDING
            )
        )
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_overdue_chores(self) -> List[Chore]:
        """Get all overdue chores"""
        query = select(Chore).where(
            and_(
                Chore.due_date < datetime.utcnow(),
                Chore.status == ChoreStatus.CREATED
            )
        )
        result = await self.db.execute(query)
        return result.scalars().all()
```

### Using Repository in Services

```python
class ChoreService:
    def __init__(self, chore_repo: ChoreRepository, user_repo: UserRepository):
        self.chore_repo = chore_repo
        self.user_repo = user_repo
    
    async def create_chore(
        self, 
        chore_data: ChoreCreate, 
        creator_id: int
    ) -> Chore:
        # Business logic validation
        assignee = await self.user_repo.get(chore_data.assignee_id)
        if not assignee:
            raise ValueError("Assignee not found")
        
        creator = await self.user_repo.get(creator_id)
        if assignee.parent_id != creator_id:
            raise ValueError("Can only assign chores to your children")
        
        # Use repository to create
        return await self.chore_repo.create(
            **chore_data.dict(),
            created_by_id=creator_id
        )
    
    async def get_family_chores(self, parent_id: int) -> List[Chore]:
        # Get all children
        children = await self.user_repo.get_children(parent_id)
        
        # Get chores for all family members
        all_chores = []
        for child in children:
            chores = await self.chore_repo.get_by_assignee(child.id)
            all_chores.extend(chores)
        
        return all_chores
```

### Benefits of Repository Pattern

1. **Abstraction**: Business logic doesn't need to know about database details
2. **Testability**: Easy to mock repositories for unit testing
3. **Flexibility**: Can switch data sources without changing business logic
4. **Consistency**: Standardized way to access data across the application
5. **Separation of Concerns**: Database queries separated from business rules

## Package Managers

Different ecosystems have different package managers. Here's a comparison:

### pip (Python)

```bash
# Traditional Python package manager
# Install a package
pip install fastapi

# Install from requirements file
pip install -r requirements.txt

# Install in editable mode (for development)
pip install -e .

# Create requirements file
pip freeze > requirements.txt

# Characteristics:
# - Standard Python package manager
# - Resolves dependencies sequentially
# - Can have dependency conflicts
# - Widely supported
```

### uv (Python)

```bash
# New, fast Python package manager written in Rust
# Install uv
pip install uv

# Install packages (10-100x faster than pip)
uv pip install fastapi

# Create virtual environment
uv venv

# Sync dependencies
uv pip sync requirements.txt

# Characteristics:
# - Extremely fast (written in Rust)
# - Drop-in replacement for pip
# - Better dependency resolution
# - Built-in virtual environment management
```

### npx (Node.js)

```bash
# Node Package Execute - runs packages without installing
# Run a package once
npx create-react-app my-app

# Run a specific version
npx node@14 index.js

# Run from local node_modules
npx eslint src/

# Characteristics:
# - Executes packages without global installation
# - Always uses latest version (unless specified)
# - Part of npm (Node Package Manager)
# - Great for one-time tool usage
```

### Comparison

```python
# Example: Setting up a formatter

# Python with pip
pip install black
black myfile.py

# Python with uv (faster)
uv pip install black
black myfile.py

# Node.js with npx (no installation)
npx prettier --write myfile.js

# Key Differences:
# 1. Speed: uv > pip for Python packages
# 2. Philosophy: npx emphasizes running without installing
# 3. Ecosystem: pip/uv for Python, npx for Node.js
# 4. Use cases:
#    - pip: Standard Python development
#    - uv: When you need speed and better resolution
#    - npx: Running Node tools without polluting global/local env
```

### Modern Python Project Setup

```bash
# Using uv for speed
uv venv
source .venv/bin/activate  # On Unix
# or
.venv\Scripts\activate  # On Windows

# Install dependencies
uv pip install -r requirements.txt

# Development dependencies
uv pip install -r requirements-dev.txt

# Lock dependencies (coming in future uv versions)
# uv lock
```

## Summary

These concepts work together in modern Python web development:

1. **Type Hints** provide static typing information
2. **Pydantic** uses type hints for runtime validation
3. **Decorators** enhance functions with additional behavior
4. **Async/Await** enables concurrent request handling
5. **Dependency Injection** manages component dependencies cleanly
6. **CORS** enables secure cross-origin requests
7. **Repository Pattern** abstracts data access
8. **Package Managers** handle project dependencies

Together, they create a robust, type-safe, and maintainable web application architecture.