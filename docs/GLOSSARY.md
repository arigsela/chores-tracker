# Chores Tracker Glossary

**Purpose**: Canonical definitions of domain terms and technical concepts used throughout the Chores Tracker application.

**Last Updated**: January 23, 2026

---

## Table of Contents

- [Domain Concepts](#domain-concepts)
  - [Users and Roles](#users-and-roles)
  - [Chores and Assignments](#chores-and-assignments)
  - [Assignment Modes](#assignment-modes)
  - [Rewards](#rewards)
  - [Families](#families)
- [Technical Terms](#technical-terms)
  - [Architecture](#architecture)
  - [Database](#database)
  - [API](#api)
- [System States](#system-states)
- [Quick Reference](#quick-reference)

---

## Domain Concepts

### Users and Roles

#### Parent
**Definition**: A user account with elevated privileges to manage chores, children, and family settings.

**Capabilities**:
- Create and manage child accounts
- Create, edit, and delete chores
- Approve or reject completed chore assignments
- Apply reward adjustments (bonuses/penalties)
- View family-wide statistics and activity
- Manage family invite codes

**Database Field**: `is_parent = true` in the `users` table

**Example**:
```python
# Parent registration
POST /api/v1/users/register
{
  "username": "mom",
  "email": "mom@example.com",
  "password": "securepass",
  "is_parent": true
}
```

**See Also**: [Child](#child), [User Hierarchy](#user-hierarchy)

---

#### Child
**Definition**: A dependent user account associated with a parent, with limited permissions focused on completing chores and viewing rewards.

**Capabilities**:
- View assigned chores and available pool chores
- Mark chores as complete
- View their current balance
- View their activity history
- Claim unassigned pool chores

**Restrictions**:
- Cannot create or modify chores
- Cannot approve their own completions
- Cannot modify other users
- Cannot access family management

**Database Field**: `is_parent = false` and `parent_id = <parent_user_id>` in the `users` table

**Example**:
```python
# Child registration (by parent)
POST /api/v1/users/
{
  "username": "alice",
  "password": "simple",
  "is_parent": false,
  "parent_id": 1  # Parent's user ID
}
```

**See Also**: [Parent](#parent), [Balance](#balance)

---

#### User Hierarchy
**Definition**: The parent-child relationship structure where one parent can have multiple children.

**Rules**:
- Each child has exactly one parent (enforced by `parent_id` foreign key)
- Parents can have zero or more children
- Children cannot have children (no nested hierarchies)
- All users belong to exactly one family

**Database Relationships**:
```python
# User model
parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
children: Mapped[List["User"]] = relationship(back_populates="parent")
parent: Mapped[Optional["User"]] = relationship(back_populates="children")
```

**See Also**: [Family](#family)

---

### Chores and Assignments

#### Chore
**Definition**: A task created by a parent that can be assigned to one or more children for completion.

**Core Attributes**:
- `title`: Short name (e.g., "Take out trash")
- `description`: Optional detailed instructions
- `reward`: Monetary value for completion
- `assignment_mode`: How the chore is assigned (single, multi_independent, unassigned)
- `is_recurring`: Whether the chore repeats
- `cooldown_days`: Days before recurring chore becomes available again
- `creator_id`: Parent who created the chore
- `family_id`: Family the chore belongs to

**Lifecycle**:
```
Created → Assigned → Completed → Approved → (Recurring: Cooldown → Available)
                              ↓
                           Rejected → Available Again
```

**Example**:
```python
# Create a chore
POST /api/v1/chores/
{
  "title": "Clean the kitchen",
  "description": "Wipe counters, sweep floor, load dishwasher",
  "reward": 5.00,
  "assignment_mode": "single",
  "assignee_ids": [2],  # Child user ID
  "is_recurring": true,
  "cooldown_days": 1  # Daily chore
}
```

**See Also**: [Assignment](#assignment), [Assignment Modes](#assignment-modes), [Recurring Chore](#recurring-chore)

---

#### Assignment
**Definition**: A link between a chore and a specific child, representing that child's responsibility to complete the chore. Implemented as a `ChoreAssignment` database record.

**Purpose**: Enables the multi-assignment system where a single chore can be assigned to multiple children independently.

**Core Attributes**:
- `chore_id`: Reference to the chore
- `assignee_id`: Reference to the assigned child
- `is_completed`: Whether the child marked it complete
- `is_approved`: Whether the parent approved completion
- `completion_date`: When the child completed it
- `approval_date`: When the parent approved it
- `approval_reward`: Final reward amount (for range rewards)
- `rejection_reason`: Parent's explanation if rejected

**States**:
1. **Pending**: Created but not completed (`is_completed = false`)
2. **Completed**: Child marked complete (`is_completed = true, is_approved = false`)
3. **Approved**: Parent approved (`is_approved = true`)
4. **Rejected**: Parent rejected (no specific flag, but `rejection_reason` is set)

**Database Table**: `chore_assignments` (junction table for many-to-many relationship)

**Example**:
```sql
-- ChoreAssignment record
INSERT INTO chore_assignments (chore_id, assignee_id, is_completed, is_approved)
VALUES (1, 2, false, false);  -- Chore 1 assigned to Child 2
```

**See Also**: [Chore](#chore), [Assignee](#assignee), [Assignment Modes](#assignment-modes)

---

#### Assignee
**Definition**: A child user to whom a chore has been assigned. Synonymous with "assigned child."

**Usage Context**:
- "This chore has 3 assignees" = 3 children have assignments for this chore
- "assignee_ids" in API requests = list of child user IDs to create assignments for

**Database Field**: `assignee_id` in the `chore_assignments` table (foreign key to `users.id`)

**See Also**: [Assignment](#assignment), [Child](#child)

---

### Assignment Modes

The assignment mode determines how a chore is distributed to children. This is a core architectural concept that enables flexible chore management.

#### Single Assignment Mode
**Value**: `assignment_mode = 'single'`

**Definition**: Traditional one-child-one-chore assignment. Exactly one child is assigned to the chore.

**Behavior**:
- Requires exactly 1 assignee_id when creating the chore
- Creates 1 ChoreAssignment record
- Only the assigned child sees the chore
- Child completes → parent approves → child's balance increases
- For recurring chores: assignment resets after cooldown period

**Use Cases**:
- Specific tasks for specific children (e.g., "Alice: clean your bathroom")
- Rotating responsibilities (manually reassign after completion)
- Tasks requiring specific skills/age

**Example**:
```python
POST /api/v1/chores/
{
  "title": "Mow the lawn",
  "reward": 15.00,
  "assignment_mode": "single",
  "assignee_ids": [2]  # Only Alice (user_id=2)
}
```

**See Also**: [Multi-Independent Mode](#multi-independent-mode), [Unassigned Pool Mode](#unassigned-pool-mode)

---

#### Multi-Independent Mode
**Value**: `assignment_mode = 'multi_independent'`

**Definition**: Personal chores where each child does their own version independently. Multiple children are assigned, and each completes the chore separately.

**Behavior**:
- Requires 1 or more assignee_ids when creating
- Creates N ChoreAssignment records (one per assignee)
- Each child sees the chore in their list
- Each child completes independently
- Parent approves each completion separately
- Each child's balance increases independently
- For recurring: each assignment resets independently after cooldown

**Use Cases**:
- Personal responsibilities (e.g., "Clean your room")
- Hygiene tasks (e.g., "Brush your teeth")
- Individual practice (e.g., "30 minutes reading")

**Example**:
```python
POST /api/v1/chores/
{
  "title": "Clean your room",
  "reward": 5.00,
  "is_recurring": true,
  "cooldown_days": 7,  # Weekly
  "assignment_mode": "multi_independent",
  "assignee_ids": [2, 3, 4]  # Alice, Bob, Charlie
}
# Creates 3 independent assignments
```

**Key Difference from Single Mode**:
- Single: One child does the chore once
- Multi-Independent: Multiple children each do the chore separately

**See Also**: [Single Assignment Mode](#single-assignment-mode), [Unassigned Pool Mode](#unassigned-pool-mode)

---

#### Unassigned Pool Mode
**Value**: `assignment_mode = 'unassigned'`

**Definition**: Shared household chores available to any child on a first-come-first-served basis. No initial assignments are created.

**Behavior**:
- Requires 0 assignee_ids when creating (empty array)
- Creates 0 ChoreAssignment records initially
- All children in the family see the chore in "Available Pool"
- First child to complete "claims" the chore (creates assignment)
- Other children no longer see it after it's claimed
- Parent approves → child's balance increases
- For recurring: assignment deleted after cooldown, returns to pool

**Use Cases**:
- Shared household tasks (e.g., "Take out trash", "Walk the dog")
- Flexible responsibilities
- Encouraging initiative and fairness
- Tasks that only need to be done once per cycle

**Example**:
```python
POST /api/v1/chores/
{
  "title": "Walk the dog",
  "reward": 3.00,
  "is_recurring": true,
  "cooldown_days": 1,  # Daily
  "assignment_mode": "unassigned",
  "assignee_ids": []  # No initial assignees
}

# When child completes:
POST /api/v1/chores/5/complete
# Creates ChoreAssignment(chore_id=5, assignee_id=current_child)
```

**Claiming Logic**:
```
Unassigned Chore (visible to all children)
    ↓
First Child Clicks "Complete"
    ↓
Assignment Created (child "claims" the chore)
    ↓
Removed from other children's available pool
    ↓
Parent approves → Child earns reward
    ↓
(If recurring) After cooldown → Assignment deleted → Returns to pool
```

**See Also**: [Single Assignment Mode](#single-assignment-mode), [Multi-Independent Mode](#multi-independent-mode)

---

### Rewards

#### Fixed Reward
**Definition**: A chore with a predetermined, unchanging reward amount set at creation.

**Behavior**:
- `is_range_reward = false`
- `reward` field contains the fixed amount
- `min_reward` and `max_reward` are null
- Upon approval, `approval_reward = reward` (copied automatically)

**Use Case**: Standard chores with consistent value (e.g., "Take out trash" always earns $2)

**Example**:
```python
POST /api/v1/chores/
{
  "title": "Set the table",
  "reward": 2.50,
  "is_range_reward": false,  # Fixed reward
  # min_reward and max_reward not specified
}
```

**See Also**: [Range Reward](#range-reward)

---

#### Range Reward
**Definition**: A chore with a flexible reward where the parent determines the final amount within a specified range upon approval.

**Behavior**:
- `is_range_reward = true`
- `reward` field contains suggested/default amount
- `min_reward` and `max_reward` define the allowable range
- Parent must provide `approval_reward` value when approving
- Validation enforces: `min_reward ≤ approval_reward ≤ max_reward`

**Use Cases**:
- Quality-based tasks (e.g., "Help with homework" - quality varies)
- Effort-based tasks (e.g., "Yard work" - scope varies)
- Bonus opportunities (e.g., "Extra credit chores")

**Example**:
```python
# Create range reward chore
POST /api/v1/chores/
{
  "title": "Help with homework",
  "reward": 5.00,  # Suggested amount
  "is_range_reward": true,
  "min_reward": 3.00,
  "max_reward": 10.00
}

# Parent approves with custom amount
POST /api/v1/assignments/7/approve
{
  "reward_value": 7.50  # Must be between 3.00 and 10.00
}
```

**Validation**:
- Creation: Requires `min_reward < max_reward`
- Approval: Requires `min_reward ≤ reward_value ≤ max_reward`
- Error if parent provides value outside range

**See Also**: [Fixed Reward](#fixed-reward), [Approval Reward](#approval-reward)

---

#### Approval Reward
**Definition**: The final reward amount credited to a child's balance upon parent approval of a completed assignment.

**Source**:
- Fixed rewards: Automatically set to `chore.reward`
- Range rewards: Set by parent at approval time

**Database Field**: `approval_reward` in the `chore_assignments` table

**Usage**:
```python
# Assignment after approval
{
  "chore_id": 5,
  "assignee_id": 2,
  "is_completed": true,
  "is_approved": true,
  "approval_reward": 7.50,  # This amount is added to child's balance
  "approval_date": "2026-01-15T10:30:00Z"
}
```

**See Also**: [Balance](#balance), [Range Reward](#range-reward)

---

#### Balance
**Definition**: The cumulative amount a child has earned from approved chore completions and reward adjustments, minus any payouts.

**Calculation**:
```python
balance = sum(approved_assignments.approval_reward)
        + sum(adjustments.amount)
        - sum(payouts.amount)  # Currently 0 (payouts not implemented)
```

**Components**:
1. **Chore earnings**: Sum of `approval_reward` from all approved assignments
2. **Adjustments**: Manual bonuses (positive) or penalties (negative) from parents
3. **Payouts**: (Future feature) Money actually given to child (currently not implemented)

**Current Balance (No Payouts)**:
```python
balance = sum(approved_assignments.approval_reward) + sum(adjustments.amount)
```

**API Endpoint**:
```python
GET /api/v1/users/me/balance
# Returns: {"balance": 45.50}
```

**Display**: Shown prominently on child's dashboard

**See Also**: [Reward Adjustment](#reward-adjustment), [Approval Reward](#approval-reward)

---

#### Reward Adjustment
**Definition**: A manual balance change applied by a parent outside the normal chore completion workflow, typically for bonuses or penalties.

**Purpose**:
- Award bonuses for exceptional behavior
- Apply penalties for rule violations
- Correct balance errors
- Recognize achievements outside chore system

**Attributes**:
- `child_id`: Child receiving the adjustment
- `parent_id`: Parent making the adjustment
- `amount`: Dollar amount (positive for bonus, negative for penalty)
- `reason`: Required text explanation
- `created_at`: Timestamp

**Example**:
```python
POST /api/v1/adjustments/
{
  "child_id": 2,
  "amount": 5.00,  # Bonus
  "reason": "Helped sibling with homework without being asked"
}

POST /api/v1/adjustments/
{
  "child_id": 3,
  "amount": -3.00,  # Penalty
  "reason": "Broke house rule: didn't clean up after snack"
}
```

**Database Table**: `reward_adjustments`

**See Also**: [Balance](#balance)

---

### Families

#### Family
**Definition**: A group of users (parents and children) who share chores, assignments, and activity within an isolated workspace.

**Purpose**:
- Enable multi-family deployments (multiple families on one instance)
- Provide data isolation between families
- Support invite-based family joining

**Attributes**:
- `name`: Optional family name (e.g., "The Smiths")
- `invite_code`: Unique 8-character code for inviting new parents
- `invite_code_expires_at`: Optional expiration for invite code
- `created_by_id`: Parent who created the family

**Family Isolation Rules**:
- Users only see chores from their family
- Parents can only manage children in their family
- Activity feeds are family-scoped
- Statistics are family-scoped

**Example**:
```python
# Create family
POST /api/v1/families/
{
  "name": "The Smiths"
}
# Returns: {"id": 1, "invite_code": "ABC123XY"}

# Join family via invite code
POST /api/v1/families/join
{
  "invite_code": "ABC123XY"
}
```

**See Also**: [Invite Code](#invite-code)

---

#### Invite Code
**Definition**: A unique 8-character alphanumeric code used to invite additional parents to join an existing family.

**Generation**: Automatically created when a family is created (random, unique)

**Usage Flow**:
1. Parent A creates family → receives invite code
2. Parent A shares invite code with Parent B
3. Parent B registers and uses invite code to join family
4. Both parents now share the same family workspace

**Expiration**: Optional (future feature via `invite_code_expires_at`)

**Database Fields**:
- `families.invite_code`: The code itself (indexed, unique)
- `families.invite_code_expires_at`: Optional expiration timestamp

**Example**:
```python
# Family with invite code
{
  "id": 1,
  "name": "The Johnsons",
  "invite_code": "XY7K92PQ",
  "created_at": "2026-01-01T00:00:00Z"
}
```

**See Also**: [Family](#family)

---

#### Recurring Chore
**Definition**: A chore that becomes available again after a cooldown period following approval, allowing it to be completed repeatedly.

**Behavior**:
- `is_recurring = true`
- `cooldown_days` defines the recurrence interval
- Cooldown starts at `approval_date` (when parent approves)
- Assignment becomes available again when: `current_date ≥ approval_date + cooldown_days`

**Cooldown Behavior by Assignment Mode**:

**Single Mode**:
```
Approved (Jan 1) → Cooldown (7 days) → Available Again (Jan 8)
Same assignment record reused, is_completed/is_approved reset
```

**Multi-Independent Mode**:
```
Child A: Approved (Jan 1) → Cooldown (7 days) → Available for Child A (Jan 8)
Child B: Approved (Jan 3) → Cooldown (7 days) → Available for Child B (Jan 10)
Each assignment has independent cooldown
```

**Unassigned Pool Mode**:
```
Approved (Jan 1) → Cooldown (7 days) → Assignment Deleted (Jan 8) → Returns to Pool
Pool chore becomes visible to all children again
```

**Common Cooldown Values**:
- `cooldown_days = 1`: Daily chores
- `cooldown_days = 7`: Weekly chores
- `cooldown_days = 30`: Monthly chores

**Example**:
```python
POST /api/v1/chores/
{
  "title": "Take out trash",
  "reward": 2.00,
  "is_recurring": true,
  "cooldown_days": 1,  # Daily recurrence
  "assignment_mode": "unassigned"
}
```

**See Also**: [Chore](#chore), [Cooldown](#cooldown)

---

#### Cooldown
**Definition**: The waiting period after a recurring chore is approved before it becomes available for completion again.

**Trigger**: Parent approves assignment → `approval_date` set → cooldown starts

**Duration**: Specified by `chore.cooldown_days` field

**Availability Check**:
```python
# Assignment is available if:
if not assignment.is_completed:
    if chore.is_recurring and assignment.approval_date:
        cooldown_end = assignment.approval_date + timedelta(days=chore.cooldown_days)
        return datetime.utcnow() >= cooldown_end
    return True
return False
```

**Example Timeline**:
```
Jan 1 10:00 AM - Child completes chore
Jan 1 11:00 AM - Parent approves (approval_date set)
Jan 1-7        - Cooldown period (cooldown_days = 7)
Jan 8 11:00 AM - Chore becomes available again
```

**See Also**: [Recurring Chore](#recurring-chore)

---

## Technical Terms

### Architecture

#### Service Layer
**Definition**: The business logic tier that sits between API endpoints and the data access layer (repositories).

**Location**: `backend/app/services/`

**Responsibilities**:
- Implement business rules and validation
- Orchestrate multi-repository operations
- Handle complex workflows
- Enforce permissions and access control

**Example Services**:
- `UserService`: User registration, authentication, password reset
- `ChoreService`: Chore creation, assignment logic, completion rules
- `ChoreAssignmentService`: Approval/rejection, cooldown enforcement
- `FamilyService`: Family creation, invite code management

**Pattern**:
```python
class ChoreService:
    def __init__(self, repository: ChoreRepository):
        self.repository = repository

    async def create_chore(self, db: AsyncSession, creator_id: int, chore_data: dict):
        # Business logic validation
        if not await self.user_is_parent(creator_id):
            raise PermissionError("Only parents can create chores")

        # Call repository for data access
        chore = await self.repository.create(db, obj_in=chore_data)

        # Create assignments based on assignment_mode
        await self.create_assignments(db, chore, chore_data.assignee_ids)

        return chore
```

**See Also**: [Repository Layer](#repository-layer), [API Endpoints](#api-endpoints)

---

#### Repository Layer
**Definition**: The data access tier that abstracts database operations and provides a consistent interface for querying and persisting data.

**Location**: `backend/app/repositories/`

**Responsibilities**:
- CRUD operations (Create, Read, Update, Delete)
- Query construction and execution
- Eager loading of relationships
- Database-specific logic

**Example Repositories**:
- `UserRepository`: User queries, authentication helpers
- `ChoreRepository`: Chore queries, availability filtering
- `ChoreAssignmentRepository`: Assignment CRUD, cooldown logic

**Pattern**:
```python
class ChoreRepository(BaseRepository[Chore]):
    async def get_available_for_child(
        self,
        db: AsyncSession,
        child_id: int
    ) -> List[Chore]:
        # Database query logic
        query = select(Chore).join(ChoreAssignment).where(
            ChoreAssignment.assignee_id == child_id,
            ChoreAssignment.is_completed == False
        )
        result = await db.execute(query)
        return result.scalars().all()
```

**See Also**: [Service Layer](#service-layer), [Unit of Work](#unit-of-work)

---

#### Unit of Work
**Definition**: A transaction management pattern that coordinates multiple repository operations to maintain data consistency.

**Location**: `backend/app/core/unit_of_work.py`

**Purpose**:
- Group multiple database operations into atomic transactions
- Ensure all-or-nothing semantics (commit all or rollback all)
- Manage database session lifecycle

**Usage**:
```python
async with UnitOfWork() as uow:
    # Multiple operations in same transaction
    user = await uow.users.create(db=uow.session, obj_in=user_data)
    chore = await uow.chores.create(db=uow.session, obj_in=chore_data)

    # All operations committed together
    await uow.commit()

    # On exception, automatic rollback
```

**See Also**: [Repository Layer](#repository-layer)

---

#### API Endpoints
**Definition**: HTTP route handlers that receive client requests, delegate to services, and return JSON responses.

**Location**: `backend/app/api/api_v1/endpoints/`

**Versioning**: All endpoints prefixed with `/api/v1/`

**Structure**:
```python
@router.post("/chores/", status_code=201)
async def create_chore(
    chore_data: ChoreCreate,  # Request validation (Pydantic)
    current_user: User = Depends(get_current_user),  # Authentication
    chore_service: ChoreService = Depends(get_chore_service),  # DI
    db: AsyncSession = Depends(get_db)  # Database session
):
    # Delegate to service layer
    chore = await chore_service.create_chore(db, current_user.id, chore_data)

    # Return response (Pydantic)
    return ChoreResponse.from_orm(chore)
```

**See Also**: [Service Layer](#service-layer), [Pydantic Schemas](#pydantic-schemas)

---

#### Pydantic Schemas
**Definition**: Data validation and serialization models that define the structure of API requests and responses.

**Location**: `backend/app/schemas/`

**Types**:
- **Base schemas**: Common fields shared across variants
- **Create schemas**: For POST requests (input validation)
- **Update schemas**: For PUT/PATCH requests
- **Response schemas**: For API responses (serialization)

**Example**:
```python
class ChoreBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    reward: float = Field(..., gt=0)

class ChoreCreate(ChoreBase):
    assignment_mode: str = Field(..., pattern="^(single|multi_independent|unassigned)$")
    assignee_ids: List[int] = []

class ChoreResponse(ChoreBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    creator_id: int
    created_at: datetime
```

**See Also**: [API Endpoints](#api-endpoints)

---

### Database

#### SQLAlchemy Model
**Definition**: Python class representing a database table using SQLAlchemy ORM declarative syntax.

**Location**: `backend/app/models/`

**Modern Syntax (SQLAlchemy 2.0)**:
```python
from sqlalchemy.orm import Mapped, mapped_column

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True)
    is_parent: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    children: Mapped[List["User"]] = relationship(back_populates="parent")
```

**See Also**: [Database Migration](#database-migration)

---

#### Database Migration
**Definition**: A versioned script that applies schema changes to the database in a controlled, reversible manner.

**Tool**: Alembic (SQLAlchemy migration tool)

**Location**: `backend/alembic/versions/`

**Workflow**:
```bash
# 1. Modify SQLAlchemy models
# 2. Auto-generate migration
alembic revision --autogenerate -m "add cooldown_days to chores"

# 3. Review generated migration
# 4. Apply migration
alembic upgrade head

# 5. Rollback if needed
alembic downgrade -1
```

**See Also**: [Operations: Database Migrations](/Users/arisela/git/chores-tracker/docs/operations/database-migrations.md)

---

#### Junction Table
**Definition**: A database table that implements a many-to-many relationship between two other tables by storing foreign keys to both.

**Example**: `chore_assignments` table

**Purpose**: Links chores to children, enabling the multi-assignment system

**Structure**:
```sql
CREATE TABLE chore_assignments (
    id INT PRIMARY KEY,
    chore_id INT REFERENCES chores(id),    -- FK to chores
    assignee_id INT REFERENCES users(id),   -- FK to users
    is_completed BOOLEAN,
    is_approved BOOLEAN,
    -- Additional tracking fields
    UNIQUE (chore_id, assignee_id)  -- One assignment per chore-child pair
);
```

**See Also**: [Assignment](#assignment), [Chore](#chore)

---

### API

#### JWT (JSON Web Token)
**Definition**: A self-contained authentication token encoding user identity and claims, used for stateless API authentication.

**Structure**:
```json
{
  "sub": "123",  // Subject (user ID)
  "exp": 1706961600  // Expiration timestamp
}
```

**Usage Flow**:
```
1. POST /api/v1/users/login → Returns JWT
2. Store JWT (AsyncStorage/localStorage)
3. Include in requests: Authorization: Bearer <token>
4. Backend validates token and extracts user_id
```

**Expiration**: 8 days (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)

**See Also**: [JWT Auth Explainer](/Users/arisela/git/chores-tracker/docs/api/JWT_AUTH_EXPLAINER.md)

---

#### CORS (Cross-Origin Resource Sharing)
**Definition**: HTTP security mechanism allowing the backend (port 8000) to accept requests from the frontend (port 8081).

**Configuration**: `backend/app/main.py`

**Allowed Origins**:
```python
BACKEND_CORS_ORIGINS = ["http://localhost:8081"]  # Frontend dev server
```

**See Also**: [Backend Architecture](/Users/arisela/git/chores-tracker/docs/architecture/BACKEND_ARCHITECTURE.md)

---

#### Rate Limiting
**Definition**: Request throttling mechanism to prevent abuse and ensure fair API usage.

**Implementation**: SlowAPI middleware

**Limits** (examples):
- Login: 5 requests per minute
- Registration: 3 requests per minute
- General API: 100 requests per minute
- Chore creation: 30 requests per minute

**Response**: HTTP 429 (Too Many Requests) when limit exceeded

**See Also**: [Backend Architecture](/Users/arisela/git/chores-tracker/docs/architecture/BACKEND_ARCHITECTURE.md)

---

## System States

### Assignment States

An assignment can be in one of these states:

| State | is_completed | is_approved | rejection_reason | Description |
|-------|--------------|-------------|------------------|-------------|
| **Pending** | `false` | `false` | `null` | Assigned but not completed |
| **Completed** | `true` | `false` | `null` | Child marked complete, awaiting approval |
| **Approved** | `true` | `true` | `null` | Parent approved, reward credited |
| **Rejected** | `true` | `false` | `"reason"` | Parent rejected, not credited |

**State Transitions**:
```
Pending → Completed (child clicks "Mark Complete")
Completed → Approved (parent clicks "Approve")
Completed → Rejected (parent clicks "Reject" with reason)
Rejected → Pending (child can retry)
Approved → (cooldown) → Pending (for recurring chores)
```

---

### Chore Availability States

A chore can be available or unavailable for completion:

**Available**:
- Assignment exists for child
- `is_completed = false`
- If recurring and previously approved: `current_time ≥ approval_date + cooldown_days`

**Unavailable**:
- Already completed (`is_completed = true`)
- In cooldown period (recurring chore recently approved)
- No assignment exists (not assigned to this child, or pool chore already claimed)

---

## Quick Reference

### Assignment Modes Comparison

| Feature | Single | Multi-Independent | Unassigned |
|---------|--------|-------------------|------------|
| **Assignees at creation** | Exactly 1 | 1 or more | 0 |
| **Assignments created** | 1 | N (one per child) | 0 initially |
| **Completion** | One child completes | Each child completes independently | First child to complete claims it |
| **Approval** | Parent approves the one assignment | Parent approves each separately | Parent approves the claimed assignment |
| **Recurring behavior** | Assignment resets after cooldown | Each assignment resets independently | Assignment deleted, returns to pool |
| **Use case** | Specific tasks for specific children | Personal responsibilities (each child does their own) | Shared tasks (first-come-first-served) |

---

### Reward Types Comparison

| Feature | Fixed Reward | Range Reward |
|---------|--------------|--------------|
| **is_range_reward** | `false` | `true` |
| **Fields required** | `reward` | `reward`, `min_reward`, `max_reward` |
| **Parent decides amount** | No | Yes (at approval time) |
| **approval_reward** | Automatically set to `reward` | Parent provides value in range |
| **Use case** | Standard chores with consistent value | Quality/effort-based tasks |

---

### API Endpoint Categories

| Category | Prefix | Examples |
|----------|--------|----------|
| **Users** | `/api/v1/users/` | Register, login, profile |
| **Chores** | `/api/v1/chores/` | Create, list, complete |
| **Assignments** | `/api/v1/assignments/` | Approve, reject, list |
| **Families** | `/api/v1/families/` | Create, join, list members |
| **Adjustments** | `/api/v1/adjustments/` | Create bonus/penalty |
| **Activities** | `/api/v1/activities/` | View activity feed |
| **Statistics** | `/api/v1/statistics/` | Family and child stats |
| **Health** | `/api/v1/health/` | Health checks |

---

### Common Field Naming Patterns

| Field Name | Type | Meaning |
|------------|------|---------|
| `*_id` | `int` | Foreign key reference (e.g., `parent_id`, `chore_id`) |
| `is_*` | `bool` | Boolean flag (e.g., `is_completed`, `is_parent`) |
| `*_date` | `datetime` | Timestamp (e.g., `completion_date`, `approval_date`) |
| `*_at` | `datetime` | Alternative timestamp naming (e.g., `created_at`) |
| `*_ids` | `List[int]` | List of IDs (e.g., `assignee_ids`) |

---

## See Also

**Architecture Documentation**:
- [Backend Architecture](/Users/arisela/git/chores-tracker/docs/architecture/BACKEND_ARCHITECTURE.md)
- [Codebase Overview](/Users/arisela/git/chores-tracker/docs/architecture/CODEBASE_OVERVIEW.md)

**Development Guides**:
- [Getting Started](/Users/arisela/git/chores-tracker/docs/development/GETTING_STARTED.md)
- [Python FastAPI Concepts](/Users/arisela/git/chores-tracker/docs/development/PYTHON_FASTAPI_CONCEPTS.md)

**API Documentation**:
- Interactive Docs: http://localhost:8000/docs
- [JWT Auth Explainer](/Users/arisela/git/chores-tracker/docs/api/JWT_AUTH_EXPLAINER.md)

---

**Last Updated**: January 23, 2026
**Maintainers**: Development Team
**Feedback**: Open an issue to suggest additions or corrections to this glossary
