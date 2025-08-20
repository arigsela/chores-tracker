#!/usr/bin/env python3
"""
Setup script to create test users for E2E testing
"""
import asyncio
import httpx
from datetime import datetime

API_BASE_URL = "http://localhost:8000/api/v1"

# Generate unique usernames with timestamp
timestamp = datetime.now().strftime("%H%M%S")
PARENT_USERNAME = f"test_parent_{timestamp}"
PARENT_PASSWORD = "TestPass123!"
CHILD_USERNAME = f"test_child_{timestamp}"
CHILD_PASSWORD = "ChildPass123!"

async def create_users():
    """Create parent and child users for E2E testing"""
    async with httpx.AsyncClient() as client:
        # 1. Create parent user
        print(f"Creating parent user: {PARENT_USERNAME}")
        parent_data = {
            "username": PARENT_USERNAME,
            "password": PARENT_PASSWORD,
            "email": f"{PARENT_USERNAME}@test.com",
            "is_parent": True
        }
        
        response = await client.post(
            f"{API_BASE_URL}/users/register",
            json=parent_data
        )
        
        if response.status_code == 200:
            print(f"✅ Parent user created: {PARENT_USERNAME}")
            parent_user = response.json()
        else:
            print(f"❌ Failed to create parent: {response.status_code} - {response.text}")
            return None, None
        
        # 2. Login as parent to get token
        print("Logging in as parent...")
        login_data = {
            "username": PARENT_USERNAME,
            "password": PARENT_PASSWORD
        }
        
        response = await client.post(
            f"{API_BASE_URL}/users/login",
            data=login_data
        )
        
        if response.status_code == 200:
            parent_token = response.json()["access_token"]
            print("✅ Parent logged in successfully")
        else:
            print(f"❌ Failed to login parent: {response.status_code}")
            return None, None
        
        # 3. Create child user
        print(f"Creating child user: {CHILD_USERNAME}")
        child_data = {
            "username": CHILD_USERNAME,
            "password": CHILD_PASSWORD,
            "is_parent": False,
            "parent_id": parent_user["id"]
        }
        
        response = await client.post(
            f"{API_BASE_URL}/users/register",
            json=child_data,
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        if response.status_code == 200:
            print(f"✅ Child user created: {CHILD_USERNAME}")
        else:
            print(f"❌ Failed to create child: {response.status_code} - {response.text}")
            return None, None
        
        return {
            "parent_username": PARENT_USERNAME,
            "parent_password": PARENT_PASSWORD,
            "child_username": CHILD_USERNAME,
            "child_password": CHILD_PASSWORD
        }

async def main():
    """Main function"""
    users = await create_users()
    if users:
        print("\n✅ Test users created successfully!")
        print(f"Parent: {users['parent_username']} / {users['parent_password']}")
        print(f"Child: {users['child_username']} / {users['child_password']}")
        
        # Save to file for Playwright test
        with open('/tmp/test_users.txt', 'w') as f:
            f.write(f"{users['parent_username']},{users['parent_password']},{users['child_username']},{users['child_password']}")
        print("\nUser credentials saved to /tmp/test_users.txt")
    else:
        print("\n❌ Failed to create test users")
        return 1
    return 0

if __name__ == "__main__":
    exit(asyncio.run(main()))