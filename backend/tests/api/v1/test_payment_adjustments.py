"""
Tests for payment adjustment endpoints.
"""
import pytest
from httpx import AsyncClient
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.user import User

pytestmark = pytest.mark.asyncio

async def test_create_payment(
    client: AsyncClient,
    parent_token: str,
    test_child_user: User,
    db_session: AsyncSession
):
    """Test creating a payment."""
    # Create a payment
    response = await client.post(
        "/api/v1/payments/record",
        json={
            "child_id": test_child_user.id,
            "amount": 10.50,
            "description": "Test payment"
        },
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["amount"] == -10.50  # Should be negative (reducing balance)
    assert data["description"] == "Test payment"
    assert data["is_adjustment"] == False
    assert data["child_id"] == test_child_user.id

async def test_create_adjustment_positive(
    client: AsyncClient,
    parent_token: str,
    test_child_user: User,
    db_session: AsyncSession
):
    """Test creating a positive adjustment."""
    # Create a positive adjustment
    response = await client.post(
        "/api/v1/payments/adjust",
        json={
            "child_id": test_child_user.id,
            "amount": 5.25,
            "description": "Bonus for good behavior",
            "is_adjustment": True
        },
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["amount"] == 5.25  # Should be positive (adding to balance)
    assert data["description"] == "Bonus for good behavior"
    assert data["is_adjustment"] == True
    assert data["child_id"] == test_child_user.id

async def test_create_adjustment_negative(
    client: AsyncClient,
    parent_token: str,
    test_child_user: User,
    db_session: AsyncSession
):
    """Test creating a negative adjustment."""
    # Create a negative adjustment
    response = await client.post(
        "/api/v1/payments/adjust",
        json={
            "child_id": test_child_user.id,
            "amount": -3.75,
            "description": "Deduction for missed chore",
            "is_adjustment": True
        },
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["amount"] == -3.75  # Should be negative (subtracting from balance)
    assert data["description"] == "Deduction for missed chore"
    assert data["is_adjustment"] == True
    assert data["child_id"] == test_child_user.id

async def test_get_payment_history(
    client: AsyncClient,
    parent_token: str,
    test_child_user: User,
    db_session: AsyncSession
):
    """Test getting payment history."""
    # Create a payment and adjustments first
    await client.post(
        "/api/v1/payments/record",
        json={
            "child_id": test_child_user.id,
            "amount": 10.0,
            "description": "Test payment"
        },
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    
    await client.post(
        "/api/v1/payments/adjust",
        json={
            "child_id": test_child_user.id,
            "amount": 5.0,
            "description": "Test adjustment",
            "is_adjustment": True
        },
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    
    # Get payment history
    response = await client.get(
        f"/api/v1/payments/history/{test_child_user.id}",
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) >= 2  # Should have at least the two payments we just created
    
    # Check that we can find our test payments
    payment_found = False
    adjustment_found = False
    
    for item in data:
        if item["description"] == "Test payment" and item["amount"] == -10.0 and not item["is_adjustment"]:
            payment_found = True
        elif item["description"] == "Test adjustment" and item["amount"] == 5.0 and item["is_adjustment"]:
            adjustment_found = True
    
    assert payment_found, "Test payment not found in history"
    assert adjustment_found, "Test adjustment not found in history"

async def test_get_child_balance(
    client: AsyncClient,
    parent_token: str,
    test_child_user: User,
    db_session: AsyncSession
):
    """Test getting child balance."""
    # First create an approved chore to have some earnings
    chore_response = await client.post(
        "/api/v1/chores/",
        json={
            "title": "Test chore for balance",
            "description": "For testing balance calculation",
            "reward": 15.0,
            "assignee_id": test_child_user.id
        },
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert chore_response.status_code == status.HTTP_201_CREATED
    chore_id = chore_response.json()["id"]
    
    # Mark chore as complete
    await client.put(
        f"/api/v1/chores/{chore_id}/complete",
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    
    # Approve the chore
    await client.put(
        f"/api/v1/chores/{chore_id}/approve",
        json={"reward_value": 15.0},
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    
    # Create a payment and adjustment
    await client.post(
        "/api/v1/payments/record",
        json={
            "child_id": test_child_user.id,
            "amount": 5.0,
            "description": "Balance test payment"
        },
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    
    await client.post(
        "/api/v1/payments/adjust",
        json={
            "child_id": test_child_user.id,
            "amount": 2.5,
            "description": "Balance test adjustment",
            "is_adjustment": True
        },
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    
    # Get balance
    response = await client.get(
        f"/api/v1/payments/balance/{test_child_user.id}",
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Check balance components
    assert "total_earned" in data
    assert "total_paid" in data
    assert "total_adjustments" in data
    assert "current_balance" in data
    
    # Validate balance calculation
    # total_earned should be 15.0 from the approved chore
    # total_paid should be 5.0 from the payment (stored as -5.0 but displayed as positive)
    # total_adjustments should be 2.5 from the adjustment
    # current_balance should be 15.0 + 2.5 - 5.0 = 12.5
    assert data["total_earned"] == 15.0
    assert data["total_paid"] == 5.0
    assert data["total_adjustments"] == 2.5
    assert data["current_balance"] == 12.5

async def test_child_cannot_adjust_balance(
    client: AsyncClient,
    child_token: str,
    test_child_user: User,
    db_session: AsyncSession
):
    """Test that children cannot adjust balances."""
    response = await client.post(
        "/api/v1/payments/adjust",
        json={
            "child_id": test_child_user.id,
            "amount": 100.0,
            "description": "Trying to give myself money",
            "is_adjustment": True
        },
        headers={"Authorization": f"Bearer {child_token}"}
    )
    
    assert response.status_code == status.HTTP_403_FORBIDDEN

async def test_parent_cannot_adjust_other_child(
    client: AsyncClient,
    parent_token: str,
    db_session: AsyncSession,
    other_parent_with_child
):
    """Test that a parent cannot adjust balance for another parent's child."""
    other_parent, other_child = other_parent_with_child
    
    response = await client.post(
        "/api/v1/payments/adjust",
        json={
            "child_id": other_child.id,
            "amount": 5.0,
            "description": "Test adjustment",
            "is_adjustment": True
        },
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    
    assert response.status_code in (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND)

@pytest.fixture
async def other_parent_with_child(db_session):
    """Create another parent with a child."""
    from backend.app.models.user import User
    from backend.app.core.security.password import get_password_hash
    
    # Create parent
    other_parent = User(
        username="otherparent",
        email="otherparent@example.com",
        hashed_password=get_password_hash("password123"),
        is_parent=True
    )
    db_session.add(other_parent)
    await db_session.commit()
    await db_session.refresh(other_parent)
    
    # Create child
    other_child = User(
        username="otherchild",
        hashed_password=get_password_hash("password123"),
        is_parent=False,
        parent_id=other_parent.id
    )
    db_session.add(other_child)
    await db_session.commit()
    await db_session.refresh(other_child)
    
    return other_parent, other_child