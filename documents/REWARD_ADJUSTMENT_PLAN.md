# Manual Reward Balance Adjustment Feature

This document outlines the implementation plan for adding the ability to manually adjust reward balances for children in the Chores Tracker application.

## Feature Overview

Currently, the application calculates a child's reward balance based on completed and approved chores. This feature will add the ability for parents to:

1. Manually add reward dollars to a child's balance (positive adjustment)
2. Manually remove reward dollars from a child's balance (negative adjustment)
3. View a history of manual adjustments and payments
4. See the total adjustments reflected in the allowance summary

This feature will be useful when parents need to make corrections or add bonuses outside the normal chore completion workflow.

## Implementation Plan

### 1. Database Changes

Create a new `Payment` model to track both payments and manual adjustments:

```python
class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    amount: Mapped[float] = mapped_column(Float)
    description: Mapped[str] = mapped_column(Text)
    is_adjustment: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    child_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    parent_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # Relationships
    child: Mapped["User"] = relationship("User", foreign_keys=[child_id])
    parent: Mapped["User"] = relationship("User", foreign_keys=[parent_id])
```

Add relationships to the User model:

```python
# Add to User model
payments_received: Mapped[List["Payment"]] = relationship("Payment", back_populates="child", foreign_keys="Payment.child_id")
payments_made: Mapped[List["Payment"]] = relationship("Payment", back_populates="parent", foreign_keys="Payment.parent_id")
```

### 2. API Endpoints

Create new endpoints for payment functionality:

1. `POST /api/v1/payments/record` - Record a payment to a child
2. `POST /api/v1/payments/adjust` - Add or remove reward dollars manually
3. `GET /api/v1/payments/history/{child_id}` - Get payment history for a child
4. `GET /api/v1/payments/balance/{child_id}` - Get current balance for a child

Plus HTML endpoints for UI components:

1. `GET /api/v1/html/payments/adjust-form/{child_id}` - Get HTML form for adjusting balance
2. `GET /api/v1/html/payments/history/{child_id}` - Get HTML for payment history

### 3. UI Components

1. **Balance Adjustment Form** - A form for entering adjustment amount and description
2. **Payment History Component** - A table showing payment and adjustment history
3. **Updated Allowance Summary** - Modified to include adjustments in balance calculation

### 4. Business Logic

1. Only parents can create adjustments
2. Parents can only adjust balances for their own children
3. Adjustments can be positive (adding to balance) or negative (removing from balance)
4. All adjustments require a description explaining the reason
5. Balance is calculated as: `total_earned + total_adjustments - total_paid`

### 5. Mobile App Updates

Update the mobile app to support:

1. Viewing the updated balance including adjustments
2. Making manual balance adjustments
3. Viewing payment and adjustment history

### 6. Testing

1. Test creating positive and negative adjustments
2. Test balance calculations with adjustments
3. Test access control (parent/child permissions)
4. Test UI components and updates

## Implementation Steps

1. Create the Payment model
2. Generate database migration
3. Create schemas for payments and adjustments
4. Implement repository layer
5. Implement service layer
6. Create API endpoints
7. Create HTML templates and components
8. Update existing UI components
9. Add unit tests
10. Test integration

## Completion Criteria

The feature will be considered complete when:

1. Parents can successfully add and remove reward dollars from their children's balances
2. The adjusted balance is correctly reflected in the allowance summary
3. Payment history is visible and accurate
4. All tests pass
5. The feature is properly documented