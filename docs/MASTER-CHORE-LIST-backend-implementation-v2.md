# Master Chore List - Backend Implementation Plan v2

## Overview

This document outlines the backend implementation for the Master Chore List feature with two key enhancements:
1. **Selective Visibility**: Hide specific chores from certain children
2. **Grayed Out Completed Chores**: Show completed chores as unavailable until reset based on recurrence

## Phased Implementation Plan

### Phase 1: Database Foundation (2 days)

#### Subphase 1.1: Schema Design & Migration Scripts (0.5 day)
**Tasks:**
- [ ] Design chore_visibility table schema
- [ ] Design recurrence fields for chores table
- [ ] Write Alembic migration script
- [ ] Add necessary indexes

**Testing:**
- [ ] Test migration up/down locally
- [ ] Verify indexes are created correctly
- [ ] Test foreign key constraints
- [ ] Verify default values

**Deliverables:**
- Migration file: `xxx_add_visibility_and_recurrence.py`
- Schema documentation

#### Subphase 1.2: SQLAlchemy Models (0.5 day)
**Tasks:**
- [ ] Create ChoreVisibility model
- [ ] Update Chore model with recurrence fields
- [ ] Add relationships between models
- [ ] Update User model relationships

**Testing:**
- [ ] Unit test model creation
- [ ] Test relationship loading
- [ ] Verify cascade operations
- [ ] Test model constraints

**Code:**
```python
# backend/app/models/chore_visibility.py
from sqlalchemy import Column, Integer, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from ..db.base_class import Base

class ChoreVisibility(Base):
    __tablename__ = "chore_visibility"
    
    id = Column(Integer, primary_key=True, index=True)
    chore_id = Column(Integer, ForeignKey("chores.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    is_hidden = Column(Boolean, default=False)
    
    # Relationships
    chore = relationship("Chore", back_populates="visibility_settings")
    user = relationship("User", back_populates="hidden_chores")
    
    __table_args__ = (
        UniqueConstraint('chore_id', 'user_id', name='unique_chore_user'),
    )
```

**Test File:**
```python
# backend/tests/models/test_chore_visibility.py
async def test_create_visibility_record():
    """Test creating a visibility record"""
    
async def test_unique_constraint():
    """Test that duplicate chore-user pairs are prevented"""
    
async def test_cascade_delete():
    """Test that visibility records are deleted when chore is deleted"""
```

#### Subphase 1.3: Pydantic Schemas (0.5 day)
**Tasks:**
- [ ] Create ChoreVisibility schemas
- [ ] Update Chore schemas with recurrence fields
- [ ] Create ChoreListResponse schema
- [ ] Add validation rules

**Testing:**
- [ ] Test schema validation
- [ ] Test serialization/deserialization
- [ ] Test optional field handling
- [ ] Test validation error messages

**Code:**
```python
# backend/app/schemas/chore_visibility.py
from pydantic import BaseModel, ConfigDict, Field
from typing import List

class ChoreVisibilityBulkUpdate(BaseModel):
    chore_id: int
    hidden_from_users: List[int] = Field(default_factory=list)
    visible_to_users: List[int] = Field(default_factory=list)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "chore_id": 1,
                "hidden_from_users": [2, 3],
                "visible_to_users": [4]
            }
        }
    )
```

#### Subphase 1.4: Database Migration Execution & Verification (0.5 day)
**Tasks:**
- [ ] Run migration on test database
- [ ] Verify all tables and columns created
- [ ] Test rollback procedure
- [ ] Document any issues

**Testing:**
- [ ] Integration test with test data
- [ ] Performance test with large datasets
- [ ] Test migration with existing data
- [ ] Verify no data loss

### Phase 2: Service Layer Implementation (2 days)

#### Subphase 2.1: ChoreVisibilityService (0.5 day)
**Tasks:**
- [ ] Implement update_chore_visibility method
- [ ] Implement get_hidden_chore_ids_for_user method
- [ ] Add bulk operations support
- [ ] Add error handling

**Testing:**
- [ ] Unit test each method
- [ ] Test bulk updates
- [ ] Test error scenarios
- [ ] Test concurrent updates

**Test Cases:**
```python
# backend/tests/services/test_chore_visibility_service.py
class TestChoreVisibilityService:
    async def test_update_single_user_visibility(self):
        """Test hiding chore from one user"""
        
    async def test_update_multiple_users_visibility(self):
        """Test hiding chore from multiple users"""
        
    async def test_make_visible_after_hidden(self):
        """Test changing visibility from hidden to visible"""
        
    async def test_get_hidden_chores_empty_list(self):
        """Test when user has no hidden chores"""
```

#### Subphase 2.2: Recurrence Calculation Engine (0.75 day)
**Tasks:**
- [ ] Implement _calculate_reset_time method
- [ ] Handle daily recurrence
- [ ] Handle weekly recurrence
- [ ] Handle monthly recurrence with edge cases
- [ ] Add timezone support

**Testing:**
- [ ] Test daily recurrence calculations
- [ ] Test weekly recurrence (each day)
- [ ] Test monthly edge cases (31st, Feb 29)
- [ ] Test timezone transitions
- [ ] Test DST handling

**Test Cases:**
```python
# backend/tests/services/test_recurrence_engine.py
class TestRecurrenceEngine:
    @pytest.mark.parametrize("completion_time,expected_reset", [
        ("2024-01-15 14:30:00", "2024-01-16 00:00:00"),  # Daily
        ("2024-01-15 23:59:00", "2024-01-16 00:00:00"),  # Daily at end of day
    ])
    async def test_daily_recurrence(self, completion_time, expected_reset):
        """Test daily recurrence calculations"""
        
    async def test_monthly_31st_handling(self):
        """Test monthly recurrence on 31st for months with fewer days"""
        
    async def test_leap_year_february_29(self):
        """Test monthly recurrence for Feb 29 in non-leap years"""
```

#### Subphase 2.3: Enhanced ChoreService (0.75 day)
**Tasks:**
- [ ] Update get_pool_chores with visibility filtering
- [ ] Implement availability checking
- [ ] Add progress calculation
- [ ] Update complete_chore with recurrence
- [ ] Add authorization checks

**Testing:**
- [ ] Test visibility filtering
- [ ] Test availability logic
- [ ] Test progress calculations
- [ ] Test authorization
- [ ] Integration tests

**Test Cases:**
```python
# backend/tests/services/test_chore_service_v2.py
class TestChoreServiceV2:
    async def test_get_pool_chores_filters_hidden(self):
        """Test that hidden chores are excluded from pool"""
        
    async def test_complete_chore_sets_next_available(self):
        """Test that completing recurring chore sets next available time"""
        
    async def test_cannot_complete_unavailable_chore(self):
        """Test that unavailable chores cannot be completed"""
        
    async def test_progress_calculation_accuracy(self):
        """Test that progress percentage is calculated correctly"""
```

### Phase 3: API Layer Implementation (1.5 days)

#### Subphase 3.1: Visibility Management Endpoints (0.5 day)
**Tasks:**
- [ ] Implement PUT /chores/{id}/visibility
- [ ] Implement GET /chores/{id}/visibility
- [ ] Add authorization middleware
- [ ] Add request validation

**Testing:**
- [ ] Test successful visibility updates
- [ ] Test authorization (parent-only)
- [ ] Test invalid requests
- [ ] Test error responses

**API Tests:**
```python
# backend/tests/api/v2/test_visibility_endpoints.py
async def test_update_visibility_as_parent():
    """Test parent can update visibility"""
    
async def test_update_visibility_as_child_forbidden():
    """Test child cannot update visibility"""
    
async def test_get_visibility_returns_current_settings():
    """Test retrieving current visibility settings"""
```

#### Subphase 3.2: Enhanced Chore List Endpoints (0.5 day)
**Tasks:**
- [ ] Update GET /chores/pool endpoint
- [ ] Add visibility filtering
- [ ] Include availability status
- [ ] Add progress information

**Testing:**
- [ ] Test filtered responses
- [ ] Test available/completed separation
- [ ] Test progress data
- [ ] Test performance

#### Subphase 3.3: HTMX HTML Endpoints (0.5 day)
**Tasks:**
- [ ] Create pool HTML endpoint
- [ ] Add visibility indicators
- [ ] Include countdown timers
- [ ] Add progress bars

**Testing:**
- [ ] Test HTML generation
- [ ] Test template rendering
- [ ] Test dynamic updates
- [ ] Test browser compatibility

### Phase 4: Integration & Performance (1 day)

#### Subphase 4.1: End-to-End Integration Tests (0.5 day)
**Tasks:**
- [ ] Write complete workflow tests
- [ ] Test parent creates chore with visibility
- [ ] Test child sees filtered list
- [ ] Test chore completion and reset

**Testing:**
```python
# backend/tests/integration/test_visibility_workflow.py
async def test_complete_visibility_workflow():
    """Test complete workflow from creation to completion"""
    # 1. Parent creates chore hidden from child1
    # 2. Verify child1 cannot see it
    # 3. Verify child2 can see and claim it
    # 4. Complete chore and verify reset time
    # 5. Verify grayed out state
```

#### Subphase 4.2: Performance Testing & Optimization (0.5 day)
**Tasks:**
- [ ] Load test visibility queries
- [ ] Optimize database queries
- [ ] Add query result caching
- [ ] Profile recurrence calculations

**Performance Tests:**
```python
# backend/tests/performance/test_visibility_performance.py
async def test_visibility_query_performance():
    """Test query performance with many visibility rules"""
    # Create 1000 chores with various visibility settings
    # Measure query time
    # Assert < 100ms
```

## Database Schema

### 1. New Table: `chore_visibility`
```sql
CREATE TABLE chore_visibility (
    id INT PRIMARY KEY AUTO_INCREMENT,
    chore_id INT NOT NULL,
    user_id INT NOT NULL,
    is_hidden BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (chore_id) REFERENCES chores(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_chore_user (chore_id, user_id),
    INDEX idx_user_hidden (user_id, is_hidden)
);
```

### 2. Updates to `chores` table
```sql
ALTER TABLE chores 
ADD COLUMN last_completion_time TIMESTAMP NULL,
ADD COLUMN next_available_time TIMESTAMP NULL,
ADD COLUMN recurrence_type ENUM('none', 'daily', 'weekly', 'monthly') DEFAULT 'none',
ADD COLUMN recurrence_value INT DEFAULT NULL,
ADD INDEX idx_next_available (next_available_time),
ADD INDEX idx_recurrence (recurrence_type, next_available_time);
```

## Testing Strategy

### Unit Testing Guidelines
- Each service method must have at least 3 test cases
- Test happy path, error cases, and edge cases
- Use pytest fixtures for test data
- Mock external dependencies

### Integration Testing Guidelines
- Test complete workflows
- Use test database with rollback
- Test API endpoints with different user roles
- Verify response formats

### Performance Testing Guidelines
- Test with realistic data volumes (1000+ chores)
- Measure query execution time
- Profile memory usage
- Test concurrent operations

## Success Metrics

### Phase 1 Success Criteria
- [ ] All migrations run without errors
- [ ] Models pass all unit tests
- [ ] Schemas validate correctly
- [ ] 100% test coverage for new code

### Phase 2 Success Criteria
- [ ] All service methods implemented
- [ ] Visibility filtering works correctly
- [ ] Recurrence calculations accurate
- [ ] All edge cases handled

### Phase 3 Success Criteria
- [ ] All endpoints return correct data
- [ ] Authorization working properly
- [ ] HTML templates render correctly
- [ ] API documentation updated

### Phase 4 Success Criteria
- [ ] All integration tests pass
- [ ] Query performance < 100ms
- [ ] No memory leaks
- [ ] Load tests pass with 100 concurrent users

## Risk Mitigation

### Technical Risks
1. **Complex Queries**: Mitigate with proper indexes and query optimization
2. **Race Conditions**: Use database transactions and row locking
3. **Timezone Issues**: Store all times in UTC, convert for display

### Testing Risks
1. **Incomplete Coverage**: Enforce minimum 80% coverage
2. **Missing Edge Cases**: Regular code reviews
3. **Performance Regression**: Automated performance tests in CI

## Documentation Requirements

### For Each Phase
- [ ] Update API documentation
- [ ] Add code comments
- [ ] Update README
- [ ] Create migration guide

### Developer Documentation
- [ ] Service method documentation
- [ ] Schema documentation
- [ ] Migration procedures
- [ ] Troubleshooting guide

## Timeline Summary

- **Phase 1**: 2 days (Database Foundation)
- **Phase 2**: 2 days (Service Layer)
- **Phase 3**: 1.5 days (API Layer)
- **Phase 4**: 1 day (Integration & Performance)
- **Total**: 6.5 days

## Dependencies

### External Dependencies
- SQLAlchemy 2.0+
- Pydantic v2
- pytest-asyncio
- Alembic

### Internal Dependencies
- Existing User model
- Existing Chore model
- Authentication system
- Database connection pool