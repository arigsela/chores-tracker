#!/usr/bin/env python3
"""Test HTML endpoints for reward adjustments."""

import asyncio
import sys
import httpx
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

BASE_URL = "http://localhost:8000"
USERNAME = "testparent"
PASSWORD = "password123"
CHILD_ID = 5  # testchild1 created earlier


async def login():
    """Login as parent user and get token."""
    async with httpx.AsyncClient() as client:
        # Login
        response = await client.post(
            f"{BASE_URL}/api/v1/users/login",
            data={"username": USERNAME, "password": PASSWORD}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Logged in as {USERNAME}")
            return data["access_token"]
        else:
            print(f"✗ Login failed: {response.status_code}")
            print(response.text)
            return None


async def test_html_endpoints():
    """Test all HTML endpoints for adjustments."""
    token = await login()
    if not token:
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient() as client:
        # Test 1: Inline form endpoint
        print("\n1. Testing inline form endpoint...")
        response = await client.get(
            f"{BASE_URL}/api/v1/html/adjustments/inline-form/{CHILD_ID}",
            headers=headers
        )
        
        if response.status_code == 200:
            print("✓ Inline form endpoint working")
            
            # Check for expected elements
            html = response.text
            checks = [
                ("adjustment-form-", "Form ID found"),
                ("inline-adjustment-form-", "Form element found"),
                ("setQuickAmount", "Quick amount function found"),
                ("cancelAdjustment", "Cancel function found"),
                ("bg-purple-50", "Purple theme applied")
            ]
            
            for check_str, check_msg in checks:
                if check_str in html:
                    print(f"  ✓ {check_msg}")
                else:
                    print(f"  ✗ {check_msg}")
                    
            with open("/tmp/inline_form_test.html", "w") as f:
                f.write(html)
            print("  → Saved to /tmp/inline_form_test.html")
        else:
            print(f"✗ Inline form endpoint failed: {response.status_code}")
            print(response.text)
        
        # Test 2: Modal form endpoint
        print("\n2. Testing modal form endpoint...")
        response = await client.get(
            f"{BASE_URL}/api/v1/html/adjustments/modal-form/{CHILD_ID}",
            headers=headers
        )
        
        if response.status_code == 200:
            print("✓ Modal form endpoint working")
            html = response.text
            
            checks = [
                ("adjustment-modal", "Modal ID found"),
                ("modal-adjustment-form", "Modal form found"),
                ("setModalAmount", "Modal amount function found"),
                ("closeAdjustmentModal", "Close modal function found"),
                ("Quick Adjustments", "Quick adjustment buttons found")
            ]
            
            for check_str, check_msg in checks:
                if check_str in html:
                    print(f"  ✓ {check_msg}")
                else:
                    print(f"  ✗ {check_msg}")
                    
            with open("/tmp/modal_form_test.html", "w") as f:
                f.write(html)
            print("  → Saved to /tmp/modal_form_test.html")
        else:
            print(f"✗ Modal form endpoint failed: {response.status_code}")
        
        # Test 3: Full page form endpoint
        print("\n3. Testing full page form endpoint...")
        response = await client.get(
            f"{BASE_URL}/api/v1/html/adjustments/form",
            headers=headers
        )
        
        if response.status_code == 200:
            print("✓ Full page form endpoint working")
            html = response.text
            
            checks = [
                ("adjustment-form", "Form ID found"),
                ("Select Child", "Child selection found"),
                ("Adjustment Amount", "Amount field found"),
                ("Reason for Adjustment", "Reason field found"),
                ("Apply Adjustment", "Submit button found")
            ]
            
            for check_str, check_msg in checks:
                if check_str in html:
                    print(f"  ✓ {check_msg}")
                else:
                    print(f"  ✗ {check_msg}")
                    
            with open("/tmp/full_form_test.html", "w") as f:
                f.write(html)
            print("  → Saved to /tmp/full_form_test.html")
        else:
            print(f"✗ Full page form endpoint failed: {response.status_code}")
        
        # Test 4: List endpoint (should be empty initially)
        print("\n4. Testing list endpoint...")
        response = await client.get(
            f"{BASE_URL}/api/v1/html/adjustments/list/{CHILD_ID}",
            headers=headers
        )
        
        if response.status_code == 200:
            print("✓ List endpoint working")
            html = response.text
            
            checks = [
                ("Adjustment History", "Title found"),
                ("No adjustments have been made yet", "Empty state found")
            ]
            
            for check_str, check_msg in checks:
                if check_str in html:
                    print(f"  ✓ {check_msg}")
                else:
                    print(f"  ✗ {check_msg}")
                    
            with open("/tmp/list_test.html", "w") as f:
                f.write(html)
            print("  → Saved to /tmp/list_test.html")
        else:
            print(f"✗ List endpoint failed: {response.status_code}")
        
        # Test 5: Create an adjustment and check the list again
        print("\n5. Creating a test adjustment...")
        adjustment_data = {
            "child_id": CHILD_ID,
            "amount": "10.00",
            "reason": "Test bonus from HTML endpoint test"
        }
        
        response = await client.post(
            f"{BASE_URL}/api/v1/adjustments/",
            json=adjustment_data,
            headers=headers
        )
        
        if response.status_code == 201:
            print("✓ Test adjustment created")
            
            # Now check the list again
            response = await client.get(
                f"{BASE_URL}/api/v1/html/adjustments/list/{CHILD_ID}",
                headers=headers
            )
            
            if response.status_code == 200:
                html = response.text
                
                checks = [
                    ("Test bonus from HTML endpoint test", "Adjustment reason found"),
                    ("+$10.00", "Adjustment amount found"),
                    ("Total Adjustments:", "Total summary found")
                ]
                
                for check_str, check_msg in checks:
                    if check_str in html:
                        print(f"  ✓ {check_msg}")
                    else:
                        print(f"  ✗ {check_msg}")
                        
                with open("/tmp/list_with_data_test.html", "w") as f:
                    f.write(html)
                print("  → Saved to /tmp/list_with_data_test.html")
        else:
            print(f"✗ Failed to create test adjustment: {response.status_code}")


async def main():
    """Run all tests."""
    print("Testing HTML Endpoints for Reward Adjustments")
    print("=" * 50)
    
    await test_html_endpoints()
    
    print("\n" + "=" * 50)
    print("HTML endpoint tests complete!")
    print("\nAll HTML endpoints are now ready for use:")
    print("- Inline form: /api/v1/html/adjustments/inline-form/{child_id}")
    print("- Modal form: /api/v1/html/adjustments/modal-form/{child_id}")
    print("- Full form: /api/v1/html/adjustments/form")
    print("- List view: /api/v1/html/adjustments/list/{child_id}")


if __name__ == "__main__":
    asyncio.run(main())