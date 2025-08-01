#!/usr/bin/env python3
"""Create a test child for testparent."""

import asyncio
import sys
import httpx
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

BASE_URL = "http://localhost:8000"
PARENT_USERNAME = "testparent"
PARENT_PASSWORD = "password123"


async def login():
    """Login as parent user and get token."""
    async with httpx.AsyncClient() as client:
        # Login
        response = await client.post(
            f"{BASE_URL}/api/v1/users/login",
            data={"username": PARENT_USERNAME, "password": PARENT_PASSWORD}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Logged in as {PARENT_USERNAME}")
            return data["access_token"]
        else:
            print(f"✗ Login failed: {response.status_code}")
            print(response.text)
            return None


async def create_child():
    """Create a child user for testparent."""
    token = await login()
    if not token:
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient() as client:
        # Create child user
        child_data = {
            "username": "testchild1",
            "password": "childpass123",
            "is_parent": False
        }
        
        response = await client.post(
            f"{BASE_URL}/api/v1/users/",
            json=child_data,
            headers=headers
        )
        
        if response.status_code == 201:
            print(f"✓ Created child user: testchild1")
            return response.json()
        else:
            print(f"✗ Failed to create child: {response.status_code}")
            print(response.text)
            return None


async def main():
    """Run the script."""
    print("Creating test child for testparent")
    print("=" * 50)
    
    child = await create_child()
    if child:
        print(f"\nChild created successfully!")
        print(f"ID: {child['id']}")
        print(f"Username: {child['username']}")
    
    print("\n" + "=" * 50)


if __name__ == "__main__":
    asyncio.run(main())