#!/usr/bin/env python3
"""
Create test users for E2E testing
"""
import json
import urllib.request
import urllib.parse
from datetime import datetime

API_BASE_URL = "http://localhost:8000/api/v1"

# Generate unique usernames
timestamp = datetime.now().strftime("%H%M%S")
PARENT_USERNAME = f"test_parent_{timestamp}"
PARENT_PASSWORD = "TestPass123!"
CHILD_USERNAME = f"test_child_{timestamp}"
CHILD_PASSWORD = "ChildPass123!"

def make_request(url, method="GET", data=None, headers=None):
    """Make HTTP request"""
    if headers is None:
        headers = {}
    
    request = urllib.request.Request(url, method=method)
    
    if data:
        if isinstance(data, dict):
            if headers.get("Content-Type") == "application/x-www-form-urlencoded":
                data = urllib.parse.urlencode(data).encode()
            else:
                headers["Content-Type"] = "application/json"
                data = json.dumps(data).encode()
        request.data = data
    
    for key, value in headers.items():
        request.add_header(key, value)
    
    try:
        response = urllib.request.urlopen(request)
        content = response.read().decode()
        return response.code, json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        error_content = e.read().decode()
        try:
            error_json = json.loads(error_content)
        except:
            error_json = {"detail": error_content}
        return e.code, error_json

# Create parent user
print(f"Creating parent user: {PARENT_USERNAME}")
parent_data = {
    "username": PARENT_USERNAME,
    "password": PARENT_PASSWORD,
    "email": f"{PARENT_USERNAME}@test.com",
    "is_parent": True
}

status, response = make_request(
    f"{API_BASE_URL}/users/register",
    method="POST",
    data=parent_data
)

if status == 200:
    parent_id = response["id"]
    print(f"✅ Parent created: {PARENT_USERNAME} (ID: {parent_id})")
    
    # Login as parent
    login_data = {
        "username": PARENT_USERNAME,
        "password": PARENT_PASSWORD
    }
    
    status, response = make_request(
        f"{API_BASE_URL}/users/login",
        method="POST",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if status == 200:
        parent_token = response["access_token"]
        print(f"✅ Parent logged in successfully")
        
        # Create child user
        print(f"Creating child user: {CHILD_USERNAME}")
        child_data = {
            "username": CHILD_USERNAME,
            "password": CHILD_PASSWORD,
            "email": f"{CHILD_USERNAME}@test.com",
            "is_parent": False,
            "parent_id": parent_id
        }
        
        status, response = make_request(
            f"{API_BASE_URL}/users/",
            method="POST",
            data=child_data,
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        if status == 200:
            child_id = response["id"]
            print(f"✅ Child created: {CHILD_USERNAME} (ID: {child_id})")
            
            # Create some test chores
            print("\nCreating test chores...")
            
            # Fixed reward chore
            chore1 = {
                "name": "Clean Room",
                "description": "Clean and organize bedroom",
                "reward_type": "fixed",
                "reward_amount": 5.00,
                "assignee_id": child_id,
                "is_active": True,
                "is_recurring": False
            }
            
            status, response = make_request(
                f"{API_BASE_URL}/chores/",
                method="POST",
                data=chore1,
                headers={"Authorization": f"Bearer {parent_token}"}
            )
            
            if status == 200:
                print(f"✅ Fixed chore created: Clean Room ($5.00)")
            
            # Range reward chore
            chore2 = {
                "name": "Wash Dishes",
                "description": "Wash and dry all dishes",
                "reward_type": "range",
                "reward_min": 3.00,
                "reward_max": 8.00,
                "assignee_id": child_id,
                "is_active": True,
                "is_recurring": False
            }
            
            status, response = make_request(
                f"{API_BASE_URL}/chores/",
                method="POST",
                data=chore2,
                headers={"Authorization": f"Bearer {parent_token}"}
            )
            
            if status == 200:
                print(f"✅ Range chore created: Wash Dishes ($3-$8)")
                
            print(f"\n" + "="*60)
            print("TEST USERS CREATED SUCCESSFULLY!")
            print("="*60)
            print(f"Parent: {PARENT_USERNAME} / {PARENT_PASSWORD}")
            print(f"Child: {CHILD_USERNAME} / {CHILD_PASSWORD}")
            print("="*60)
            
            # Save to file for reference
            with open('/tmp/test_credentials.txt', 'w') as f:
                f.write(f"PARENT: {PARENT_USERNAME} / {PARENT_PASSWORD}\n")
                f.write(f"CHILD: {CHILD_USERNAME} / {CHILD_PASSWORD}\n")
                f.write(f"PARENT_ID: {parent_id}\n")
                f.write(f"CHILD_ID: {child_id}\n")
            print("\nCredentials saved to /tmp/test_credentials.txt")
            
        else:
            print(f"❌ Failed to create child: {response}")
    else:
        print(f"❌ Failed to login parent: {response}")
else:
    print(f"❌ Failed to create parent: {response}")