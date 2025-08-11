#!/usr/bin/env python3
"""Test the balance functionality for child users."""

import asyncio
import httpx

BASE_URL = "http://localhost:8000"

async def main():
    """Test balance retrieval for a child user."""
    async with httpx.AsyncClient() as client:
        # Login as child
        print("1. Logging in as demochild...")
        login_data = {
            "username": "demochild",
            "password": "child123"
        }
        
        login_response = await client.post(
            f"{BASE_URL}/api/v1/users/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if login_response.status_code != 200:
            print(f"Login failed: {login_response.text}")
            return
            
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✓ Logged in successfully")
        
        # Get balance
        print("\n2. Getting balance...")
        balance_response = await client.get(
            f"{BASE_URL}/api/v1/users/me/balance",
            headers=headers
        )
        
        if balance_response.status_code != 200:
            print(f"Failed to get balance: {balance_response.text}")
            return
            
        balance = balance_response.json()
        print("✓ Balance retrieved successfully!")
        print("\n📊 Balance Details:")
        print(f"  Current Balance: ${balance['balance']:.2f}")
        print(f"  Total Earned: ${balance['total_earned']:.2f}")
        print(f"  Adjustments: ${balance['adjustments']:.2f}")
        print(f"  Paid Out: ${balance['paid_out']:.2f}")
        print(f"  Pending Approval: ${balance['pending_chores_value']:.2f}")
        
        # Calculate expected balance
        expected = balance['total_earned'] + balance['adjustments'] - balance['paid_out']
        print(f"\n💡 Balance Calculation:")
        print(f"  ${balance['total_earned']:.2f} (earned) + ${balance['adjustments']:.2f} (adjustments) - ${balance['paid_out']:.2f} (paid) = ${expected:.2f}")
        
        if abs(balance['balance'] - expected) < 0.01:
            print("✓ Balance calculation is correct!")
        else:
            print(f"✗ Balance mismatch! Expected ${expected:.2f} but got ${balance['balance']:.2f}")
        
        # Test parent trying to access balance endpoint
        print("\n3. Testing parent access (should fail)...")
        parent_login = {
            "username": "demoparent",
            "password": "demo123"
        }
        
        parent_response = await client.post(
            f"{BASE_URL}/api/v1/users/login",
            data=parent_login,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if parent_response.status_code == 200:
            parent_token = parent_response.json()["access_token"]
            parent_headers = {"Authorization": f"Bearer {parent_token}"}
            
            parent_balance = await client.get(
                f"{BASE_URL}/api/v1/users/me/balance",
                headers=parent_headers
            )
            
            if parent_balance.status_code == 403:
                print("✓ Parent correctly denied access to child balance endpoint")
            else:
                print(f"✗ Unexpected response for parent: {parent_balance.status_code}")
        
        print("\n✅ Balance functionality test completed!")

if __name__ == "__main__":
    asyncio.run(main())