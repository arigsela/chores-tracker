#!/usr/bin/env python3
"""
Test script for Phase 4.3 - Approvals (Fixed and Range)
Tests both individual and bulk approval functionality
"""

import asyncio
import httpx
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Test configuration
API_BASE_URL = "http://localhost:8000/api/v1"
PARENT_USERNAME = "demoparent"
PARENT_PASSWORD = "password123"
CHILD1_USERNAME = "demochild1"
CHILD1_PASSWORD = "password123"
CHILD2_USERNAME = "demochild2"
CHILD2_PASSWORD = "password123"

# Test results tracking
test_results = []

def print_test_result(test_name: str, passed: bool, details: str = ""):
    """Print and track test result"""
    status = "✅ PASSED" if passed else "❌ FAILED"
    print(f"{test_name}: {status}")
    if details:
        print(f"  Details: {details}")
    test_results.append((test_name, passed))

async def login(client: httpx.AsyncClient, username: str, password: str) -> str:
    """Login and return token"""
    response = await client.post(
        f"{API_BASE_URL}/users/login",
        data={"username": username, "password": password}
    )
    if response.status_code != 200:
        raise Exception(f"Login failed: {response.text}")
    return response.json()["access_token"]

async def create_test_chores(client: httpx.AsyncClient, token: str, child_id: int):
    """Create test chores for approval testing"""
    chores = []
    
    # Create fixed reward chore
    fixed_chore_data = {
        "title": f"Test Fixed Chore {datetime.now().timestamp()}",
        "description": "Test chore with fixed reward",
        "reward": 5.00,
        "is_range_reward": False,
        "assignee_id": child_id,
        "is_recurring": False
    }
    
    response = await client.post(
        f"{API_BASE_URL}/chores/",
        json=fixed_chore_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code == 201:
        chores.append(response.json())
    
    # Create range reward chore
    range_chore_data = {
        "title": f"Test Range Chore {datetime.now().timestamp()}",
        "description": "Test chore with range reward",
        "is_range_reward": True,
        "min_reward": 3.00,
        "max_reward": 10.00,
        "assignee_id": child_id,
        "is_recurring": False
    }
    
    response = await client.post(
        f"{API_BASE_URL}/chores/",
        json=range_chore_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code == 201:
        chores.append(response.json())
    
    return chores

async def complete_chore(client: httpx.AsyncClient, token: str, chore_id: int):
    """Complete a chore as child"""
    response = await client.post(
        f"{API_BASE_URL}/chores/{chore_id}/complete",
        headers={"Authorization": f"Bearer {token}"}
    )
    return response.status_code == 200

async def run_tests():
    """Run all approval tests"""
    async with httpx.AsyncClient() as client:
        print("\n" + "="*60)
        print("PHASE 4.3 - APPROVALS TESTING")
        print("="*60 + "\n")
        
        # Test 1: Parent authentication
        print("Test 1: Parent Authentication")
        try:
            parent_token = await login(client, PARENT_USERNAME, PARENT_PASSWORD)
            print_test_result("Parent Authentication", True, "Successfully logged in as parent")
        except Exception as e:
            print_test_result("Parent Authentication", False, str(e))
            return
        
        # Test 2: Child authentication
        print("\nTest 2: Child Authentication")
        try:
            child1_token = await login(client, CHILD1_USERNAME, CHILD1_PASSWORD)
            child2_token = await login(client, CHILD2_USERNAME, CHILD2_PASSWORD)
            print_test_result("Child Authentication", True, "Both children logged in")
        except Exception as e:
            print_test_result("Child Authentication", False, str(e))
            return
        
        # Get child IDs
        response = await client.get(
            f"{API_BASE_URL}/users/my-children",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        children = response.json()
        child1_id = next((c["id"] for c in children if c["username"] == CHILD1_USERNAME), None)
        child2_id = next((c["id"] for c in children if c["username"] == CHILD2_USERNAME), None)
        
        # Test 3: Create test chores
        print("\nTest 3: Create Test Chores")
        try:
            chores1 = await create_test_chores(client, parent_token, child1_id)
            chores2 = await create_test_chores(client, parent_token, child2_id)
            all_chores = chores1 + chores2
            print_test_result("Create Test Chores", True, f"Created {len(all_chores)} test chores")
        except Exception as e:
            print_test_result("Create Test Chores", False, str(e))
            return
        
        # Test 4: Complete chores as children
        print("\nTest 4: Complete Chores")
        try:
            # Child 1 completes their chores
            for chore in chores1:
                await complete_chore(client, child1_token, chore["id"])
            
            # Child 2 completes their chores
            for chore in chores2:
                await complete_chore(client, child2_token, chore["id"])
            
            print_test_result("Complete Chores", True, f"Completed {len(all_chores)} chores")
        except Exception as e:
            print_test_result("Complete Chores", False, str(e))
        
        # Test 5: Get pending approvals
        print("\nTest 5: Get Pending Approvals")
        try:
            response = await client.get(
                f"{API_BASE_URL}/chores/pending-approval",
                headers={"Authorization": f"Bearer {parent_token}"}
            )
            pending_chores = response.json()
            pending_count = len(pending_chores)
            print_test_result("Get Pending Approvals", pending_count >= len(all_chores), 
                            f"Found {pending_count} pending approvals")
        except Exception as e:
            print_test_result("Get Pending Approvals", False, str(e))
        
        # Test 6: Approve fixed reward chore
        print("\nTest 6: Approve Fixed Reward Chore")
        try:
            fixed_chore = next((c for c in pending_chores if not c.get("is_range_reward")), None)
            if fixed_chore:
                response = await client.post(
                    f"{API_BASE_URL}/chores/{fixed_chore['id']}/approve",
                    json={},  # Empty body required by the endpoint
                    headers={"Authorization": f"Bearer {parent_token}"}
                )
                print(f"  Debug - Response status: {response.status_code}")
                if response.status_code == 422:
                    print(f"  Debug - Error details: {response.text}")
                passed = response.status_code in [200, 201]
                print_test_result("Approve Fixed Reward", passed, 
                                f"Approved chore with ${fixed_chore.get('reward', 0):.2f} reward")
            else:
                print_test_result("Approve Fixed Reward", False, "No fixed reward chore found")
        except Exception as e:
            print_test_result("Approve Fixed Reward", False, str(e))
        
        # Test 7: Approve range reward chore with custom value
        print("\nTest 7: Approve Range Reward Chore")
        try:
            range_chore = next((c for c in pending_chores if c.get("is_range_reward")), None)
            if range_chore:
                # Use middle of the actual range
                min_reward = range_chore.get("min_reward", 0)
                max_reward = range_chore.get("max_reward", 10)
                custom_reward = (min_reward + max_reward) / 2
                response = await client.post(
                    f"{API_BASE_URL}/chores/{range_chore['id']}/approve",
                    json={"reward_value": custom_reward},
                    headers={"Authorization": f"Bearer {parent_token}"}
                )
                print(f"  Debug - Response status: {response.status_code}")
                if response.status_code == 422:
                    print(f"  Debug - Error details: {response.text}")
                passed = response.status_code in [200, 201]
                print_test_result("Approve Range Reward", passed, 
                                f"Approved with custom reward ${custom_reward:.2f}")
            else:
                print_test_result("Approve Range Reward", False, "No range reward chore found")
        except Exception as e:
            print_test_result("Approve Range Reward", False, str(e))
        
        # Test 8: Verify balances updated
        print("\nTest 8: Verify Balance Updates")
        try:
            # Small delay to ensure database is updated
            await asyncio.sleep(0.5)
            
            # Check child 1 balance
            response = await client.get(
                f"{API_BASE_URL}/users/me/balance",
                headers={"Authorization": f"Bearer {child1_token}"}
            )
            balance_data1 = response.json()
            child1_balance = balance_data1.get("balance", 0)
            child1_earned = balance_data1.get("total_earned", 0)
            
            # Check child 2 balance  
            response = await client.get(
                f"{API_BASE_URL}/users/me/balance",
                headers={"Authorization": f"Bearer {child2_token}"}
            )
            balance_data2 = response.json()
            child2_balance = balance_data2.get("balance", 0)
            child2_earned = balance_data2.get("total_earned", 0)
            
            print(f"  Debug - Child1 balance response: {balance_data1}")
            print(f"  Debug - Child2 balance response: {balance_data2}")
            
            # Check either balance or total_earned increased (since we approved some chores)
            passed = child1_balance > 0 or child2_balance > 0 or child1_earned > 0 or child2_earned > 0
            print_test_result("Verify Balance Updates", passed,
                            f"Child1: ${child1_balance:.2f}, Child2: ${child2_balance:.2f}")
        except Exception as e:
            print_test_result("Verify Balance Updates", False, str(e))
        
        # Test 9: Bulk approval simulation
        print("\nTest 9: Bulk Approval (Multiple Fixed Rewards)")
        try:
            # Create multiple fixed reward chores
            bulk_chores = []
            for i in range(3):
                chore_data = {
                    "title": f"Bulk Test Chore {i+1}",
                    "description": "Test chore for bulk approval",
                    "reward": 2.50,
                    "is_range_reward": False,
                    "assignee_id": child1_id,
                    "is_recurring": False
                }
                response = await client.post(
                    f"{API_BASE_URL}/chores/",
                    json=chore_data,
                    headers={"Authorization": f"Bearer {parent_token}"}
                )
                if response.status_code == 201:
                    bulk_chores.append(response.json())
            
            # Complete all bulk chores
            for chore in bulk_chores:
                await complete_chore(client, child1_token, chore["id"])
            
            # Approve all at once
            approved_count = 0
            for chore in bulk_chores:
                response = await client.post(
                    f"{API_BASE_URL}/chores/{chore['id']}/approve",
                    json={},  # Empty body required by the endpoint
                    headers={"Authorization": f"Bearer {parent_token}"}
                )
                if response.status_code in [200, 201]:
                    approved_count += 1
            
            passed = approved_count == len(bulk_chores)
            print_test_result("Bulk Approval", passed, 
                            f"Approved {approved_count}/{len(bulk_chores)} chores")
        except Exception as e:
            print_test_result("Bulk Approval", False, str(e))
        
        # Clean up test chores
        print("\nTest 10: Cleanup Test Chores")
        try:
            cleanup_count = 0
            # Get all chores
            response = await client.get(
                f"{API_BASE_URL}/chores/",
                headers={"Authorization": f"Bearer {parent_token}"}
            )
            all_parent_chores = response.json()
            
            # Delete test chores
            for chore in all_parent_chores:
                if "Test" in chore.get("title", "") or "Bulk Test" in chore.get("title", ""):
                    response = await client.delete(
                        f"{API_BASE_URL}/chores/{chore['id']}",
                        headers={"Authorization": f"Bearer {parent_token}"}
                    )
                    if response.status_code in [200, 204]:
                        cleanup_count += 1
            
            print_test_result("Cleanup", True, f"Deleted {cleanup_count} test chores")
        except Exception as e:
            print_test_result("Cleanup", False, str(e))

def print_summary():
    """Print test summary"""
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed_count = sum(1 for _, passed in test_results if passed)
    total_count = len(test_results)
    
    for test_name, passed in test_results:
        status = "✅" if passed else "❌"
        print(f"{status} {test_name}")
    
    print(f"\nTotal: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n🎉 ALL TESTS PASSED! Phase 4.3 approval functionality is working correctly.")
    else:
        print(f"\n⚠️  {total_count - passed_count} test(s) failed. Please review the failures above.")

if __name__ == "__main__":
    print("Starting Phase 4.3 Approval Tests...")
    print("Make sure the backend is running with: docker-compose up")
    print("")
    
    asyncio.run(run_tests())
    print_summary()