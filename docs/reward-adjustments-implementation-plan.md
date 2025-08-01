# Reward Adjustments Feature - Implementation Plan

**Feature Branch**: `feature/reward-adjustments`  
**Created**: 2025-08-01  
**Last Updated**: 2025-08-01  
**Current Status**: Planning Phase  
**Overall Progress**: 0% (0/49 tasks)

## Overview

### Feature Description
Implement a reward adjustment system that allows parent users to make manual adjustments (additions or deductions) to their children's total reward balance. This MVP implementation focuses on simplicity without complex features like history UI or auditing.

### Business Requirements
- Parents can add bonus rewards or apply deductions to child balances
- Adjustments are separate from chore rewards to maintain system integrity
- Each adjustment requires a reason for accountability
- Children see updated balance but not individual adjustment details
- No editing/deleting adjustments in MVP (immutable records)

### Technical Approach
Following the LEVER framework:
- **Leverage**: Extend existing repository/service patterns
- **Extend**: Build on current balance calculation logic
- **Verify**: Ensure parent-child relationships are validated
- **Eliminate**: No duplicate balance tracking mechanisms
- **Reduce**: Simple UI integration into existing allowance summary

## Phased Implementation

### Phase 1: Database & Model Layer (0/11 tasks)
Foundation for storing reward adjustments with proper relationships and constraints.

#### Subphase 1.1: Database Migration (0/4 tasks)
⬜ Create Alembic migration file for reward_adjustments table  
⬜ Define table schema with proper indexes and foreign keys  
⬜ Add migration rollback logic  
⬜ Test migration up/down locally  

**Technical Specifications**:
```sql
CREATE TABLE reward_adjustments (
    id INT PRIMARY KEY AUTO_INCREMENT,
    child_id INT NOT NULL,
    parent_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    reason VARCHAR(500) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (child_id) REFERENCES users(id),
    FOREIGN KEY (parent_id) REFERENCES users(id),
    INDEX idx_child_adjustments (child_id),
    INDEX idx_parent_adjustments (parent_id)
);
```

#### Subphase 1.2: SQLAlchemy Model (0/4 tasks)
⬜ Create `backend/app/models/reward_adjustment.py`  
⬜ Implement RewardAdjustment model with proper type annotations  
⬜ Add model to `backend/app/models/__init__.py`  
⬜ Verify model relationships with User model  

**Model Structure**:
```python
class RewardAdjustment(Base):
    __tablename__ = "reward_adjustments"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    child_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    parent_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    child: Mapped["User"] = relationship("User", foreign_keys=[child_id])
    parent: Mapped["User"] = relationship("User", foreign_keys=[parent_id])
```

#### Subphase 1.3: Pydantic Schemas (0/3 tasks)
⬜ Create `backend/app/schemas/reward_adjustment.py`  
⬜ Implement RewardAdjustmentCreate and RewardAdjustmentResponse schemas  
⬜ Add proper validation for amount range and reason length  

### Phase 2: Repository & Service Layer (0/12 tasks)
Business logic and data access patterns following existing architecture.

#### Subphase 2.1: Repository Implementation (0/4 tasks)
⬜ Create `backend/app/repositories/reward_adjustment_repository.py`  
⬜ Extend BaseRepository with adjustment-specific methods  
⬜ Implement `get_by_child_id` method for filtered queries  
⬜ Add `calculate_total_adjustments` aggregation method  

#### Subphase 2.2: Service Layer (0/5 tasks)
⬜ Create `backend/app/services/reward_adjustment_service.py`  
⬜ Implement `create_adjustment` with parent-child validation  
⬜ Add `get_child_adjustments` with permission checks  
⬜ Create service dependency injection setup  
⬜ Add service to dependency providers  

#### Subphase 2.3: Balance Calculation Update (0/3 tasks)
⬜ Update UserService to include adjustments in balance calculation  
⬜ Modify `get_children_allowance_summary` method  
⬜ Test balance calculations with adjustments  

**Updated Balance Formula**:
```python
total_adjustments = await self.adjustment_repo.calculate_total_adjustments(db, child_id)
balance_due = total_earned + total_adjustments - paid_out
```

### Phase 3: API Layer (0/9 tasks)
RESTful endpoints for creating and retrieving adjustments.

#### Subphase 3.1: JSON API Endpoints (0/5 tasks)
⬜ Create `backend/app/api/v1/adjustments.py` router  
⬜ Implement POST `/api/v1/adjustments/` endpoint  
⬜ Implement GET `/api/v1/adjustments/child/{child_id}` endpoint  
⬜ Add proper OpenAPI documentation  
⬜ Register router in main API module  

#### Subphase 3.2: Error Handling & Validation (0/4 tasks)
⬜ Add comprehensive error responses (400, 403, 404)  
⬜ Implement rate limiting decorators  
⬜ Add request validation middleware  
⬜ Test error scenarios  

### Phase 4: Frontend Integration (0/10 tasks)
UI updates for creating adjustments and displaying updated balances.

#### Subphase 4.1: HTML Templates (0/3 tasks)
⬜ Create `backend/app/templates/adjustments/form.html`  
⬜ Design inline/modal adjustment form with HTMX  
⬜ Add form validation and error display  

#### Subphase 4.2: Allowance Summary Integration (0/4 tasks)
⬜ Update allowance summary template to show adjustments  
⬜ Add "Adjust Balance" button for each child  
⬜ Implement HTMX dynamic form loading  
⬜ Update balance display format  

**Balance Display Format**:
```html
<div class="balance-breakdown">
    <span>Chore Earnings: ${{ chore_total }}</span>
    <span>Adjustments: ${{ adjustment_total }}</span>
    <hr>
    <strong>Total Balance: ${{ total_balance }}</strong>
</div>
```

#### Subphase 4.3: HTML API Endpoints (0/3 tasks)
⬜ Add adjustment form endpoint to `html.py`  
⬜ Implement POST handler for form submission  
⬜ Add success/error response handling  

### Phase 5: Testing & Validation (0/7 tasks)
Comprehensive testing to ensure reliability and correctness.

#### Subphase 5.1: Unit Tests (0/4 tasks)
⬜ Write tests for RewardAdjustmentService  
⬜ Test parent-child validation logic  
⬜ Test balance calculation with adjustments  
⬜ Test edge cases (negative amounts, boundaries)  

#### Subphase 5.2: Integration Tests (0/3 tasks)
⬜ Test API endpoint authentication and authorization  
⬜ Test end-to-end adjustment creation flow  
⬜ Test concurrent adjustment handling  

## Testing Integration

### Test Commands
```bash
# Run specific test file
docker compose exec api python -m pytest backend/tests/services/test_reward_adjustment_service.py

# Run with coverage
docker compose exec api python -m pytest --cov=backend/app/services/reward_adjustment_service

# Run integration tests
docker compose exec api python -m pytest backend/tests/api/v1/test_adjustments.py
```

### Test Scenarios
1. **Authorization Tests**
   - Parent can create adjustments for own children
   - Parent cannot adjust other parents' children
   - Children cannot create adjustments

2. **Validation Tests**
   - Amount within range (-999.99 to 999.99)
   - Reason required and length validated
   - Child must exist and belong to parent

3. **Balance Calculation Tests**
   - Positive adjustments increase balance
   - Negative adjustments decrease balance
   - Multiple adjustments sum correctly

## Technical Notes

### Validation Rules
- **Amount**: DECIMAL(10,2), range -999.99 to 999.99
- **Reason**: VARCHAR(500), minimum 3 characters
- **Relationships**: Validated via foreign keys and service logic

### Error Handling
- 400: Invalid adjustment data or business rule violation
- 403: Parent attempting to adjust non-owned child
- 404: Child or referenced entity not found
- 422: Validation error in request data

### Security Considerations
- JWT authentication required for all endpoints
- Role-based access (parents only)
- Parent-child relationship validation
- No cross-family data access

### API Examples

**Create Adjustment**:
```bash
curl -X POST http://localhost:8000/api/v1/adjustments/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "child_id": 2,
    "amount": 5.00,
    "reason": "Bonus for extra help with groceries"
  }'
```

**Get Child Adjustments**:
```bash
curl http://localhost:8000/api/v1/adjustments/child/2 \
  -H "Authorization: Bearer $TOKEN"
```

## Progress Tracking

### Phase Completion
- [ ] Phase 1: Database & Model Layer (0%)
- [ ] Phase 2: Repository & Service Layer (0%)
- [ ] Phase 3: API Layer (0%)
- [ ] Phase 4: Frontend Integration (0%)
- [ ] Phase 5: Testing & Validation (0%)

### Rollback Procedures
1. **Database Rollback**: `alembic downgrade -1`
2. **Code Rollback**: `git checkout main -- <affected files>`
3. **Branch Reset**: `git reset --hard origin/main`

### Dependencies
- Phase 2 requires Phase 1 completion
- Phase 3 requires Phase 2 completion
- Phase 4 can start after Phase 3 API design
- Phase 5 can run in parallel with development

### Future Enhancements (Post-MVP)
1. Adjustment history UI with pagination
2. Edit/delete capabilities with audit trail
3. Adjustment categories and types
4. Approval workflow for large adjustments
5. Export functionality for record keeping
6. Bulk adjustment operations

---

**Note**: This plan follows the chores-tracker architecture patterns and is designed for incremental implementation with clear checkpoints for progress tracking.