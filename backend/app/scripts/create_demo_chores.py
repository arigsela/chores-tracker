#!/usr/bin/env python3
"""Create demo chores for testing."""

import asyncio
import httpx

BASE_URL = "http://localhost:8000"

async def main():
    """Create demo chores."""
    async with httpx.AsyncClient() as client:
        # Login as parent
        login_data = {
            "username": "demoparent",
            "password": "demo123"
        }
        
        print("Logging in as demoparent...")
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
        
        # Get child user ID
        print("Getting child user ID...")
        children_response = await client.get(
            f"{BASE_URL}/api/v1/users/my-children",
            headers=headers
        )
        
        if children_response.status_code != 200:
            print(f"Failed to get children: {children_response.text}")
            return
            
        children = children_response.json()
        child = next((c for c in children if c["username"] == "demochild"), None)
        
        if not child:
            print("Child user 'demochild' not found!")
            return
            
        child_id = child["id"]
        print(f"Found child: demochild (ID: {child_id})")
        
        # Create test chores
        chores = [
            {
                "title": "Clean Your Room",
                "description": "Make bed, organize toys, vacuum floor",
                "reward": 5.0,
                "is_range_reward": False,
                "assignee_id": child_id,
                "is_recurring": True,
                "cooldown_days": 7
            },
            {
                "title": "Do Homework",
                "description": "Complete all homework assignments",
                "reward": 3.0,
                "is_range_reward": False,
                "assignee_id": child_id,
                "is_recurring": True,
                "cooldown_days": 1
            },
            {
                "title": "Take Out Trash",
                "description": "Empty all wastebaskets and take to curb",
                "is_range_reward": True,
                "min_reward": 2.0,
                "max_reward": 4.0,
                "assignee_id": child_id,
                "is_recurring": True,
                "cooldown_days": 3
            },
            {
                "title": "Feed the Pet",
                "description": "Give food and fresh water to the pet",
                "reward": 2.0,
                "is_range_reward": False,
                "assignee_id": child_id,
                "is_recurring": True,
                "cooldown_days": 1
            },
            {
                "title": "Set the Table",
                "description": "Set plates, utensils, and napkins for dinner",
                "is_range_reward": True,
                "min_reward": 1.0,
                "max_reward": 3.0,
                "assignee_id": child_id,
                "is_recurring": True,
                "cooldown_days": 1
            }
        ]
        
        print("\nCreating chores...")
        for chore_data in chores:
            response = await client.post(
                f"{BASE_URL}/api/v1/chores/",
                json=chore_data,
                headers=headers,
                follow_redirects=True
            )
            
            if response.status_code == 201:
                chore = response.json()
                print(f"✓ Created chore: {chore['title']}")
            else:
                print(f"✗ Failed to create chore '{chore_data['title']}': Status {response.status_code}, {response.text}")
        
        print("\nDemo chores created successfully!")
        print("\nYou can now login as 'demochild' with password 'child123' to test the chores functionality.")

if __name__ == "__main__":
    asyncio.run(main())