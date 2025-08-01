#!/usr/bin/env python3
"""Test adjustment form integration in allowance summary."""

import asyncio
import sys
import httpx
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

BASE_URL = "http://localhost:8000"
USERNAME = "testparent"
PASSWORD = "password123"


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


async def test_allowance_summary_integration():
    """Test that the adjustment button appears in allowance summary."""
    token = await login()
    if not token:
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient() as client:
        # Get allowance summary HTML
        print("\n1. Testing allowance summary with adjustment button...")
        response = await client.get(
            f"{BASE_URL}/api/v1/users/summary",
            headers=headers
        )
        
        if response.status_code == 200:
            html_content = response.text
            
            # Check for adjustment button
            if "adjust-btn-" in html_content:
                print("✓ Adjustment button found in allowance summary")
            else:
                print("✗ Adjustment button NOT found in allowance summary")
            
            # Check for JavaScript function
            if "showAdjustmentForm" in html_content:
                print("✓ JavaScript function found")
            else:
                print("✗ JavaScript function NOT found")
            
            # Check for purple styling
            if "bg-purple-500" in html_content:
                print("✓ Purple styling found for adjustment button")
            else:
                print("✗ Purple styling NOT found")
            
            # Check for refresh-summary event listener
            if "refresh-summary" in html_content:
                print("✓ Refresh event listener found")
            else:
                print("✗ Refresh event listener NOT found")
            
            # Save the HTML to a file for manual inspection
            with open("/tmp/allowance_summary_test.html", "w") as f:
                f.write(html_content)
            print(f"\n✓ Saved HTML to /tmp/allowance_summary_test.html for inspection")
            
        else:
            print(f"✗ Failed to get allowance summary: {response.status_code}")
            print(response.text)
        
        # Test dashboard page loads correctly
        print("\n2. Testing dashboard page...")
        response = await client.get(
            f"{BASE_URL}/pages/dashboard",
            headers=headers
        )
        
        if response.status_code == 200:
            print("✓ Dashboard page loaded successfully")
            
            # Check if allowance summary section exists
            if "allowance-summary" in response.text:
                print("✓ Allowance summary section found in dashboard")
            else:
                print("✗ Allowance summary section NOT found in dashboard")
        else:
            print(f"✗ Failed to load dashboard: {response.status_code}")


async def main():
    """Run all tests."""
    print("Testing Adjustment Integration in Allowance Summary")
    print("=" * 50)
    
    await test_allowance_summary_integration()
    
    print("\n" + "=" * 50)
    print("Integration test complete!")
    print("\nNote: The HTML endpoint for inline form will be created in Phase 4.3")


if __name__ == "__main__":
    asyncio.run(main())