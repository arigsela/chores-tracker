#!/usr/bin/env python3
"""
Phase 4.5 - Parent Flow End-to-End Testing
Complete parent user journey testing including all implemented features
"""

import asyncio
import httpx
from datetime import datetime, timedelta
import sys
from pathlib import Path
import random
import time

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Test configuration
API_BASE_URL = "http://localhost:8000/api/v1"
TEST_TIMESTAMP = datetime.now().strftime("%H%M%S")

# Test user credentials
PARENT_USERNAME = f"testparent{TEST_TIMESTAMP}"
PARENT_PASSWORD = "TestPass123!"
CHILD1_USERNAME = f"testchild1{TEST_TIMESTAMP}"
CHILD1_PASSWORD = "TestPass123!"
CHILD2_USERNAME = f"testchild2{TEST_TIMESTAMP}"
CHILD2_PASSWORD = "TestPass123!"

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
    """Run complete parent user journey"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        print_section("PHASE 4.5 - PARENT FLOW E2E TESTING")
        print(f"Timestamp: {TEST_TIMESTAMP}")
        
        # ========== SECTION 1: USER REGISTRATION ==========
        print_section("SECTION 1: USER REGISTRATION & AUTHENTICATION")
        
        # Test 1: Register parent user
        print("\nTest 1: Register Parent User")
        try:
            parent_data = {
                "username": PARENT_USERNAME,
                "password": PARENT_PASSWORD,
                "is_parent": "true",
                "email": f"{PARENT_USERNAME}@example.com"
            }
            response = await client.post(f"{API_BASE_URL}/users/register", data=parent_data)
            if response.status_code == 201:
                parent_user = response.json()
                parent_id = parent_user["id"]
                print_test_result("Register Parent User", True, f"Created {PARENT_USERNAME} (ID: {parent_id})")
            else:
                print_test_result("Register Parent User", False, f"Status: {response.status_code}")
                return
        except Exception as e:
            print_test_result("Register Parent User", False, str(e))
            return
        
        # Test 2: Parent login
        print("\nTest 2: Parent Authentication")
        try:
            parent_token = await login(client, PARENT_USERNAME, PARENT_PASSWORD)
            print_test_result("Parent Authentication", True, "Successfully authenticated")
        except Exception as e:
            print_test_result("Parent Authentication", False, str(e))
            return
        
        # Test 3: Create child users
        print("\nTest 3: Create Child Users")
        child_ids = []
        try:
            # Wait to avoid rate limiting from parent registration
            await asyncio.sleep(1)
            
            for i, child_username in enumerate([CHILD1_USERNAME, CHILD2_USERNAME]):
                if i > 0:
                    # Wait between child registrations to avoid rate limiting
                    print("  Waiting to avoid rate limit...")
                    await asyncio.sleep(21)  # Rate limit is 3 per minute
                    
                child_data = {
                    "username": child_username,
                    "password": CHILD1_PASSWORD,
                    "is_parent": "false",
                    "parent_id": str(parent_id)
                }
                response = await client.post(
                    f"{API_BASE_URL}/users/register",
                    data=child_data,
                    headers={"Authorization": f"Bearer {parent_token}"}
                )
                if response.status_code == 201:
                    child = response.json()
                    child_ids.append(child["id"])
                    print(f"  Created {child_username} (ID: {child['id']})")
                else:
                    print(f"  Failed to create {child_username}: {response.status_code} - {response.text}")
            
            print_test_result("Create Child Users", len(child_ids) == 2, 
                            f"Created {len(child_ids)} children")
        except Exception as e:
            print_test_result("Create Child Users", False, str(e))
            return
        
        # ========== SECTION 2: CHILDREN MANAGEMENT ==========
        print_section("SECTION 2: CHILDREN MANAGEMENT")
        
        # Test 4: View children list
        print("\nTest 4: View Children List")
        try:
            response = await client.get(
                f"{API_BASE_URL}/users/my-children",
                headers={"Authorization": f"Bearer {parent_token}"}
            )
            if response.status_code == 200:
                children = response.json()
                print_test_result("View Children List", len(children) == 2, 
                                f"Found {len(children)} children")
            else:
                print_test_result("View Children List", False, f"Status: {response.status_code}")
        except Exception as e:
            print_test_result("View Children List", False, str(e))
        
        # Test 5: Get allowance summary
        print("\nTest 5: Get Allowance Summary")
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
        
        # ========== SECTION 3: CHORE MANAGEMENT ==========
        print_section("SECTION 3: CHORE MANAGEMENT")
        
        # Test 6: Create unassigned chore
        print("\nTest 6: Create Unassigned Chore")
        try:
            chore_data = {
                "title": f"Clean Living Room {TEST_TIMESTAMP}",
                "description": "Vacuum and dust the living room",
                "reward": 5.00,
                "is_recurring": False
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
                print_test_result("Create Unassigned Chore", False, f"Status: {response.status_code}")
        except Exception as e:
            print_test_result("Create Unassigned Chore", False, str(e))
        
        # Test 7: Create assigned chore (fixed reward)
        print("\nTest 7: Create Assigned Chore (Fixed Reward)")
        try:
            chore_data = {
                "title": f"Take Out Trash {TEST_TIMESTAMP}",
                "description": "Take trash bins to curb",
                "reward": 3.50,
                "assignee_id": child_ids[0],
                "is_recurring": False
            }
            response = await client.post(
                f"{API_BASE_URL}/chores/",
                json=chore_data,
                headers={"Authorization": f"Bearer {parent_token}"}
            )
            if response.status_code == 201:
                fixed_chore = response.json()
                print_test_result("Create Assigned Chore (Fixed)", True, 
                                f"Created chore ID: {fixed_chore['id']}")
            else:
                print_test_result("Create Assigned Chore (Fixed)", False, f"Status: {response.status_code}")
        except Exception as e:
            print_test_result("Create Assigned Chore (Fixed)", False, str(e))
        
        # Test 8: Create assigned chore (range reward)
        print("\nTest 8: Create Assigned Chore (Range Reward)")
        try:
            chore_data = {
                "title": f"Wash Car {TEST_TIMESTAMP}",
                "description": "Wash and vacuum the car",
                "is_range_reward": True,
                "min_reward": 5.00,
                "max_reward": 10.00,
                "assignee_id": child_ids[0],
                "is_recurring": False
            }
            response = await client.post(
                f"{API_BASE_URL}/chores/",
                json=chore_data,
                headers={"Authorization": f"Bearer {parent_token}"}
            )
            if response.status_code == 201:
                range_chore = response.json()
                print_test_result("Create Assigned Chore (Range)", True, 
                                f"Created chore ID: {range_chore['id']}")
            else:
                print_test_result("Create Assigned Chore (Range)", False, f"Status: {response.status_code}")
        except Exception as e:
            print_test_result("Create Assigned Chore (Range)", False, str(e))
        
        # Test 9: Edit chore
        print("\nTest 9: Edit Chore")
        try:
            update_data = {
                "title": f"Clean Living Room UPDATED {TEST_TIMESTAMP}",
                "description": "Vacuum, dust, and organize the living room",
                "reward": 6.00
            }
            response = await client.put(
                f"{API_BASE_URL}/chores/{unassigned_chore['id']}",
                json=update_data,
                headers={"Authorization": f"Bearer {parent_token}"}
            )
            if response.status_code == 200:
                print_test_result("Edit Chore", True, "Successfully updated chore")
            else:
                print_test_result("Edit Chore", False, f"Status: {response.status_code}")
        except Exception as e:
            print_test_result("Edit Chore", False, str(e))
        
        # Test 10: Assign unassigned chore
        print("\nTest 10: Assign Unassigned Chore")
        try:
            response = await client.post(
                f"{API_BASE_URL}/chores/{unassigned_chore['id']}/assign",
                json={"assignee_id": child_ids[1]},
                headers={"Authorization": f"Bearer {parent_token}"}
            )
            if response.status_code == 200:
                print_test_result("Assign Unassigned Chore", True, 
                                f"Assigned to child {child_ids[1]}")
            else:
                print_test_result("Assign Unassigned Chore", False, f"Status: {response.status_code}")
        except Exception as e:
            print_test_result("Assign Unassigned Chore", False, str(e))
        
        # ========== SECTION 4: CHILD COMPLETION FLOW ==========
        print_section("SECTION 4: CHILD COMPLETION FLOW")
        
        # Test 11: Child login
        print("\nTest 11: Child Authentication")
        try:
            child1_token = await login(client, CHILD1_USERNAME, CHILD1_PASSWORD)
            print_test_result("Child Authentication", True, f"Logged in as {CHILD1_USERNAME}")
        except Exception as e:
            print_test_result("Child Authentication", False, str(e))
            return
        
        # Test 12: Child completes fixed reward chore
        print("\nTest 12: Child Completes Fixed Reward Chore")
        try:
            response = await client.post(
                f"{API_BASE_URL}/chores/{fixed_chore['id']}/complete",
                headers={"Authorization": f"Bearer {child1_token}"}
            )
            if response.status_code == 200:
                print_test_result("Child Completes Fixed Chore", True, "Chore marked as completed")
            else:
                print_test_result("Child Completes Fixed Chore", False, f"Status: {response.status_code}")
        except Exception as e:
            print_test_result("Child Completes Fixed Chore", False, str(e))
        
        # Test 13: Child completes range reward chore
        print("\nTest 13: Child Completes Range Reward Chore")
        try:
            response = await client.post(
                f"{API_BASE_URL}/chores/{range_chore['id']}/complete",
                headers={"Authorization": f"Bearer {child1_token}"}
            )
            if response.status_code == 200:
                print_test_result("Child Completes Range Chore", True, "Chore marked as completed")
            else:
                print_test_result("Child Completes Range Chore", False, f"Status: {response.status_code}")
        except Exception as e:
            print_test_result("Child Completes Range Chore", False, str(e))
        
        # ========== SECTION 5: APPROVALS ==========
        print_section("SECTION 5: APPROVALS")
        
        # Test 14: Get pending approvals
        print("\nTest 14: Get Pending Approvals")
        try:
            response = await client.get(
                f"{API_BASE_URL}/chores/pending-approval",
                headers={"Authorization": f"Bearer {parent_token}"}
            )
            if response.status_code == 200:
                pending = response.json()
                print_test_result("Get Pending Approvals", len(pending) == 2, 
                                f"Found {len(pending)} chores pending approval")
            else:
                print_test_result("Get Pending Approvals", False, f"Status: {response.status_code}")
        except Exception as e:
            print_test_result("Get Pending Approvals", False, str(e))
        
        # Test 15: Approve fixed reward chore
        print("\nTest 15: Approve Fixed Reward Chore")
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
                print_test_result("Approve Fixed Reward", False, f"Status: {response.status_code}")
        except Exception as e:
            print_test_result("Approve Fixed Reward", False, str(e))
        
        # Test 16: Approve range reward chore
        print("\nTest 16: Approve Range Reward Chore")
        try:
            reward_value = 7.50  # Between min and max
            response = await client.post(
                f"{API_BASE_URL}/chores/{range_chore['id']}/approve",
                json={"reward_value": reward_value},
                headers={"Authorization": f"Bearer {parent_token}"}
            )
            if response.status_code == 200:
                print_test_result("Approve Range Reward", True, 
                                f"Approved for ${reward_value}")
            else:
                print_test_result("Approve Range Reward", False, f"Status: {response.status_code}")
        except Exception as e:
            print_test_result("Approve Range Reward", False, str(e))
        
        # ========== SECTION 6: ADJUSTMENTS ==========
        print_section("SECTION 6: ADJUSTMENTS")
        
        # Test 17: Create bonus adjustment
        print("\nTest 17: Create Bonus Adjustment")
        try:
            adjustment_data = {
                "child_id": child_ids[0],
                "amount": 15.00,
                "reason": "Bonus for excellent behavior and helping with extra tasks"
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
                print_test_result("Create Bonus Adjustment", False, f"Status: {response.status_code}")
        except Exception as e:
            print_test_result("Create Bonus Adjustment", False, str(e))
        
        # Test 18: Create deduction adjustment
        print("\nTest 18: Create Deduction Adjustment")
        try:
            adjustment_data = {
                "child_id": child_ids[0],
                "amount": -5.00,
                "reason": "Deduction for not completing homework on time"
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
                print_test_result("Create Deduction Adjustment", False, f"Status: {response.status_code}")
        except Exception as e:
            print_test_result("Create Deduction Adjustment", False, str(e))
        
        # Test 19: View adjustment history
        print("\nTest 19: View Adjustment History")
        try:
            response = await client.get(
                f"{API_BASE_URL}/adjustments/child/{child_ids[0]}",
                headers={"Authorization": f"Bearer {parent_token}"}
            )
            if response.status_code == 200:
                adjustments = response.json()
                print_test_result("View Adjustment History", len(adjustments) == 2, 
                                f"Found {len(adjustments)} adjustments")
            else:
                print_test_result("View Adjustment History", False, f"Status: {response.status_code}")
        except Exception as e:
            print_test_result("View Adjustment History", False, str(e))
        
        # ========== SECTION 7: BALANCE VERIFICATION ==========
        print_section("SECTION 7: BALANCE VERIFICATION")
        
        # Test 20: Check child balance
        print("\nTest 20: Verify Child Balance")
        try:
            response = await client.get(
                f"{API_BASE_URL}/users/me/balance",
                headers={"Authorization": f"Bearer {child1_token}"}
            )
            if response.status_code == 200:
                balance_data = response.json()
                expected_balance = 3.50 + 7.50 + 15.00 - 5.00  # Fixed + Range + Bonus - Deduction
                actual_balance = balance_data.get('balance', 0)
                
                # Allow small floating point differences
                balance_matches = abs(actual_balance - expected_balance) < 0.01
                
                print_test_result("Verify Child Balance", balance_matches, 
                                f"Balance: ${actual_balance:.2f} (Expected: ${expected_balance:.2f})")
                
                # Show balance breakdown
                print(f"  Breakdown:")
                print(f"    Earned: ${balance_data.get('total_earned', 0):.2f}")
                print(f"    Adjustments: ${balance_data.get('adjustments', 0):.2f}")
                print(f"    Paid Out: ${balance_data.get('paid_out', 0):.2f}")
            else:
                print_test_result("Verify Child Balance", False, f"Status: {response.status_code}")
        except Exception as e:
            print_test_result("Verify Child Balance", False, str(e))
        
        # ========== SECTION 8: ADVANCED FEATURES ==========
        print_section("SECTION 8: ADVANCED FEATURES")
        
        # Test 21: Create recurring chore
        print("\nTest 21: Create Recurring Chore")
        try:
            chore_data = {
                "title": f"Daily Room Cleaning {TEST_TIMESTAMP}",
                "description": "Keep room tidy every day",
                "reward": 2.00,
                "assignee_id": child_ids[1],
                "is_recurring": True,
                "recurrence_pattern": "daily"
            }
            response = await client.post(
                f"{API_BASE_URL}/chores/",
                json=chore_data,
                headers={"Authorization": f"Bearer {parent_token}"}
            )
            if response.status_code == 201:
                recurring_chore = response.json()
                print_test_result("Create Recurring Chore", True, 
                                f"Created recurring chore ID: {recurring_chore['id']}")
            else:
                print_test_result("Create Recurring Chore", False, f"Status: {response.status_code}")
        except Exception as e:
            print_test_result("Create Recurring Chore", False, str(e))
        
        # Test 22: Bulk assign chores
        print("\nTest 22: Bulk Assign Chores")
        try:
            # First create some unassigned chores
            chore_ids = []
            for i in range(3):
                chore_data = {
                    "title": f"Bulk Chore {i+1} {TEST_TIMESTAMP}",
                    "description": f"Test bulk assignment chore {i+1}",
                    "reward": 2.50,
                    "is_recurring": False
                }
                response = await client.post(
                    f"{API_BASE_URL}/chores/",
                    json=chore_data,
                    headers={"Authorization": f"Bearer {parent_token}"}
                )
                if response.status_code == 201:
                    chore_ids.append(response.json()["id"])
            
            # Now bulk assign them
            bulk_data = {
                "chore_ids": chore_ids,
                "assignee_id": child_ids[1]
            }
            response = await client.post(
                f"{API_BASE_URL}/chores/bulk-assign",
                json=bulk_data,
                headers={"Authorization": f"Bearer {parent_token}"}
            )
            if response.status_code == 200:
                result = response.json()
                print_test_result("Bulk Assign Chores", True, 
                                f"Assigned {len(chore_ids)} chores to child")
            else:
                print_test_result("Bulk Assign Chores", False, f"Status: {response.status_code}")
        except Exception as e:
            print_test_result("Bulk Assign Chores", False, str(e))
        
        # Test 23: Filter chores by status
        print("\nTest 23: Filter Chores by Status")
        try:
            # Get active chores
            response = await client.get(
                f"{API_BASE_URL}/chores/?status=active",
                headers={"Authorization": f"Bearer {parent_token}"}
            )
            if response.status_code == 200:
                active_chores = response.json()
                
                # Get completed chores
                response = await client.get(
                    f"{API_BASE_URL}/chores/?status=completed",
                    headers={"Authorization": f"Bearer {parent_token}"}
                )
                completed_chores = response.json() if response.status_code == 200 else []
                
                print_test_result("Filter Chores by Status", True, 
                                f"Active: {len(active_chores)}, Completed: {len(completed_chores)}")
            else:
                print_test_result("Filter Chores by Status", False, f"Status: {response.status_code}")
        except Exception as e:
            print_test_result("Filter Chores by Status", False, str(e))
        
        # Test 24: Delete/disable chore
        print("\nTest 24: Disable Chore")
        try:
            response = await client.delete(
                f"{API_BASE_URL}/chores/{chore_ids[0]}",
                headers={"Authorization": f"Bearer {parent_token}"}
            )
            if response.status_code in [200, 204]:
                print_test_result("Disable Chore", True, "Successfully disabled chore")
            else:
                print_test_result("Disable Chore", False, f"Status: {response.status_code}")
        except Exception as e:
            print_test_result("Disable Chore", False, str(e))

def print_summary():
    """Print comprehensive test summary"""
    print_section("TEST SUMMARY")
    
    passed_count = sum(1 for _, passed in test_results if passed)
    total_count = len(test_results)
    
    # Group tests by section
    sections = {
        "Registration & Auth": test_results[0:3],
        "Children Management": test_results[3:5],
        "Chore Management": test_results[5:10],
        "Child Completion": test_results[10:13],
        "Approvals": test_results[13:16],
        "Adjustments": test_results[16:19],
        "Balance": test_results[19:20],
        "Advanced Features": test_results[20:24] if len(test_results) >= 24 else test_results[20:]
    }
    
    print("\nResults by Section:")
    for section_name, section_tests in sections.items():
        if section_tests:
            section_passed = sum(1 for _, passed in section_tests if passed)
            section_total = len(section_tests)
            status = "✅" if section_passed == section_total else "⚠️"
            print(f"{status} {section_name}: {section_passed}/{section_total}")
    
    print("\nDetailed Results:")
    for test_name, passed in test_results:
        status = "✅" if passed else "❌"
        print(f"{status} {test_name}")
        if not passed and test_name in test_details:
            print(f"    → {test_details[test_name]}")
    
    print(f"\n{'='*60}")
    print(f"OVERALL: {passed_count}/{total_count} tests passed ({(passed_count/total_count*100):.1f}%)")
    print('='*60)
    
    if passed_count == total_count:
        print("\n🎉 PERFECT SCORE! All parent flow features are working correctly!")
        print("Phase 4.5 Parent Flow Acceptance is COMPLETE! ✅")
    elif passed_count >= total_count * 0.9:
        print(f"\n✅ EXCELLENT! {(passed_count/total_count*100):.1f}% of tests passing.")
        print("Parent flow is production-ready with minor issues to address.")
    elif passed_count >= total_count * 0.75:
        print(f"\n⚠️ GOOD PROGRESS! {(passed_count/total_count*100):.1f}% of tests passing.")
        print("Core functionality works but some features need attention.")
    else:
        print(f"\n❌ NEEDS WORK: Only {(passed_count/total_count*100):.1f}% of tests passing.")
        print("Please review the failures above before proceeding.")

if __name__ == "__main__":
    print("Starting Phase 4.5 Parent Flow E2E Tests...")
    print("Make sure the backend is running with: docker-compose up")
    print("")
    
    asyncio.run(run_parent_journey())
    print_summary()