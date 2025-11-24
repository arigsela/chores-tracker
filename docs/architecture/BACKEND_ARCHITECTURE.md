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
- **REST JSON API**: Modern RESTful API design with comprehensive OpenAPI documentation
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
- **pytest**: Testing framework with async support
- **prometheus-fastapi-instrumentator**: Metrics collection and monitoring

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
│   │   ├── chore.py            # Chore model
│   │   ├── chore_assignment.py # ChoreAssignment junction table
│   │   ├── family.py           # Family model
│   │   ├── activity.py         # Activity audit log
│   │   └── reward_adjustment.py # Reward adjustment model
│   ├── repositories/           # Data access layer
│   │   ├── base.py             # Generic repository
│   │   ├── user.py             # User repository
│   │   ├── chore.py            # Chore repository
│   │   ├── chore_assignment.py # ChoreAssignment repository
│   │   ├── family.py           # Family repository
│   │   ├── activity.py         # Activity repository
│   │   └── reward_adjustment.py # Reward adjustment repository
│   ├── schemas/                # Pydantic schemas (DTOs)
│   │   ├── user.py             # User schemas
│   │   ├── chore.py            # Chore schemas
│   │   ├── chore_assignment.py # ChoreAssignment schemas
│   │   ├── family.py           # Family schemas
│   │   ├── activity.py         # Activity schemas
│   │   └── reward_adjustment.py # Reward adjustment schemas
│   ├── services/               # Business logic layer
│   │   ├── base.py             # Base service class
│   │   ├── user_service.py     # User business logic
│   │   ├── chore_service.py    # Chore business logic
│   │   ├── chore_assignment_service.py # Assignment lifecycle
│   │   ├── family_service.py   # Family management
│   │   └── activity_service.py # Activity logging
│   └── scripts/                # Utility scripts
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
- Define root-level routes
- Include API routers
- Set up exception handlers
- Configure Prometheus metrics instrumentation

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

    # User type and hierarchy
    is_parent: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))

    # Family membership
    family_id: Mapped[Optional[int]] = mapped_column(ForeignKey("families.id"))
    registration_code: Mapped[Optional[str]] = mapped_column(String(20), unique=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, onupdate=func.now())

    # Relationships
    children: Mapped[List["User"]] = relationship(
        back_populates="parent",
        foreign_keys=[parent_id],
        remote_side=[id]
    )
    parent: Mapped[Optional["User"]] = relationship(
        back_populates="children",
        foreign_keys=[parent_id],
        remote_side=[id]
    )
    family: Mapped[Optional["Family"]] = relationship(back_populates="members")

    # Chore relationships
    chore_assignments: Mapped[List["ChoreAssignment"]] = relationship(
        back_populates="assignee",
        cascade="all, delete-orphan"
    )
    chores_created: Mapped[List["Chore"]] = relationship(
        back_populates="creator",
        foreign_keys="Chore.creator_id"
    )

    # Activity and adjustment relationships
    activities: Mapped[List["Activity"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
    adjustments_received: Mapped[List["RewardAdjustment"]] = relationship(
        back_populates="child",
        foreign_keys="RewardAdjustment.child_id"
    )
    adjustments_created: Mapped[List["RewardAdjustment"]] = relationship(
        back_populates="parent",
        foreign_keys="RewardAdjustment.parent_id"
    )
```

#### Chore Model
```python
class Chore(Base):
    __tablename__ = "chores"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Assignment mode: 'single', 'multi_independent', 'unassigned'
    assignment_mode: Mapped[str] = mapped_column(String(50), default='single')

    # Reward configuration
    reward: Mapped[float] = mapped_column(Float)
    is_range_reward: Mapped[bool] = mapped_column(Boolean, default=False)
    min_reward: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_reward: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Recurrence settings
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    cooldown_days: Mapped[int] = mapped_column(Integer, default=0)

    # Lifecycle
    is_disabled: Mapped[bool] = mapped_column(Boolean, default=False)

    # Foreign keys
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    family_id: Mapped[Optional[int]] = mapped_column(ForeignKey("families.id"))

    # Relationships
    assignments: Mapped[List["ChoreAssignment"]] = relationship(
        back_populates="chore",
        cascade="all, delete-orphan"
    )
    creator: Mapped["User"] = relationship(back_populates="chores_created")
    family: Mapped[Optional["Family"]] = relationship(back_populates="chores")
```

#### ChoreAssignment Model (Junction Table)
```python
class ChoreAssignment(Base):
    """
    Junction table enabling many-to-many relationship between Chores and Users.
    Powers the multi-assignment system with three modes:
    - single: One child assigned
    - multi_independent: Multiple children, each completes separately
    - unassigned: Pool chore, created when child claims it
    """
    __tablename__ = "chore_assignments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Foreign keys
    chore_id: Mapped[int] = mapped_column(
        ForeignKey("chores.id", ondelete="CASCADE"),
        index=True
    )
    assignee_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True
    )

    # Completion tracking
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    completion_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    approval_date: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Reward tracking
    approval_reward: Mapped[Optional[float]] = mapped_column(Float)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, onupdate=func.now())

    # Relationships
    chore: Mapped["Chore"] = relationship(back_populates="assignments")
    assignee: Mapped["User"] = relationship(back_populates="chore_assignments")

    # Constraints
    __table_args__ = (
        UniqueConstraint('chore_id', 'assignee_id', name='unique_chore_assignee'),
    )

    # Properties for business logic
    @property
    def is_pending_approval(self) -> bool:
        """Assignment completed but not yet approved by parent."""
        return self.is_completed and not self.is_approved

    @property
    def is_available(self) -> bool:
        """
        Check if assignment is available for completion.
        For recurring chores, checks if cooldown period has passed.
        """
        if self.is_completed:
            return False

        if self.chore.is_recurring and self.approval_date:
            cooldown_end = self.approval_date + timedelta(days=self.chore.cooldown_days)
            return datetime.utcnow() >= cooldown_end

        return True
```

#### Family Model
```python
class Family(Base):
    """
    Represents a family unit for multi-family support.
    Enables family isolation and invite-based membership.
    """
    __tablename__ = "families"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(255))

    # Invite system
    invite_code: Mapped[str] = mapped_column(String(8), unique=True, index=True)
    invite_code_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, onupdate=func.now())

    # Relationships
    members: Mapped[List["User"]] = relationship(
        back_populates="family",
        foreign_keys="User.family_id"
    )
    chores: Mapped[List["Chore"]] = relationship(back_populates="family")
```

#### Activity Model
```python
class Activity(Base):
    """
    Audit log for all system actions.
    Provides activity feed and compliance tracking.
    """
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Activity identification
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True
    )
    activity_type: Mapped[str] = mapped_column(String(50), index=True)
    description: Mapped[str] = mapped_column(Text)

    # Optional target (e.g., child affected by parent's action)
    target_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )

    # Flexible JSON storage for activity-specific data
    activity_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime, index=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="activities")
    target_user: Mapped[Optional["User"]] = relationship(foreign_keys=[target_user_id])
```

**Activity Types:**
- `chore_created`, `chore_completed`, `chore_approved`, `chore_rejected`
- `user_registered`, `user_login`, `password_reset`
- `adjustment_created`, `family_created`, `family_joined`

### Model Relationships Overview

The application uses a sophisticated multi-assignment system powered by the ChoreAssignment junction table:

```
User (Parent) ──creates──> Chore ──has many──> ChoreAssignment ──belongs to──> User (Child)
     │                        │                         │
     └─ belongs to ─> Family ─┘                         │
                                                         │
                                              is tracked by──> Activity
```

**Key Relationship Patterns:**

1. **User-Family**: Many-to-one (users belong to one family)
2. **Chore-Family**: Many-to-one (chores belong to one family for isolation)
3. **Chore-User (via ChoreAssignment)**: Many-to-many (enables multi-assignment)
4. **User-Activity**: One-to-many (users generate activities)
5. **User-User**: Self-referential (parent-child hierarchy)

**Assignment Mode Behaviors:**

| Mode | Assignments Created | Completion Behavior | Approval Behavior |
|------|-------------------|---------------------|-------------------|
| `single` | 1 assignment | Child completes their assignment | Parent approves the assignment |
| `multi_independent` | N assignments (one per child) | Each child completes independently | Parent approves each separately |
| `unassigned` | 0 assignments initially | First child to complete creates assignment | Parent approves the claimed assignment |

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

### RESTful JSON API Architecture

The application implements a modern RESTful API design:

#### API Endpoints (`/api/v1/*`)
JSON-based REST endpoints for all operations:
- `/api/v1/users/` - User management and authentication
- `/api/v1/chores/` - Chore CRUD operations
- `/api/v1/assignments/` - Chore assignment management
- `/api/v1/adjustments/` - Reward adjustments
- `/api/v1/families/` - Family management
- `/api/v1/activities/` - Activity logging
- `/api/v1/statistics/` - Statistical endpoints
- `/api/v1/health/` - Health check endpoints
- `/metrics` - Prometheus metrics endpoint

### Request/Response Flow

```
Client Request (JSON)
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
Response (JSON)
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
- **users**: `username` (unique), `email` (unique), `family_id`, `parent_id`
- **chores**: `creator_id`, `family_id`, `is_disabled`, `assignment_mode`
- **chore_assignments**: `chore_id`, `assignee_id`, `is_completed`, `(chore_id, assignee_id)` unique constraint
- **families**: `invite_code` (unique)
- **activities**: `user_id`, `activity_type`, `created_at` (for time-based queries)
- **reward_adjustments**: `child_id`, `parent_id`

Composite indexes for common queries:
- `chore_assignments(chore_id, is_completed, is_approved)` - for pending approval queries
- `chore_assignments(assignee_id, is_completed)` - for child's available chores
- `activities(user_id, created_at)` - for activity feeds

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

#### Chore Workflow (Multi-Assignment System)

**Single Assignment Mode:**
```
Chore Created → ChoreAssignment Created → Child Completes → Parent Approves
                                                                    ↓
                                                          Cooldown (if recurring)
```

**Multi-Independent Mode:**
```
Chore Created → ChoreAssignment 1 (Child A) → Completes → Approves
             ├─ ChoreAssignment 2 (Child B) → Completes → Approves
             └─ ChoreAssignment 3 (Child C) → Completes → Approves
                (Each operates independently with own cooldown)
```

**Unassigned Pool Mode:**
```
Chore Created (no assignments) → First Child Completes (creates assignment)
                                            ↓
                                   Parent Approves → Cooldown → Assignment Deleted
                                                                      ↓
                                                         Returns to pool
```

#### Reward System
1. **Fixed Rewards**:
   - Set `reward` amount on chore creation
   - Applied to `ChoreAssignment.approval_reward` on approval
2. **Range Rewards**:
   - Set `min_reward` and `max_reward` on chore creation
   - Parent supplies `approval_reward` value on approval via ChoreAssignment
   - Validation: `min_reward ≤ approval_reward ≤ max_reward`
3. **Balance Calculation**:
   ```python
   child_balance = sum(approved_assignments.approval_reward)
                 + sum(adjustments.amount)
                 - sum(payouts.amount)  # Future feature
   ```

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
- Health check endpoints: `/api/v1/health/` and `/api/v1/healthcheck`
- Prometheus metrics at `/metrics` endpoint
- Structured logging with correlation IDs
- Business metrics tracking (chores, users, families, activities)
- HTTP metrics (request duration, status codes, sizes)
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

## Frontend Architecture

> **Note**: The backend previously supported server-side HTML rendering with HTMX (deprecated August 2024). The current architecture uses a separate React Native Web frontend application.

### Current Frontend Setup
- **Location**: `frontend/` directory (separate from backend)
- **Technology**: React Native Web with Expo
- **Port**: 8081 (frontend) + 8000 (backend API)
- **Communication**: REST JSON API calls via Axios
- **Authentication**: JWT token stored in AsyncStorage/localStorage
- **State Management**: React Context API

### Mobile Application
- **Location**: `mobile/` directory
- **Technology**: React Native for iOS/Android
- **Code Sharing**: 90% component/logic sharing with web frontend
- **Offline Support**: AsyncStorage for data persistence

## Conclusion

The Chores Tracker backend is a well-architected FastAPI application that demonstrates modern Python web development practices. Its clean separation of concerns, comprehensive testing, and robust security make it suitable for production deployment while remaining maintainable and extensible.

Key strengths:
- Clean, layered architecture
- Type safety with Pydantic
- Async performance
- Comprehensive testing
- RESTful JSON API design
- Strong security practices
- Production-ready monitoring with Prometheus

This architecture provides a solid foundation for scaling and extending the application as requirements evolve.