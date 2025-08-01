"""
Test script to verify reward adjustment API endpoints.
"""
import asyncio
import httpx
from decimal import Decimal

# Configuration
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

# Test credentials
PARENT_USERNAME = "testparent2"
PARENT_PASSWORD = "password123"


async def get_auth_token():
    """Authenticate and get JWT token."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/users/login",
            data={
                "username": PARENT_USERNAME,
                "password": PARENT_PASSWORD
            }
        )
        if response.status_code != 200:
            print(f"Authentication failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
        
        data = response.json()
        return data["access_token"]


async def test_create_adjustment(token: str, child_id: int):
    """Test creating a reward adjustment."""
    print("\n=== Testing Create Adjustment ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test positive adjustment
    adjustment_data = {
        "child_id": child_id,
        "amount": "15.00",
        "reason": "Bonus for excellent behavior this week"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}{API_PREFIX}/adjustments/",
            headers=headers,
            json=adjustment_data
        )
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 201:
            data = response.json()
            print(f"Created adjustment: ID={data['id']}, Amount=${data['amount']}")
            print(f"Reason: {data['reason']}")
            return data['id']
        else:
            print(f"Error: {response.text}")
            return None


async def test_get_adjustments(token: str, child_id: int):
    """Test getting adjustments for a child."""
    print("\n=== Testing Get Child Adjustments ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}{API_PREFIX}/adjustments/child/{child_id}",
            headers=headers,
            params={"limit": 10}
        )
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            adjustments = response.json()
            print(f"Found {len(adjustments)} adjustments:")
            for adj in adjustments:
                print(f"  - ID: {adj['id']}, Amount: ${adj['amount']}, Reason: {adj['reason']}")
        else:
            print(f"Error: {response.text}")


async def test_get_total(token: str, child_id: int):
    """Test getting total adjustments for a child."""
    print("\n=== Testing Get Total Adjustments ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}{API_PREFIX}/adjustments/total/{child_id}",
            headers=headers
        )
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Total adjustments for child {child_id}: ${data['total_adjustments']}")
        else:
            print(f"Error: {response.text}")


async def test_validation(token: str, child_id: int):
    """Test API validation."""
    print("\n=== Testing API Validation ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 1: Zero amount (should fail)
    print("\n1. Testing zero amount (should fail):")
    adjustment_data = {
        "child_id": child_id,
        "amount": "0.00",
        "reason": "This should fail"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}{API_PREFIX}/adjustments/",
            headers=headers,
            json=adjustment_data
        )
        print(f"Status Code: {response.status_code}")
        if response.status_code == 422:
            print("✓ Correctly rejected zero amount")
        else:
            print(f"✗ Unexpected response: {response.text}")
    
    # Test 2: Amount out of range (should fail)
    print("\n2. Testing amount out of range (should fail):")
    adjustment_data = {
        "child_id": child_id,
        "amount": "1500.00",
        "reason": "This should fail"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}{API_PREFIX}/adjustments/",
            headers=headers,
            json=adjustment_data
        )
        print(f"Status Code: {response.status_code}")
        if response.status_code == 422:
            print("✓ Correctly rejected out-of-range amount")
        else:
            print(f"✗ Unexpected response: {response.text}")
    
    # Test 3: Short reason (should fail)
    print("\n3. Testing short reason (should fail):")
    adjustment_data = {
        "child_id": child_id,
        "amount": "5.00",
        "reason": "Hi"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}{API_PREFIX}/adjustments/",
            headers=headers,
            json=adjustment_data
        )
        print(f"Status Code: {response.status_code}")
        if response.status_code == 422:
            print("✓ Correctly rejected short reason")
        else:
            print(f"✗ Unexpected response: {response.text}")


async def main():
    """Run all API tests."""
    print("Testing Reward Adjustment API Endpoints...")
    
    # Get authentication token
    token = await get_auth_token()
    if not token:
        print("Failed to authenticate. Exiting.")
        return
    
    print(f"✓ Authenticated successfully")
    
    # Use child_id 2 (testchild from previous tests)
    child_id = 2
    
    # Run tests
    adjustment_id = await test_create_adjustment(token, child_id)
    await test_get_adjustments(token, child_id)
    await test_get_total(token, child_id)
    await test_validation(token, child_id)
    
    print("\n=== API Tests Complete ===")


if __name__ == "__main__":
    asyncio.run(main())