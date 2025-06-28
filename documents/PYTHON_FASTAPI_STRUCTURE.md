# Python & FastAPI Code Structure Guide

## Table of Contents
1. [Introduction to Python/FastAPI](#introduction-to-pythonfastapi)
2. [Project Structure Overview](#project-structure-overview)
3. [Core Python Concepts](#core-python-concepts)
4. [FastAPI Fundamentals](#fastapi-fundamentals)
5. [Dependency Injection in FastAPI](#dependency-injection-in-fastapi)
6. [Async Programming](#async-programming)
7. [Middleware Pattern](#middleware-pattern)
8. [Request-Response Flow](#request-response-flow)
9. [Real Examples from Your Code](#real-examples-from-your-code)

## Introduction to Python/FastAPI

FastAPI is a modern Python web framework that's similar to Spring Boot in Java but with some key differences:

- **Type hints everywhere**: Python 3.6+ type annotations provide IDE support and runtime validation
- **Async by default**: Like Spring WebFlux, not traditional Spring MVC
- **Automatic API documentation**: OpenAPI (Swagger) generated automatically
- **Dependency injection**: Function-based, not field-based like Spring's `@Autowired`

## Project Structure Overview

Your backend follows a clean architecture pattern:

```
backend/
├── app/                        # Main application package
│   ├── main.py                # Entry point (like Application.java in Spring Boot)
│   ├── api/                   # API layer (Controllers)
│   ├── core/                  # Core utilities (Config, Security)
│   ├── db/                    # Database configuration
│   ├── dependencies/          # Dependency injection setup
│   ├── middleware/            # Cross-cutting concerns (like Spring interceptors)
│   ├── models/                # Domain entities (like JPA entities)
│   ├── repositories/          # Data access layer (like Spring Data repos)
│   ├── schemas/               # DTOs (Data Transfer Objects)
│   └── services/              # Business logic layer (like @Service)
```

## Core Python Concepts

### 1. **Decorators** (Similar to Java Annotations)

In Python, decorators modify function behavior. They're like Java annotations but more powerful:

```python
# From your main.py
@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request, db: AsyncSession = Depends(get_db)):
    """Render the index page."""
    return templates.TemplateResponse("pages/index.html", {"request": request})
```

This is equivalent to Java's:
```java
@GetMapping("/")
@ResponseBody
public String readIndex(@RequestParam Request request, @Autowired Database db) {
    return templateEngine.render("pages/index.html", context);
}
```

### 2. **Type Hints**

Python type hints provide IDE support and runtime validation:

```python
# From your models/user.py
class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    username: Mapped[str] = mapped_column(String(100), unique=True)
    is_parent: Mapped[bool] = mapped_column(Boolean, default=False)
```

- `Mapped[int]` = strongly typed integer column
- `Optional[str]` = nullable string (like `String | null` in Java)

### 3. **Async/Await**

Python's async is similar to Java's CompletableFuture but cleaner:

```python
# From your repositories/base.py
async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
    query = select(self.model).where(self.model.id == id)
    result = await db.execute(query)
    return result.scalars().first()
```

## FastAPI Fundamentals

### 1. **Application Instance**

```python
# From your main.py
app = FastAPI(
    title=settings.APP_NAME,
    description="A comprehensive API for managing household chores...",
    version="1.0.0",
    docs_url="/docs",      # Swagger UI endpoint
    redoc_url="/redoc"     # ReDoc UI endpoint
)
```

### 2. **Route Decorators**

FastAPI uses decorators to define routes:

```python
@app.get("/path")          # HTTP GET
@app.post("/path")         # HTTP POST
@app.put("/path")          # HTTP PUT
@app.delete("/path")       # HTTP DELETE
```

### 3. **Path Parameters**

```python
# From your main.py
@app.get("/pages/{page}", response_class=HTMLResponse)
async def read_page(request: Request, page: str, db: AsyncSession = Depends(get_db)):
    # 'page' is automatically extracted from the URL
    path = f"pages/{page}.html"
    return templates.TemplateResponse(path, {"request": request})
```

### 4. **Request Body with Pydantic Models**

```python
# From your schemas/user.py
class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str = Field(..., min_length=4)
    parent_id: Optional[int] = None

# Used in endpoint
@app.post("/users/", response_model=UserResponse)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    # 'user' is automatically validated and parsed from JSON
    return await user_service.create(db, obj_in=user.dict())
```

## Dependency Injection in FastAPI

FastAPI's DI is function-based, unlike Spring's field injection:

### 1. **Basic Dependency**

```python
# From your db/base.py
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Usage in endpoint
async def some_endpoint(db: AsyncSession = Depends(get_db)):
    # 'db' is injected automatically
```

### 2. **Authentication Dependency**

```python
# From your dependencies/auth.py
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get the current authenticated user."""
    user_id = verify_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user = await user_repo.get(db, id=int(user_id))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user
```

### 3. **Chained Dependencies**

Your code shows dependency chaining:

```python
# OAuth2 scheme extracts token from Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")

# get_current_user depends on oauth2_scheme and get_db
# Endpoints depend on get_current_user
@app.get("/protected")
async def protected_route(current_user: User = Depends(get_current_user)):
    return {"user": current_user.username}
```

## Async Programming

### 1. **Async Functions**

All I/O operations in your code are async:

```python
# From your services/base.py
async def create(self, db: AsyncSession, *, obj_in: dict) -> ModelType:
    return await self.repository.create(db, obj_in=obj_in)
```

### 2. **Async Context Managers**

```python
# From your core/unit_of_work.py
class UnitOfWork:
    async def __aenter__(self):
        self._session = AsyncSessionLocal()
        return self
    
    async def __aexit__(self, *args):
        await self.rollback()
        await self._session.close()
```

Usage:
```python
async with UnitOfWork() as uow:
    # Do work
    await uow.commit()
```

## Middleware Pattern

Middleware in FastAPI processes requests before/after route handlers:

```python
# From your middleware/rate_limit.py
@app.middleware("http")
async def my_middleware(request: Request, call_next):
    # Before route handler
    start_time = time.time()
    
    response = await call_next(request)  # Call route handler
    
    # After route handler
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

Your rate limiting middleware:
```python
# Decorator pattern for rate limiting
limit_login = limiter.limit("5 per minute")
limit_register = limiter.limit("3 per minute")

# Applied to endpoints
@router.post("/login")
@limit_login
async def login(request: Request, ...):
    # Rate limited to 5 requests per minute
```

## Request-Response Flow

Let's trace a typical request through your application:

### 1. **HTTP Request Arrives**
```
POST /api/v1/chores/
Authorization: Bearer <token>
Content-Type: application/json
{"title": "Clean room", "assignee_id": 2}
```

### 2. **Middleware Processing**
- CORS middleware checks origin
- Rate limiter checks request count
- Request continues if allowed

### 3. **Route Matching**
FastAPI matches the route in `api/api_v1/endpoints/chores.py`:
```python
@router.post("/", response_model=ChoreResponse)
@limit_create
async def create_chore(
    request: Request,
    chore: ChoreCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
```

### 4. **Dependency Resolution**
FastAPI resolves dependencies in order:
1. `get_db()` → creates database session
2. `oauth2_scheme` → extracts token from header
3. `get_current_user(token, db)` → validates token, fetches user
4. `ChoreCreate` → validates request body

### 5. **Business Logic**
```python
# Service layer handles business rules
chore = await chore_service.create(
    db, 
    obj_in=chore.dict(), 
    creator_id=current_user.id
)
```

### 6. **Repository Layer**
```python
# Repository creates database record
async def create(self, db: AsyncSession, *, obj_in: Dict) -> Chore:
    db_obj = self.model(**obj_in)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj
```

### 7. **Response Serialization**
- Pydantic model validates response
- FastAPI converts to JSON
- Response sent to client

## Real Examples from Your Code

### Example 1: Complex Endpoint with Multiple Dependencies

```python
# From your main.py - HTML endpoint for chore approval
@app.post("/api/v1/chores/{chore_id}/approve", response_class=HTMLResponse)
async def approve_chore_html(
    request: Request,
    chore_id: int,                                    # Path parameter
    db: AsyncSession = Depends(get_db),               # Database dependency
    current_user: models.User = Depends(get_current_user)  # Auth dependency
):
    # Extract reward value from multiple sources
    reward_value = None
    
    # Try query parameters first
    query_params = dict(request.query_params)
    if "reward_value" in query_params:
        reward_value = float(query_params["reward_value"])
    
    # Try form data
    if reward_value is None:
        form_data = await request.form()
        if "reward_value" in form_data:
            reward_value = float(form_data["reward_value"])
    
    # Business logic validation
    chore = await chore_repo.get(db, id=chore_id)
    if not chore:
        raise HTTPException(status_code=404, detail="Chore not found")
    
    if not current_user.is_parent or chore.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only creator can approve")
    
    # Update and return HTML
    updated_chore = await chore_repo.approve_chore(db, chore_id, reward_value)
    return templates.TemplateResponse(
        "components/chore_item.html", 
        {"request": request, "chore": updated_chore}
    )
```

### Example 2: Service Layer Pattern

```python
# From your services/chore_service.py
class ChoreService(BaseService[Chore, ChoreRepository]):
    async def bulk_assign_chores(
        self, db: AsyncSession, *, 
        chore_ids: List[int], 
        assignee_id: int
    ) -> List[Chore]:
        """Assign multiple chores in a single transaction."""
        async with UnitOfWork() as uow:
            chores = []
            for chore_id in chore_ids:
                # Validate each chore exists
                chore = await self.repository.get(uow.session, id=chore_id)
                if not chore:
                    raise ChoreNotFoundError(f"Chore {chore_id} not found")
                
                # Update assignment
                updated = await self.repository.update(
                    uow.session,
                    id=chore_id,
                    obj_in={"assignee_id": assignee_id}
                )
                chores.append(updated)
            
            # Commit all changes together
            await uow.commit()
            return chores
```

### Example 3: Repository with Eager Loading

```python
# From your repositories/chore.py
class ChoreRepository(BaseRepository[Chore]):
    async def get_by_assignee(
        self, db: AsyncSession, *, assignee_id: int
    ) -> List[Chore]:
        """Get all chores for a specific assignee with relations."""
        query = (
            select(self.model)
            .where(self.model.assignee_id == assignee_id)
            .options(
                joinedload(self.model.assignee),  # Eager load user
                joinedload(self.model.creator)    # Eager load creator
            )
        )
        result = await db.execute(query)
        return result.scalars().unique().all()
```

## Key Differences from Java/Spring

1. **No Compilation**: Python is interpreted, errors show at runtime
2. **Duck Typing**: If it walks like a duck... (but we use type hints)
3. **Global Interpreter Lock (GIL)**: Single thread for Python code, but async I/O is truly concurrent
4. **Package Management**: `pip` and `requirements.txt` instead of Maven/Gradle
5. **No Interfaces**: Python uses protocols and abstract base classes
6. **Function-Based DI**: Dependencies are functions, not classes/fields

## Best Practices in Your Code

1. **Type Hints Everywhere**: Improves IDE support and catches errors
2. **Async Throughout**: All I/O operations are async
3. **Dependency Injection**: Clean separation of concerns
4. **Repository Pattern**: Abstracts database access
5. **Service Layer**: Business logic separated from API layer
6. **Pydantic Validation**: Automatic request/response validation
7. **Error Handling**: Proper HTTP exceptions with status codes

## Common Patterns

### Dependency Injection Chain
```
oauth2_scheme → token
    ↓
get_current_user → user
    ↓
endpoint → business logic
```

### Layered Architecture
```
API Endpoint
    ↓
Service Layer (business logic)
    ↓
Repository Layer (data access)
    ↓
Database
```

### Request Validation Flow
```
Raw Request → Pydantic Model → Validated Data → Business Logic
```

This architecture provides a clean, maintainable structure that should feel familiar coming from Java/Spring, while leveraging Python's strengths.