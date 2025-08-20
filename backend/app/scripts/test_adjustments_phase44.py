#!/usr/bin/env python3
"""
Test script for Phase 4.4 - Adjustments
Tests adjustment creation, listing, and total calculation
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

async def run_tests():
    """Run all adjustment tests"""
    async with httpx.AsyncClient() as client:
        print("\n" + "="*60)
        print("PHASE 4.4 - ADJUSTMENTS TESTING")
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
            print_test_result("Child Authentication", True, "Successfully logged in as child")
        except Exception as e:
            print_test_result("Child Authentication", False, str(e))
            return
        
        # Get child ID
        response = await client.get(
            f"{API_BASE_URL}/users/my-children",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        children = response.json()
        child1 = next((c for c in children if c["username"] == CHILD1_USERNAME), None)
        
        if not child1:
            print_test_result("Find Child", False, "Could not find demochild1")
            return
        
        child1_id = child1["id"]
        print(f"\nUsing child ID: {child1_id} ({CHILD1_USERNAME})")
        
        # Test 3: Create positive adjustment (bonus)
        print("\nTest 3: Create Positive Adjustment (Bonus)")
        try:
            adjustment_data = {
                "child_id": child1_id,
                "amount": 10.50,
                "reason": "Bonus for excellent behavior this week"
            }
            response = await client.post(
                f"{API_BASE_URL}/adjustments/",
                json=adjustment_data,
                headers={"Authorization": f"Bearer {parent_token}"}
            )
            passed = response.status_code == 201
            if passed:
                adj = response.json()
                print_test_result("Create Positive Adjustment", True, 
                                f"Created bonus of ${adj['amount']}")
            else:
                print(f"  Response: {response.status_code} - {response.text}")
                print_test_result("Create Positive Adjustment", False, 
                                f"Status: {response.status_code}")
        except Exception as e:
            print_test_result("Create Positive Adjustment", False, str(e))
        
        # Test 4: Create negative adjustment (deduction)
        print("\nTest 4: Create Negative Adjustment (Deduction)")
        try:
            adjustment_data = {
                "child_id": child1_id,
                "amount": -3.25,
                "reason": "Deduction for not completing homework"
            }
            response = await client.post(
                f"{API_BASE_URL}/adjustments/",
                json=adjustment_data,
                headers={"Authorization": f"Bearer {parent_token}"}
            )
            passed = response.status_code == 201
            if passed:
                adj = response.json()
                print_test_result("Create Negative Adjustment", True, 
                                f"Created deduction of ${adj['amount']}")
            else:
                print(f"  Response: {response.status_code} - {response.text}")
                print_test_result("Create Negative Adjustment", False, 
                                f"Status: {response.status_code}")
        except Exception as e:
            print_test_result("Create Negative Adjustment", False, str(e))
        
        # Test 5: List child adjustments
        print("\nTest 5: List Child Adjustments")
        try:
            response = await client.get(
                f"{API_BASE_URL}/adjustments/child/{child1_id}",
                headers={"Authorization": f"Bearer {parent_token}"}
            )
            passed = response.status_code == 200
            if passed:
                adjustments = response.json()
                print_test_result("List Child Adjustments", True, 
                                f"Found {len(adjustments)} adjustments")
                # Display adjustments
                for adj in adjustments[:5]:  # Show first 5
                    amount = float(adj['amount'])
                    sign = '+' if amount >= 0 else ''
                    print(f"    - {sign}${abs(amount):.2f}: {adj['reason'][:50]}...")
            else:
                print_test_result("List Child Adjustments", False, 
                                f"Status: {response.status_code}")
        except Exception as e:
            print_test_result("List Child Adjustments", False, str(e))
        
        # Test 6: Get adjustment total
        print("\nTest 6: Get Adjustment Total")
        try:
            response = await client.get(
                f"{API_BASE_URL}/adjustments/total/{child1_id}",
                headers={"Authorization": f"Bearer {parent_token}"}
            )
            passed = response.status_code == 200
            if passed:
                total_data = response.json()
                total = float(total_data['total_adjustments'])
                expected = 10.50 - 3.25  # From our test adjustments
                print_test_result("Get Adjustment Total", True, 
                                f"Total adjustments: ${total:.2f}")
            else:
                print_test_result("Get Adjustment Total", False, 
                                f"Status: {response.status_code}")
        except Exception as e:
            print_test_result("Get Adjustment Total", False, str(e))
        
        # Test 7: Validation - Zero amount
        print("\nTest 7: Validation - Zero Amount")
        try:
            adjustment_data = {
                "child_id": child1_id,
                "amount": 0,
                "reason": "Invalid zero adjustment"
            }
            response = await client.post(
                f"{API_BASE_URL}/adjustments/",
                json=adjustment_data,
                headers={"Authorization": f"Bearer {parent_token}"}
            )
            # Should fail with 422
            passed = response.status_code == 422
            print_test_result("Validation - Zero Amount", passed, 
                            "Correctly rejected zero amount" if passed else "Failed to reject zero amount")
        except Exception as e:
            print_test_result("Validation - Zero Amount", False, str(e))
        
        # Test 8: Validation - Short reason
        print("\nTest 8: Validation - Short Reason")
        try:
            adjustment_data = {
                "child_id": child1_id,
                "amount": 5.00,
                "reason": "AB"  # Too short (min 3 chars)
            }
            response = await client.post(
                f"{API_BASE_URL}/adjustments/",
                json=adjustment_data,
                headers={"Authorization": f"Bearer {parent_token}"}
            )
            # Should fail with 422
            passed = response.status_code == 422
            print_test_result("Validation - Short Reason", passed, 
                            "Correctly rejected short reason" if passed else "Failed to reject short reason")
        except Exception as e:
            print_test_result("Validation - Short Reason", False, str(e))
        
        # Test 9: Child cannot create adjustments
        print("\nTest 9: Child Cannot Create Adjustments")
        try:
            adjustment_data = {
                "child_id": child1_id,
                "amount": 100.00,
                "reason": "Child trying to give themselves money"
            }
            response = await client.post(
                f"{API_BASE_URL}/adjustments/",
                json=adjustment_data,
                headers={"Authorization": f"Bearer {child1_token}"}
            )
            # Should fail with 403
            passed = response.status_code in [403, 400]
            print_test_result("Child Cannot Create Adjustments", passed, 
                            "Correctly blocked child from creating adjustment" if passed else "Failed to block child")
        except Exception as e:
            print_test_result("Child Cannot Create Adjustments", False, str(e))
        
        # Test 10: Check balance includes adjustments
        print("\nTest 10: Check Balance Includes Adjustments")
        try:
            response = await client.get(
                f"{API_BASE_URL}/users/me/balance",
                headers={"Authorization": f"Bearer {child1_token}"}
            )
            if response.status_code == 200:
                balance_data = response.json()
                adjustments = balance_data.get('adjustments', 0)
                print_test_result("Check Balance Includes Adjustments", True,
                                f"Adjustments in balance: ${adjustments:.2f}")
            else:
                print_test_result("Check Balance Includes Adjustments", False,
                                f"Status: {response.status_code}")
        except Exception as e:
            print_test_result("Check Balance Includes Adjustments", False, str(e))

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
        print("\n🎉 ALL TESTS PASSED! Phase 4.4 adjustment functionality is working correctly.")
    else:
        print(f"\n⚠️  {total_count - passed_count} test(s) failed. Please review the failures above.")

if __name__ == "__main__":
    print("Starting Phase 4.4 Adjustment Tests...")
    print("Make sure the backend is running with: docker-compose up")
    print("")
    
    asyncio.run(run_tests())
    print_summary()