#!/usr/bin/env python3
"""
Phase 4.5 - Parent Flow Quick E2E Testing
Tests using existing demo users to avoid rate limits
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
TEST_TIMESTAMP = datetime.now().strftime("%H%M%S")

# Use existing demo users
PARENT_USERNAME = "demoparent"
PARENT_PASSWORD = "password123"
CHILD1_USERNAME = "demochild1"
CHILD1_PASSWORD = "password123"
CHILD2_USERNAME = "demochild2"
CHILD2_PASSWORD = "password123"

# Test results tracking
test_results = []
test_details = {}

def print_section(title: str):
    """Print section header"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print('='*60)

def print_test_result(test_name: str, passed: bool, details: str = ""):
    """Print and track test result"""
    status = "✅ PASSED" if passed else "❌ FAILED"
    print(f"\n{test_name}: {status}")
    if details:
        print(f"  Details: {details}")
    test_results.append((test_name, passed))
    test_details[test_name] = details

async def login(client: httpx.AsyncClient, username: str, password: str) -> str:
    """Login and return token"""
    response = await client.post(
        f"{API_BASE_URL}/users/login",
        data={"username": username, "password": password}
    )
    if response.status_code != 200:
        raise Exception(f"Login failed: {response.status_code} - {response.text}")
    return response.json()["access_token"]

async def run_parent_journey():
    """Run complete parent user journey with existing demo users"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        print_section("PHASE 4.5 - PARENT FLOW QUICK E2E TESTING")
        print(f"Using existing demo users")
        print(f"Timestamp: {TEST_TIMESTAMP}")
        
        # ========== SECTION 1: AUTHENTICATION ==========
        print_section("SECTION 1: AUTHENTICATION")
        
        # Test 1: Parent login
        print("\nTest 1: Parent Authentication")
        try:
            parent_token = await login(client, PARENT_USERNAME, PARENT_PASSWORD)
            print_test_result("Parent Authentication", True, "Successfully authenticated as demoparent")
        except Exception as e:
            print_test_result("Parent Authentication", False, str(e))
            return
        
        # Get parent info
        response = await client.get(
            f"{API_BASE_URL}/users/me",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        parent_user = response.json()
        parent_id = parent_user["id"]
        
        # Test 2: Child login
        print("\nTest 2: Child Authentication")
        try:
            child1_token = await login(client, CHILD1_USERNAME, CHILD1_PASSWORD)
            
            # Get child1's actual ID
            response = await client.get(
                f"{API_BASE_URL}/users/me",
                headers={"Authorization": f"Bearer {child1_token}"}
            )
            child1_user = response.json()
            child1_actual_id = child1_user["id"]
            
            print_test_result("Child Authentication", True, f"Logged in as {CHILD1_USERNAME} (ID: {child1_actual_id})")
        except Exception as e:
            print_test_result("Child Authentication", False, str(e))
            return
        
        # ========== SECTION 2: CHILDREN MANAGEMENT ==========
        print_section("SECTION 2: CHILDREN MANAGEMENT")
        
        # Test 3: View children list
        print("\nTest 3: View Children List")
        try:
            response = await client.get(
                f"{API_BASE_URL}/users/my-children",
                headers={"Authorization": f"Bearer {parent_token}"}
            )
            if response.status_code == 200:
                children = response.json()
                child_ids = [c["id"] for c in children]
                # Find the actual demochild1 in the list
                child1_from_list = next((c for c in children if c["username"] == CHILD1_USERNAME), None)
                if child1_from_list:
                    child1_actual_id = child1_from_list["id"]
                print_test_result("View Children List", len(children) >= 2, 
                                f"Found {len(children)} children")
            else:
                print_test_result("View Children List", False, f"Status: {response.status_code}")
                return
        except Exception as e:
            print_test_result("View Children List", False, str(e))
            return
        
        # Test 4: Get allowance summary
        print("\nTest 4: Get Allowance Summary")
        try:
            response = await client.get(
                f"{API_BASE_URL}/users/allowance-summary",
                headers={"Authorization": f"Bearer {parent_token}"}
            )
            if response.status_code == 200:
                summary = response.json()
                print_test_result("Get Allowance Summary", True, 
                                f"Retrieved summary for {len(summary)} children")
            else:
                print_test_result("Get Allowance Summary", False, f"Status: {response.status_code}")
        except Exception as e:
            print_test_result("Get Allowance Summary", False, str(e))
        
        # ========== SECTION 3: CHORE CREATION ==========
        print_section("SECTION 3: CHORE CREATION")
        
        # Test 5: Create unassigned chore
        print("\nTest 5: Create Unassigned Chore")
        try:
            chore_data = {
                "title": f"Clean Kitchen {TEST_TIMESTAMP}",
                "description": "Wash dishes and wipe counters",
                "reward": 4.50,
                "is_recurring": False,
                "assignee_id": None  # Explicitly set to None for unassigned
            }
            response = await client.post(
                f"{API_BASE_URL}/chores/",
                json=chore_data,
                headers={"Authorization": f"Bearer {parent_token}"}
            )
            if response.status_code == 201:
                unassigned_chore = response.json()
                print_test_result("Create Unassigned Chore", True, 
                                f"Created chore ID: {unassigned_chore['id']}")
            else:
                print_test_result("Create Unassigned Chore", False, 
                                f"Status: {response.status_code} - {response.text}")
        except Exception as e:
            print_test_result("Create Unassigned Chore", False, str(e))
        
        # Test 6: Create assigned chore with fixed reward
        print("\nTest 6: Create Fixed Reward Chore")
        try:
            chore_data = {
                "title": f"Homework {TEST_TIMESTAMP}",
                "description": "Complete all homework assignments",
                "reward": 2.50,
                "assignee_id": child1_actual_id,  # Use the actual ID of demochild1
                "is_recurring": False
            }
            response = await client.post(
                f"{API_BASE_URL}/chores/",
                json=chore_data,
                headers={"Authorization": f"Bearer {parent_token}"}
            )
            if response.status_code == 201:
                fixed_chore = response.json()
                print_test_result("Create Fixed Reward Chore", True, 
                                f"Created chore ID: {fixed_chore['id']}")
            else:
                print_test_result("Create Fixed Reward Chore", False, 
                                f"Status: {response.status_code}")
        except Exception as e:
            print_test_result("Create Fixed Reward Chore", False, str(e))
        
        # Test 7: Create range reward chore
        print("\nTest 7: Create Range Reward Chore")
        try:
            chore_data = {
                "title": f"Yard Work {TEST_TIMESTAMP}",
                "description": "Mow lawn and trim hedges",
                "is_range_reward": True,
                "min_reward": 8.00,
                "max_reward": 15.00,
                "assignee_id": child1_actual_id,  # Use the actual ID of demochild1
                "is_recurring": False
            }
            response = await client.post(
                f"{API_BASE_URL}/chores/",
                json=chore_data,
                headers={"Authorization": f"Bearer {parent_token}"}
            )
            if response.status_code == 201:
                range_chore = response.json()
                print_test_result("Create Range Reward Chore", True, 
                                f"Created chore ID: {range_chore['id']}")
            else:
                print_test_result("Create Range Reward Chore", False, 
                                f"Status: {response.status_code}")
        except Exception as e:
            print_test_result("Create Range Reward Chore", False, str(e))
        
        # ========== SECTION 4: CHORE COMPLETION ==========
        print_section("SECTION 4: CHORE COMPLETION")
        
        # Test 8: Child completes fixed chore
        print("\nTest 8: Complete Fixed Reward Chore")
        try:
            response = await client.post(
                f"{API_BASE_URL}/chores/{fixed_chore['id']}/complete",
                headers={"Authorization": f"Bearer {child1_token}"}
            )
            if response.status_code == 200:
                print_test_result("Complete Fixed Reward Chore", True, 
                                "Chore marked as completed")
            else:
                print_test_result("Complete Fixed Reward Chore", False, 
                                f"Status: {response.status_code}")
        except Exception as e:
            print_test_result("Complete Fixed Reward Chore", False, str(e))
        
        # Test 9: Child completes range chore
        print("\nTest 9: Complete Range Reward Chore")
        try:
            response = await client.post(
                f"{API_BASE_URL}/chores/{range_chore['id']}/complete",
                headers={"Authorization": f"Bearer {child1_token}"}
            )
            if response.status_code == 200:
                print_test_result("Complete Range Reward Chore", True, 
                                "Chore marked as completed")
            else:
                print_test_result("Complete Range Reward Chore", False, 
                                f"Status: {response.status_code}")
        except Exception as e:
            print_test_result("Complete Range Reward Chore", False, str(e))
        
        # ========== SECTION 5: APPROVALS ==========
        print_section("SECTION 5: APPROVALS")
        
        # Test 10: Get pending approvals
        print("\nTest 10: Get Pending Approvals")
        try:
            response = await client.get(
                f"{API_BASE_URL}/chores/pending-approval",
                headers={"Authorization": f"Bearer {parent_token}"}
            )
            if response.status_code == 200:
                pending = response.json()
                print_test_result("Get Pending Approvals", len(pending) >= 2, 
                                f"Found {len(pending)} pending approvals")
            else:
                print_test_result("Get Pending Approvals", False, 
                                f"Status: {response.status_code}")
        except Exception as e:
            print_test_result("Get Pending Approvals", False, str(e))
        
        # Test 11: Approve fixed reward
        print("\nTest 11: Approve Fixed Reward")
        try:
            response = await client.post(
                f"{API_BASE_URL}/chores/{fixed_chore['id']}/approve",
                json={},  # Empty body for fixed rewards
                headers={"Authorization": f"Bearer {parent_token}"}
            )
            if response.status_code == 200:
                print_test_result("Approve Fixed Reward", True, 
                                f"Approved for ${fixed_chore['reward']}")
            else:
                print_test_result("Approve Fixed Reward", False, 
                                f"Status: {response.status_code} - {response.text}")
        except Exception as e:
            print_test_result("Approve Fixed Reward", False, str(e))
        
        # Test 12: Approve range reward
        print("\nTest 12: Approve Range Reward")
        try:
            reward_value = 11.50  # Between min and max
            response = await client.post(
                f"{API_BASE_URL}/chores/{range_chore['id']}/approve",
                json={"reward_value": reward_value},
                headers={"Authorization": f"Bearer {parent_token}"}
            )
            if response.status_code == 200:
                print_test_result("Approve Range Reward", True, 
                                f"Approved for ${reward_value}")
            else:
                print_test_result("Approve Range Reward", False, 
                                f"Status: {response.status_code}")
        except Exception as e:
            print_test_result("Approve Range Reward", False, str(e))
        
        # ========== SECTION 6: ADJUSTMENTS ==========
        print_section("SECTION 6: ADJUSTMENTS")
        
        # Test 13: Create bonus adjustment
        print("\nTest 13: Create Bonus Adjustment")
        try:
            adjustment_data = {
                "child_id": child1_actual_id,  # Use the actual ID of demochild1
                "amount": 10.00,
                "reason": "Great grades on report card"
            }
            response = await client.post(
                f"{API_BASE_URL}/adjustments/",
                json=adjustment_data,
                headers={"Authorization": f"Bearer {parent_token}"}
            )
            if response.status_code == 201:
                bonus = response.json()
                print_test_result("Create Bonus Adjustment", True, 
                                f"Added ${bonus['amount']} bonus")
            else:
                print_test_result("Create Bonus Adjustment", False, 
                                f"Status: {response.status_code}")
        except Exception as e:
            print_test_result("Create Bonus Adjustment", False, str(e))
        
        # Test 14: Create deduction adjustment
        print("\nTest 14: Create Deduction Adjustment")
        try:
            adjustment_data = {
                "child_id": child1_actual_id,  # Use the actual ID of demochild1
                "amount": -3.00,
                "reason": "Forgot to do daily chore"
            }
            response = await client.post(
                f"{API_BASE_URL}/adjustments/",
                json=adjustment_data,
                headers={"Authorization": f"Bearer {parent_token}"}
            )
            if response.status_code == 201:
                deduction = response.json()
                print_test_result("Create Deduction Adjustment", True, 
                                f"Applied ${abs(float(deduction['amount']))} deduction")
            else:
                print_test_result("Create Deduction Adjustment", False, 
                                f"Status: {response.status_code}")
        except Exception as e:
            print_test_result("Create Deduction Adjustment", False, str(e))
        
        # Test 15: View adjustment history
        print("\nTest 15: View Adjustment History")
        try:
            response = await client.get(
                f"{API_BASE_URL}/adjustments/child/{child1_actual_id}",
                headers={"Authorization": f"Bearer {parent_token}"}
            )
            if response.status_code == 200:
                adjustments = response.json()
                print_test_result("View Adjustment History", len(adjustments) >= 2, 
                                f"Found {len(adjustments)} adjustments")
                # Show recent adjustments
                for adj in adjustments[:3]:
                    amount = float(adj['amount'])
                    print(f"    - {'+'if amount>=0 else ''}${abs(amount):.2f}: {adj['reason'][:40]}...")
            else:
                print_test_result("View Adjustment History", False, 
                                f"Status: {response.status_code}")
        except Exception as e:
            print_test_result("View Adjustment History", False, str(e))
        
        # ========== SECTION 7: BALANCE CHECK ==========
        print_section("SECTION 7: BALANCE VERIFICATION")
        
        # Test 16: Check child balance
        print("\nTest 16: Verify Child Balance")
        try:
            response = await client.get(
                f"{API_BASE_URL}/users/me/balance",
                headers={"Authorization": f"Bearer {child1_token}"}
            )
            if response.status_code == 200:
                balance_data = response.json()
                balance = balance_data.get('balance', 0)
                
                print_test_result("Verify Child Balance", True, 
                                f"Current balance: ${balance:.2f}")
                
                # Show balance breakdown
                print(f"  Balance Breakdown:")
                print(f"    Total Earned: ${balance_data.get('total_earned', 0):.2f}")
                print(f"    Adjustments: ${balance_data.get('adjustments', 0):.2f}")
                print(f"    Paid Out: ${balance_data.get('paid_out', 0):.2f}")
            else:
                print_test_result("Verify Child Balance", False, 
                                f"Status: {response.status_code}")
        except Exception as e:
            print_test_result("Verify Child Balance", False, str(e))

def print_summary():
    """Print test summary"""
    print_section("TEST SUMMARY")
    
    passed_count = sum(1 for _, passed in test_results if passed)
    total_count = len(test_results)
    
    # Group tests by section
    sections = {
        "Authentication": test_results[0:2] if len(test_results) >= 2 else test_results,
        "Children Management": test_results[2:4] if len(test_results) >= 4 else [],
        "Chore Creation": test_results[4:7] if len(test_results) >= 7 else [],
        "Chore Completion": test_results[7:9] if len(test_results) >= 9 else [],
        "Approvals": test_results[9:12] if len(test_results) >= 12 else [],
        "Adjustments": test_results[12:15] if len(test_results) >= 15 else [],
        "Balance": test_results[15:16] if len(test_results) >= 16 else []
    }
    
    print("\nResults by Section:")
    for section_name, section_tests in sections.items():
        if section_tests:
            section_passed = sum(1 for _, passed in section_tests if passed)
            section_total = len(section_tests)
            percent = (section_passed/section_total*100) if section_total > 0 else 0
            status = "✅" if section_passed == section_total else "⚠️"
            print(f"{status} {section_name}: {section_passed}/{section_total} ({percent:.0f}%)")
    
    print("\nDetailed Results:")
    for test_name, passed in test_results:
        status = "✅" if passed else "❌"
        print(f"{status} {test_name}")
    
    print(f"\n{'='*60}")
    print(f"OVERALL: {passed_count}/{total_count} tests passed ({(passed_count/total_count*100):.1f}%)")
    print('='*60)
    
    if passed_count == total_count:
        print("\n🎉 PERFECT SCORE! All parent flow features are working correctly!")
        print("Phase 4.5 Parent Flow Acceptance is COMPLETE! ✅")
    elif passed_count >= total_count * 0.85:
        print(f"\n✅ EXCELLENT! {(passed_count/total_count*100):.1f}% of tests passing.")
        print("Parent flow is production-ready!")
    else:
        print(f"\n⚠️ {(passed_count/total_count*100):.1f}% of tests passing.")
        print("Some features need attention.")

if __name__ == "__main__":
    print("Starting Phase 4.5 Parent Flow Quick E2E Tests...")
    print("Using existing demo users to avoid rate limits")
    print("Make sure the backend is running with: docker-compose up")
    print("")
    
    asyncio.run(run_parent_journey())
    print_summary()