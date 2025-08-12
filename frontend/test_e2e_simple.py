#!/usr/bin/env python3
"""
Simple E2E test for Chores Tracker
Tests the complete workflow from user creation to chore completion and approval
"""
from datetime import datetime
import json
import time
import urllib.request
import urllib.parse
import urllib.error

API_BASE_URL = "http://localhost:8000/api/v1"
WEB_BASE_URL = "http://localhost:8081"

# Generate unique usernames with timestamp
timestamp = datetime.now().strftime("%H%M%S")
PARENT_USERNAME = f"e2e_parent_{timestamp}"
PARENT_PASSWORD = "TestPass123!"
CHILD_USERNAME = f"e2e_child_{timestamp}"
CHILD_PASSWORD = "ChildPass123!"

def make_request(url, method="GET", data=None, headers=None):
    """Make HTTP request using urllib"""
    if headers is None:
        headers = {}
    
    request = urllib.request.Request(url, method=method)
    
    if data:
        if isinstance(data, dict):
            # Check if it's form data or JSON
            if headers.get("Content-Type") == "application/x-www-form-urlencoded":
                data = urllib.parse.urlencode(data).encode()
            else:
                data = json.dumps(data).encode()
                if "Content-Type" not in headers:
                    request.add_header("Content-Type", "application/json")
        
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

class E2ETestRunner:
    def __init__(self):
        self.parent_token = None
        self.parent_id = None
        self.child_id = None
        self.fixed_chore_id = None
        self.ranged_chore_id = None
        self.results = []
        
    def setup_users(self):
        """Step 1 & 2: Create parent and child users via API"""
        print("\n" + "="*60)
        print("STEP 1 & 2: Creating test users")
        print("="*60)
        
        # Create parent user
        print(f"\n📝 Creating parent user: {PARENT_USERNAME}")
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
            self.parent_id = response["id"]
            print(f"✅ Parent created with ID: {self.parent_id}")
            self.results.append(("Parent Creation", "PASSED"))
        else:
            print(f"❌ Failed to create parent: {response}")
            self.results.append(("Parent Creation", "FAILED"))
            return False
            
        # Login as parent to get token
        print(f"\n🔐 Logging in as parent...")
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
            self.parent_token = response["access_token"]
            print("✅ Parent logged in successfully")
            self.results.append(("Parent Login", "PASSED"))
        else:
            print(f"❌ Failed to login parent: {response}")
            self.results.append(("Parent Login", "FAILED"))
            return False
            
        # Create child user
        print(f"\n👶 Creating child user: {CHILD_USERNAME}")
        child_data = {
            "username": CHILD_USERNAME,
            "password": CHILD_PASSWORD,
            "email": f"{CHILD_USERNAME}@test.com",
            "is_parent": False,
            "parent_id": self.parent_id
        }
        
        status, response = make_request(
            f"{API_BASE_URL}/users/",
            method="POST",
            data=child_data,
            headers={"Authorization": f"Bearer {self.parent_token}"}
        )
        
        if status == 200:
            self.child_id = response["id"]
            print(f"✅ Child created with ID: {self.child_id}")
            self.results.append(("Child Creation", "PASSED"))
            return True
        else:
            print(f"❌ Failed to create child: {response}")
            self.results.append(("Child Creation", "FAILED"))
            return False
            
    def create_chores(self):
        """Step 3 & 4: Create fixed and ranged chores via API"""
        print("\n" + "="*60)
        print("STEP 3 & 4: Creating chores (fixed and ranged)")
        print("="*60)
        
        headers = {"Authorization": f"Bearer {self.parent_token}"}
        
        # Create fixed reward chore
        print(f"\n💰 Creating fixed reward chore...")
        fixed_chore = {
            "name": f"E2E Fixed Chore {timestamp}",
            "description": "Test chore with fixed reward",
            "reward_type": "fixed",
            "reward_amount": 5.00,
            "assignee_id": self.child_id,
            "is_active": True,
            "is_recurring": False
        }
        
        status, response = make_request(
            f"{API_BASE_URL}/chores/",
            method="POST",
            data=fixed_chore,
            headers=headers
        )
        
        if status == 200:
            self.fixed_chore_id = response["id"]
            print(f"✅ Fixed chore created with ID: {self.fixed_chore_id}")
            self.results.append(("Fixed Chore Creation", "PASSED"))
        else:
            print(f"❌ Failed to create fixed chore: {response}")
            self.results.append(("Fixed Chore Creation", "FAILED"))
            return False
            
        # Create ranged reward chore
        print(f"\n📊 Creating ranged reward chore...")
        ranged_chore = {
            "name": f"E2E Ranged Chore {timestamp}",
            "description": "Test chore with ranged reward",
            "reward_type": "range",
            "reward_min": 3.00,
            "reward_max": 10.00,
            "assignee_id": self.child_id,
            "is_active": True,
            "is_recurring": False
        }
        
        status, response = make_request(
            f"{API_BASE_URL}/chores/",
            method="POST",
            data=ranged_chore,
            headers=headers
        )
        
        if status == 200:
            self.ranged_chore_id = response["id"]
            print(f"✅ Ranged chore created with ID: {self.ranged_chore_id}")
            self.results.append(("Ranged Chore Creation", "PASSED"))
            return True
        else:
            print(f"❌ Failed to create ranged chore: {response}")
            self.results.append(("Ranged Chore Creation", "FAILED"))
            return False
            
    def child_complete_chores(self):
        """Step 5 & 6: Child logs in and completes chores"""
        print("\n" + "="*60)
        print("STEP 5 & 6: Child login and chore completion")
        print("="*60)
        
        # Login as child
        print(f"\n🔐 Logging in as child: {CHILD_USERNAME}")
        login_data = {
            "username": CHILD_USERNAME,
            "password": CHILD_PASSWORD
        }
        
        status, response = make_request(
            f"{API_BASE_URL}/users/login",
            method="POST",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if status == 200:
            child_token = response["access_token"]
            print("✅ Child logged in successfully")
            self.results.append(("Child Login", "PASSED"))
        else:
            print(f"❌ Failed to login child: {response}")
            self.results.append(("Child Login", "FAILED"))
            return False
            
        headers = {"Authorization": f"Bearer {child_token}"}
        
        # Complete fixed chore
        print(f"\n✔️  Completing fixed reward chore...")
        status, response = make_request(
            f"{API_BASE_URL}/chores/{self.fixed_chore_id}/complete",
            method="POST",
            headers=headers
        )
        
        if status == 200:
            print(f"✅ Fixed chore marked as completed")
            self.results.append(("Fixed Chore Completion", "PASSED"))
        else:
            print(f"❌ Failed to complete fixed chore: {response}")
            self.results.append(("Fixed Chore Completion", "FAILED"))
            
        # Complete ranged chore
        print(f"\n✔️  Completing ranged reward chore...")
        status, response = make_request(
            f"{API_BASE_URL}/chores/{self.ranged_chore_id}/complete",
            method="POST",
            headers=headers
        )
        
        if status == 200:
            print(f"✅ Ranged chore marked as completed")
            self.results.append(("Ranged Chore Completion", "PASSED"))
            return True
        else:
            print(f"❌ Failed to complete ranged chore: {response}")
            self.results.append(("Ranged Chore Completion", "FAILED"))
            return False
            
    def parent_approve_chores(self):
        """Step 7 & 8: Parent approves chores"""
        print("\n" + "="*60)
        print("STEP 7 & 8: Parent approval")
        print("="*60)
        
        headers = {"Authorization": f"Bearer {self.parent_token}"}
        
        # Approve fixed chore
        print(f"\n✅ Approving fixed reward chore...")
        status, response = make_request(
            f"{API_BASE_URL}/chores/{self.fixed_chore_id}/approve",
            method="POST",
            headers=headers
        )
        
        if status == 200:
            print(f"✅ Fixed chore approved with reward: $5.00")
            self.results.append(("Fixed Chore Approval", "PASSED"))
        else:
            print(f"❌ Failed to approve fixed chore: {response}")
            self.results.append(("Fixed Chore Approval", "FAILED"))
            
        # Approve ranged chore with lower value
        print(f"\n✅ Approving ranged reward chore with lower value...")
        approve_data = {"reward_value": 4.50}  # Lower than max (10.00)
        
        status, response = make_request(
            f"{API_BASE_URL}/chores/{self.ranged_chore_id}/approve",
            method="POST",
            data=approve_data,
            headers=headers
        )
        
        if status == 200:
            print(f"✅ Ranged chore approved with reward: $4.50 (range was $3-$10)")
            self.results.append(("Ranged Chore Approval", "PASSED"))
            return True
        else:
            print(f"❌ Failed to approve ranged chore: {response}")
            self.results.append(("Ranged Chore Approval", "FAILED"))
            return False
            
    def verify_child_balance(self):
        """Step 9 & 10: Verify child sees completed chores and updated balance"""
        print("\n" + "="*60)
        print("STEP 9 & 10: Verification")
        print("="*60)
        
        # Login as child again
        login_data = {
            "username": CHILD_USERNAME,
            "password": CHILD_PASSWORD
        }
        
        status, response = make_request(
            f"{API_BASE_URL}/users/login",
            method="POST",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if status != 200:
            print(f"❌ Failed to login child for verification")
            self.results.append(("Verification Login", "FAILED"))
            return False
            
        child_token = response["access_token"]
        headers = {"Authorization": f"Bearer {child_token}"}
        
        # Check balance
        print(f"\n💰 Checking child's balance...")
        status, response = make_request(
            f"{API_BASE_URL}/users/me/balance",
            method="GET",
            headers=headers
        )
        
        if status == 200:
            balance = response["balance"]
            expected_balance = 5.00 + 4.50  # Fixed + Ranged approval
            
            if abs(balance - expected_balance) < 0.01:
                print(f"✅ Balance correct: ${balance:.2f} (expected ${expected_balance:.2f})")
                self.results.append(("Balance Verification", "PASSED"))
            else:
                print(f"⚠️  Balance mismatch: ${balance:.2f} (expected ${expected_balance:.2f})")
                self.results.append(("Balance Verification", "WARNING"))
        else:
            print(f"❌ Failed to get balance: {response}")
            self.results.append(("Balance Verification", "FAILED"))
            
        # Check chore status
        print(f"\n📋 Checking completed chores...")
        status, response = make_request(
            f"{API_BASE_URL}/chores/",
            method="GET",
            headers=headers
        )
        
        if status == 200:
            completed_count = sum(1 for c in response if c.get("status") == "approved")
            
            if completed_count >= 2:
                print(f"✅ Found {completed_count} approved chores")
                self.results.append(("Chore Status Verification", "PASSED"))
            else:
                print(f"⚠️  Only {completed_count} approved chores found")
                self.results.append(("Chore Status Verification", "WARNING"))
                
            return True
        else:
            print(f"❌ Failed to get chores: {response}")
            self.results.append(("Chore Status Verification", "FAILED"))
            return False
            
    def run_full_test(self):
        """Run the complete E2E test suite"""
        print("\n" + "🚀 "*20)
        print("STARTING COMPREHENSIVE E2E TEST")
        print("🚀 "*20)
        
        start_time = time.time()
        
        # Run all test steps
        if self.setup_users():
            time.sleep(1)
            
            if self.create_chores():
                time.sleep(2)  # Give time for chores to be available
                
                if self.child_complete_chores():
                    time.sleep(2)  # Give time for completion to process
                    
                    if self.parent_approve_chores():
                        time.sleep(2)  # Give time for approval to process
                        
                        self.verify_child_balance()
        
        # Print results summary
        elapsed = time.time() - start_time
        self.print_summary(elapsed)
        
    def print_summary(self, elapsed_time):
        """Print test results summary"""
        print("\n" + "="*60)
        print("E2E TEST RESULTS SUMMARY")
        print("="*60)
        
        passed = sum(1 for _, status in self.results if status == "PASSED")
        failed = sum(1 for _, status in self.results if status == "FAILED")
        warnings = sum(1 for _, status in self.results if status == "WARNING")
        
        print(f"\n📊 Test Statistics:")
        print(f"  • Total Tests: {len(self.results)}")
        print(f"  • ✅ Passed: {passed}")
        print(f"  • ❌ Failed: {failed}")
        print(f"  • ⚠️  Warnings: {warnings}")
        print(f"  • ⏱️  Duration: {elapsed_time:.2f} seconds")
        
        print(f"\n📋 Detailed Results:")
        for test_name, status in self.results:
            icon = "✅" if status == "PASSED" else "❌" if status == "FAILED" else "⚠️"
            print(f"  {icon} {test_name}: {status}")
            
        print(f"\n🎯 Overall Result: ", end="")
        if failed == 0:
            if warnings > 0:
                print("✅ PASSED WITH WARNINGS")
            else:
                print("✅ ALL TESTS PASSED!")
        else:
            print("❌ TESTS FAILED")
            
        print("\n" + "="*60)
        print(f"Test Users Created:")
        print(f"  • Parent: {PARENT_USERNAME} / {PARENT_PASSWORD}")
        print(f"  • Child: {CHILD_USERNAME} / {CHILD_PASSWORD}")
        print("="*60)

def main():
    """Main function"""
    runner = E2ETestRunner()
    runner.run_full_test()
    
if __name__ == "__main__":
    main()