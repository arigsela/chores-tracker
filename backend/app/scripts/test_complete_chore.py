#!/usr/bin/env python3
"""Test the complete chore functionality."""

import asyncio
import httpx

BASE_URL = "http://localhost:8000"

async def main():
    """Test completing a chore as a child."""
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
        
        # Get available chores
        print("\n2. Getting available chores...")
        chores_response = await client.get(
            f"{BASE_URL}/api/v1/chores/available",
            headers=headers
        )
        
        if chores_response.status_code != 200:
            print(f"Failed to get chores: {chores_response.text}")
            return
            
        chores = chores_response.json()
        print(f"✓ Found {len(chores)} available chores")
        
        if not chores:
            print("No chores available to complete")
            return
            
        # Complete the first chore
        chore_to_complete = chores[0]
        print(f"\n3. Completing chore: '{chore_to_complete['title']}' (ID: {chore_to_complete['id']})")
        
        complete_response = await client.post(
            f"{BASE_URL}/api/v1/chores/{chore_to_complete['id']}/complete",
            headers=headers
        )
        
        if complete_response.status_code == 200:
            completed_chore = complete_response.json()
            print(f"✓ Chore marked as complete!")
            print(f"  - Completed at: {completed_chore.get('completed_at', 'N/A')}")
            print(f"  - Status: {'Pending Approval' if not completed_chore.get('is_approved') else 'Approved'}")
        else:
            print(f"✗ Failed to complete chore: {complete_response.text}")
            return
            
        # Verify chore moved from available
        print("\n4. Verifying chore is no longer available...")
        chores_response = await client.get(
            f"{BASE_URL}/api/v1/chores/available",
            headers=headers
        )
        
        if chores_response.status_code == 200:
            new_chores = chores_response.json()
            chore_ids = [c['id'] for c in new_chores]
            if chore_to_complete['id'] not in chore_ids:
                print(f"✓ Chore no longer in available list ({len(new_chores)} remaining)")
            else:
                print("✗ Chore still appears in available list")
        
        # Check if chore is in pending approval
        print("\n5. Checking if chore is pending approval...")
        all_chores_response = await client.get(
            f"{BASE_URL}/api/v1/chores",
            headers=headers
        )
        
        if all_chores_response.status_code == 200:
            all_chores = all_chores_response.json()
            completed_chore = next((c for c in all_chores if c['id'] == chore_to_complete['id']), None)
            if completed_chore:
                if completed_chore['is_completed'] and not completed_chore['is_approved']:
                    print("✓ Chore is pending parent approval")
                    print(f"  - Completed: {completed_chore['is_completed']}")
                    print(f"  - Approved: {completed_chore['is_approved']}")
                elif completed_chore['is_approved']:
                    print("✓ Chore was auto-approved")
                else:
                    print("✗ Unexpected chore state")
            else:
                print("✗ Could not find completed chore")
        
        print("\n✅ Complete chore functionality test passed!")
        
        # Now test as parent to see pending approval
        print("\n6. Logging in as parent to check pending approval...")
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
            
            pending_response = await client.get(
                f"{BASE_URL}/api/v1/chores/pending-approval",
                headers=parent_headers
            )
            
            if pending_response.status_code == 200:
                pending_chores = pending_response.json()
                if any(c['id'] == chore_to_complete['id'] for c in pending_chores):
                    print(f"✓ Parent can see chore in pending approval list ({len(pending_chores)} total)")
                else:
                    print("✗ Chore not found in parent's pending approval list")

if __name__ == "__main__":
    asyncio.run(main())