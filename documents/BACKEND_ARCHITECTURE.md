# Chores Tracker Backend Architecture Documentation

## Table of Contents
1. [Overview](#overview)
2. [Technology Stack](#technology-stack)
3. [Project Structure](#project-structure)
4. [Core Components](#core-components)
5. [API Design](#api-design)
6. [Authentication & Security](#authentication--security)
7. [Database Layer](#database-layer)
8. [Business Logic Layer](#business-logic-layer)
9. [Testing Strategy](#testing-strategy)
10. [Deployment & DevOps](#deployment--devops)

## Overview

The Chores Tracker backend is a modern Python web application built with FastAPI, designed to manage household chores, rewards, and family task assignments. It follows a clean, layered architecture pattern similar to enterprise Java applications but leverages Python's async capabilities for high performance.

### Key Features
- **Dual API Design**: Supports both REST JSON APIs and HTML/HTMX endpoints
- **Role-Based Access**: Parent and child accounts with different permissions
- **Async Architecture**: Full async/await support for optimal performance
- **Clean Architecture**: Separation of concerns with distinct layers

## Technology Stack

### Core Framework
- **FastAPI** (v0.104+): Modern, fast web framework for building APIs
  - Automatic OpenAPI/Swagger documentation
  - Built-in data validation with Pydantic
  - Dependency injection system
  - Async request handling

### Database & ORM
- **SQLAlchemy 2.0**: Modern ORM with async support
  - Declarative mapping with type annotations
  - Connection pooling and optimization
  - Relationship management
- **MySQL 5.7**: Production database
- **SQLite**: Testing database
- **Alembic**: Database migration tool

### Authentication & Security
- **JWT (JSON Web Tokens)**: Stateless authentication
- **bcrypt**: Password hashing
- **OAuth2PasswordBearer**: FastAPI's OAuth2 implementation
- **SlowAPI**: Rate limiting middleware

### Additional Libraries
- **Pydantic v2**: Data validation and serialization
- **Jinja2**: Template engine for HTML rendering
- **HTMX**: For dynamic UI updates (frontend integration)
- **pytest**: Testing framework with async support

## Project Structure

```
backend/
├── alembic.ini                 # Database migration configuration
├── alembic/                    # Migration scripts directory
│   ├── env.py                  # Alembic environment config
│   └── versions/               # Migration version files
├── app/                        # Main application directory
│   ├── __init__.py
│   ├── main.py                 # Application entry point & routes
│   ├── api/                    # API layer
│   │   └── api_v1/
│   │       ├── api.py          # API router aggregation
│   │       └── endpoints/      # API endpoints (controllers)
│   │           ├── users.py    # User management endpoints
│   │           └── chores.py   # Chore management endpoints
│   ├── core/                   # Core utilities and config
│   │   ├── config.py           # Application configuration
│   │   ├── logging.py          # Logging setup
│   │   ├── security/           # Security utilities
│   │   │   ├── jwt.py          # JWT token handling
│   │   │   └── password.py     # Password hashing
│   │   └── unit_of_work.py     # Transaction management
│   ├── db/                     # Database configuration
│   │   ├── base.py             # Database session management
│   │   └── base_class.py       # SQLAlchemy base class
│   ├── dependencies/           # Dependency injection
│   │   ├── auth.py             # Authentication dependencies
│   │   └── services.py         # Service layer dependencies
│   ├── middleware/             # Middleware components
│   │   └── rate_limit.py       # Rate limiting middleware
│   ├── models/                 # Database models (entities)
│   │   ├── user.py             # User model
│   │   └── chore.py            # Chore model
│   ├── repositories/           # Data access layer
│   │   ├── base.py             # Generic repository
│   │   ├── user.py             # User repository
│   │   └── chore.py            # Chore repository
│   ├── schemas/                # Pydantic schemas (DTOs)
│   │   ├── user.py             # User schemas
│   │   └── chore.py            # Chore schemas
│   ├── services/               # Business logic layer
│   │   ├── base.py             # Base service class
│   │   ├── user_service.py     # User business logic
│   │   └── chore_service.py    # Chore business logic
│   ├── scripts/                # Utility scripts
│   ├── static/                 # Static files (JS, CSS)
│   └── templates/              # HTML templates
│       ├── components/         # Reusable HTML components
│       ├── layouts/            # Base layouts
│       └── pages/              # Full page templates
├── tests/                      # Test suite
├── requirements.txt            # Python dependencies
└── pytest.ini                  # Test configuration
```

## Core Components

### 1. Application Entry Point (`main.py`)

The main FastAPI application instance with comprehensive configuration:

```python
app = FastAPI(
    title="Chores Tracker API",
    description="...",
    version="1.0.0",
    docs_url="/docs",        # Swagger UI
    redoc_url="/redoc",      # ReDoc UI
)
```

**Key Responsibilities:**
- Configure middleware (CORS, rate limiting)
- Mount static files and templates
- Define root-level routes
- Include API routers
- Set up exception handlers

### 2. Models Layer (`app/models/`)

Database entities using SQLAlchemy 2.0's modern declarative syntax:

#### User Model
```python
class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_parent: Mapped[bool] = mapped_column(Boolean, default=False)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    
    # Relationships
    children: Mapped[List["User"]] = relationship(...)
    chores_created: Mapped[List["Chore"]] = relationship(...)
```

#### Chore Model
```python
class Chore(Base):
    __tablename__ = "chores"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    reward: Mapped[float] = mapped_column(Float)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    assignee_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
```

### 3. Schemas Layer (`app/schemas/`)

Pydantic models for request/response validation and serialization:

```python
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    is_parent: bool = False

class UserCreate(UserBase):
    password: str = Field(..., min_length=4)
    parent_id: Optional[int] = None

class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    is_active: bool
```

**Schema Types:**
- **Base schemas**: Common fields
- **Create schemas**: For POST requests
- **Update schemas**: For PUT/PATCH requests
- **Response schemas**: For API responses

### 4. Repository Layer (`app/repositories/`)

Data access abstraction using the repository pattern:

```python
class BaseRepository(Generic[ModelType]):
    async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        query = select(self.model).where(self.model.id == id)
        result = await db.execute(query)
        return result.scalars().first()
    
    async def create(self, db: AsyncSession, *, obj_in: Dict) -> ModelType:
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
```

**Repository Features:**
- Generic base repository for CRUD operations
- Async database operations
- Eager loading support
- Custom query methods
- Transaction handling

### 5. Service Layer (`app/services/`)

Business logic implementation:

```python
class ChoreService(BaseService[Chore, ChoreRepository]):
    async def assign_chore(self, db: AsyncSession, *, 
                          chore_id: int, assignee_id: int) -> Chore:
        # Business logic validation
        chore = await self.repository.get(db, id=chore_id)
        if not chore:
            raise ChoreNotFoundError()
        
        # Update assignment
        return await self.repository.update(
            db, id=chore_id, obj_in={"assignee_id": assignee_id}
        )
```

**Service Responsibilities:**
- Business rule validation
- Complex operations orchestration
- Transaction coordination
- Error handling

### 6. API Endpoints (`app/api/api_v1/endpoints/`)

REST API controllers with comprehensive documentation:

```python
@router.post("/register", status_code=201)
@limit_register  # Rate limiting
async def register_user(
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
    user_service: UserService = Depends(get_user_service)
):
    """Register a new user account."""
    # Implementation
```

**Endpoint Features:**
- Automatic OpenAPI documentation
- Request validation
- Rate limiting decorators
- Dependency injection
- Error handling

## API Design

### Dual API Architecture

The application implements two types of APIs:

#### 1. RESTful JSON APIs (`/api/v1/*`)
Traditional REST endpoints returning JSON data:
- `/api/v1/users/` - User management
- `/api/v1/chores/` - Chore CRUD operations
- `/api/v1/auth/` - Authentication endpoints

#### 2. HTML/HTMX APIs (`/api/v1/html/*`)
Server-side rendered HTML fragments for dynamic UI:
- `/api/v1/html/chores/list` - Chore list component
- `/api/v1/html/chores/{id}/approve-form` - Approval modal
- `/api/v1/html/users/children` - Children dropdown

### Request/Response Flow

```
Client Request
    ↓
Middleware (CORS, Rate Limit)
    ↓
Route Handler
    ↓
Dependencies Resolution
    ├── Auth (get_current_user)
    ├── Database (get_db)
    └── Services (get_*_service)
    ↓
Service Layer (Business Logic)
    ↓
Repository Layer (Data Access)
    ↓
Database
    ↓
Response (JSON or HTML)
```

## Authentication & Security

### JWT Authentication

1. **Login Flow**:
   ```
   POST /api/v1/users/login
   → Validate credentials
   → Generate JWT token
   → Return token to client
   ```

2. **Token Structure**:
   ```python
   {
       "sub": "user_id",
       "exp": "expiration_timestamp"
   }
   ```

3. **Protected Routes**:
   ```python
   @app.get("/protected")
   async def protected_route(
       current_user: User = Depends(get_current_user)
   ):
       # User is authenticated
   ```

### Security Features

#### Password Security
- bcrypt hashing with salt rounds
- Minimum password requirements
- Password strength validation

#### Rate Limiting
```python
RATE_LIMIT_RULES = {
    "auth": {
        "login": "5 per minute",
        "register": "3 per minute",
    },
    "api": {
        "default": "100 per minute",
        "create": "30 per minute",
    }
}
```

#### Authorization
- Role-based access (Parent/Child)
- Resource ownership validation
- Hierarchical permissions

## Database Layer

### Connection Management

```python
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,         # Connection pool size
    max_overflow=40,      # Maximum overflow connections
    pool_recycle=3600,    # Recycle connections after 1 hour
    pool_pre_ping=True,   # Test connections before use
)
```

### Transaction Management

The Unit of Work pattern ensures data consistency:

```python
class UnitOfWork:
    async def __aenter__(self):
        self._session = AsyncSessionLocal()
        return self
    
    async def __aexit__(self, *args):
        await self.rollback()
        await self._session.close()
    
    async def commit(self):
        await self._session.commit()
    
    async def rollback(self):
        await self._session.rollback()
```

### Database Migrations

Using Alembic for version control:

```bash
# Generate migration
alembic revision --autogenerate -m "Add user table"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Indexes and Optimization

Key indexes for performance:
- `users.username` (unique)
- `users.email` (unique)
- `chores.assignee_id` (foreign key)
- `chores.creator_id` (foreign key)
- Composite indexes for common queries

## Business Logic Layer

### Core Business Rules

#### User Management
1. **Parent Registration**:
   - Self-registration allowed
   - Email required
   - Strong password (8+ chars)

2. **Child Registration**:
   - Only by authenticated parent
   - Parent ID required
   - Simpler password (4+ chars)

#### Chore Workflow
```
Created → Assigned → Completed → Approved
                          ↓
                     Cooldown (if recurring)
```

#### Reward System
1. **Fixed Rewards**: Set amount on creation
2. **Range Rewards**: Parent sets value on approval
3. **Validation**: Within min/max bounds

### Service Layer Patterns

```python
class ChoreService:
    async def bulk_assign_chores(
        self, db: AsyncSession, *, 
        chore_ids: List[int], 
        assignee_id: int
    ) -> List[Chore]:
        async with UnitOfWork() as uow:
            chores = []
            for chore_id in chore_ids:
                chore = await self.assign_chore(
                    uow.session, 
                    chore_id=chore_id, 
                    assignee_id=assignee_id
                )
                chores.append(chore)
            await uow.commit()
            return chores
```

## Testing Strategy

### Test Structure
```
tests/
├── conftest.py              # Global fixtures
├── api/v1/                  # API endpoint tests
├── test_repositories.py     # Repository tests
├── test_services.py         # Service tests
├── test_unit_of_work.py     # Transaction tests
└── test_middleware.py       # Middleware tests
```

### Test Categories

#### Unit Tests
- Repository methods
- Service business logic
- Utility functions
- Model validations

#### Integration Tests
- API endpoint behavior
- Database operations
- Authentication flow
- Middleware integration

#### Test Fixtures
```python
@pytest.fixture
async def test_db():
    """Create test database session."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSessionLocal() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
```

### Test Coverage
- Current: 43% overall
- Critical paths: >75%
- Total tests: 223
- All passing ✅

## Deployment & DevOps

### Environment Configuration

#### Required Environment Variables
```bash
# Database
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=secret
MYSQL_DATABASE=chores_tracker

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=11520

# Application
APP_NAME="Chores Tracker"
DEBUG=false
TESTING=false
```

### Docker Deployment

#### Dockerfile Structure
```dockerfile
FROM python:3.11-slim

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY . /app
WORKDIR /app

# Run with Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0"]
```

#### Docker Compose
```yaml
services:
  api:
    build: ./backend
    environment:
      - DATABASE_URL=mysql+aiomysql://user:pass@db/chores
    depends_on:
      - db
  
  db:
    image: mysql:5.7
    environment:
      - MYSQL_ROOT_PASSWORD=secret
```

### Production Considerations

#### Application Server
- **Uvicorn**: ASGI server for FastAPI
- **Gunicorn**: Process manager
- Command: `gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker`

#### Performance Optimization
1. **Connection Pooling**: 20 base + 40 overflow
2. **Async Operations**: Non-blocking I/O
3. **Query Optimization**: Eager loading, indexes
4. **Caching**: Redis for session/frequently accessed data

#### Monitoring
- Health check endpoint: `/api/v1/healthcheck`
- Structured logging with correlation IDs
- Metrics collection (response times, error rates)
- Database query performance logging

#### Security Hardening
1. **HTTPS Only**: TLS termination at load balancer
2. **CORS Configuration**: Whitelist allowed origins
3. **Rate Limiting**: Per-IP and per-user limits
4. **Input Validation**: Pydantic schemas
5. **SQL Injection Protection**: Parameterized queries

### Scaling Considerations

#### Horizontal Scaling
- Stateless design (JWT auth)
- Database connection pooling
- Load balancer compatible

#### Vertical Scaling
- Async architecture maximizes resource usage
- Configurable worker processes
- Memory-efficient Python 3.11+

## Common Operations

### Development Workflow

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload

# Run tests
pytest

# Format code
black .
ruff check --fix
```

### Administrative Tasks

```bash
# List all users
python -m app.scripts.list_users

# Reset password
python -m app.scripts.reset_password

# Database maintenance
alembic history
alembic current
```

### Debugging

1. **Enable SQL logging**:
   ```python
   engine = create_async_engine(url, echo=True)
   ```

2. **Request debugging**:
   - Check `/docs` for API testing
   - Use correlation IDs in logs
   - Enable DEBUG mode for detailed errors

## Best Practices

### Code Style
- Type hints for all functions
- Docstrings for public methods
- Async/await consistency
- Error handling with specific exceptions

### Security
- Never log sensitive data
- Validate all inputs
- Use parameterized queries
- Keep dependencies updated

### Performance
- Use database indexes
- Implement pagination
- Leverage async operations
- Monitor query performance

### Maintenance
- Regular dependency updates
- Database backup strategy
- Log rotation
- Monitor disk usage

## Conclusion

The Chores Tracker backend is a well-architected FastAPI application that demonstrates modern Python web development practices. Its clean separation of concerns, comprehensive testing, and robust security make it suitable for production deployment while remaining maintainable and extensible.

Key strengths:
- Clean, layered architecture
- Type safety with Pydantic
- Async performance
- Comprehensive testing
- Dual API design for flexibility
- Strong security practices

This architecture provides a solid foundation for scaling and extending the application as requirements evolve.