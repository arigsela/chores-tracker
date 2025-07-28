#!/usr/bin/env python3
"""Test script for v2 API endpoints."""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_v2_endpoints():
    """Test the v2 API endpoints."""
    print("Testing v2 API endpoints...")
    print("-" * 50)
    
    # Test 1: Register a parent user
    print("\n1. Testing parent registration...")
    parent_data = {
        "username": f"testparent_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "password": "TestPassword123",
        "email": f"testparent_{datetime.now().strftime('%Y%m%d%H%M%S')}@example.com",
        "is_parent": True
    }
    
    response = requests.post(f"{BASE_URL}/api/v2/users/register", json=parent_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code != 201:
        print("Failed to register parent!")
        return
    
    # Test 2: Login with the parent account
    print("\n2. Testing login...")
    login_data = {
        "username": parent_data["username"],
        "password": parent_data["password"]
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v2/auth/login",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code != 200:
        print("Failed to login!")
        return
    
    token = response.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 3: Get current user
    print("\n3. Testing get current user...")
    response = requests.get(f"{BASE_URL}/api/v2/users/me", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Test 4: Register a child user
    print("\n4. Testing child registration...")
    child_data = {
        "username": f"testchild_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "password": "ChildPass123",
        "is_parent": False
    }
    
    response = requests.post(f"{BASE_URL}/api/v2/users/register", json=child_data, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code != 201:
        print("Failed to register child!")
        return
    
    child_id = response.json()["data"]["id"]
    
    # Test 5: Create a chore
    print("\n5. Testing chore creation...")
    chore_data = {
        "title": "Test Chore",
        "description": "This is a test chore",
        "assignee_id": child_id,
        "reward": 5.0,
        "is_range_reward": False,
        "cooldown_days": 0,
        "recurrence_type": "none"
    }
    
    response = requests.post(f"{BASE_URL}/api/v2/chores/", json=chore_data, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Test 6: Get chores list
    print("\n6. Testing get chores...")
    response = requests.get(f"{BASE_URL}/api/v2/chores/", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Test 7: Get chore statistics
    print("\n7. Testing chore statistics...")
    response = requests.get(f"{BASE_URL}/api/v2/chores/stats/summary", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    print("\n" + "-" * 50)
    print("v2 API testing complete!")

if __name__ == "__main__":
    test_v2_endpoints()