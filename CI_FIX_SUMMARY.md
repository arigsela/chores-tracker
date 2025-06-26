# CI Test Fix Summary

## Issues Fixed

### 1. Rate Limiting Decorator Errors
**File**: `backend/app/api/api_v1/endpoints/chores.py`
- Added missing `request: Request` parameter to `update_chore` and `delete_chore` functions
- These parameters are required by the `@limit_update` and `@limit_delete` decorators

### 2. Test Error Response Handling  
**File**: `backend/tests/api/v1/test_range_reward_edge_cases.py`
- Fixed handling of validation error responses that can be either strings or lists
- Added proper type checking and conversion to handle both formats

### 3. Unit of Work Test Database Connection
**File**: `backend/tests/test_unit_of_work_service_methods.py`
- Added `test_uow_factory` fixture that returns a lambda function providing the test session
- Updated all test methods to accept and use the `test_uow_factory` parameter
- Fixed async/sync mismatch - UnitOfWork expects a synchronous factory function
- Added missing `description` field in test data

## Code Changes

### 1. Rate Limiting Fix
```python
# Before
async def update_chore(
    chore_id: int = Path(...),
    ...
):

# After  
async def update_chore(
    request: Request,
    chore_id: int = Path(...),
    ...
):
```

### 2. Error Response Handling
```python
# Added type checking for error responses
error_detail = response.json()["detail"]

if isinstance(error_detail, list):
    error_messages = [str(err).lower() for err in error_detail]
    error_message = " ".join(error_messages)
else:
    error_message = error_detail.lower()
```

### 3. UnitOfWork Test Factory
```python
# Added fixture
@pytest.fixture
def test_uow_factory(db_session):
    """Create a factory for UnitOfWork that uses the test session."""
    return lambda: db_session

# Updated all UnitOfWork usage
async with UnitOfWork(session_factory=test_uow_factory) as uow:
    # ... test code
```

## Additional Fix - DetachedInstanceError

### Issue
`test_bulk_assign_chores_rollback_on_error` was failing with:
```
sqlalchemy.orm.exc.DetachedInstanceError: Instance <User at 0x...> is not bound to a Session
```

### Solution
- Store entity IDs before the UnitOfWork context closes
- Re-fetch entities from the database when needed after the context
- This prevents accessing detached SQLAlchemy instances

```python
# Store IDs before potential session closure
parent_id = parent.id
child_id = child.id

# Later, re-fetch if needed
parent = await user_service.get(db_session, id=parent_id)
```

## Result
All failing tests are now fixed:
- ✅ test_approve_range_reward_with_negative_value
- ✅ test_bulk_assign_chores_success  
- ✅ test_approve_chore_with_next_instance
- ✅ test_approve_range_chore_with_next_instance
- ✅ test_approve_non_recurring_chore
- ✅ test_bulk_assign_validation_error
- ✅ test_bulk_assign_chores_rollback_on_error