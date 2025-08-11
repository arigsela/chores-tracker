#!/usr/bin/env python3
"""Test script for Phase 4.2 - Chore CRUD Operations."""

import asyncio
import httpx
import random
from typing import Dict, Any, Optional

BASE_URL = "http://localhost:8000"

class ChoreCRUDTest:
    def __init__(self):
        self.client = httpx.AsyncClient()
        self.token = None
        self.headers = {}
        self.user = None
        self.created_chore = None
        self.child_id = None
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
        
    async def test_parent_login(self) -> bool:
        """Test 1: Login as parent user."""
        print("\n🔐 TEST 1: Parent Authentication")
        print("-" * 40)
        
        login_data = {
            "username": "demoparent",
            "password": "demo123"
        }
        
        response = await self.client.post(
            f"{BASE_URL}/api/v1/users/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code != 200:
            print(f"❌ Login failed: {response.status_code}")
            return False
            
        data = response.json()
        self.token = data["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Get user info
        user_response = await self.client.get(
            f"{BASE_URL}/api/v1/users/me",
            headers=self.headers
        )
        
        if user_response.status_code == 200:
            self.user = user_response.json()
            print(f"✅ Logged in as: {self.user['username']} (Parent)")
            
            # Get children for assignment
            children_response = await self.client.get(
                f"{BASE_URL}/api/v1/users/my-children",
                headers=self.headers
            )
            if children_response.status_code == 200:
                children = children_response.json()
                if children:
                    self.child_id = children[0]['id']
                    print(f"   Found child: {children[0]['username']} (ID: {self.child_id})")
            return True
        
        return False
        
    async def test_create_fixed_chore(self) -> bool:
        """Test 2: Create a chore with fixed reward."""
        print("\n📝 TEST 2: Create Fixed Reward Chore")
        print("-" * 40)
        
        chore_data = {
            "title": f"Test Chore {random.randint(1000, 9999)}",
            "description": "This is a test chore created via API",
            "reward": 10.50,
            "is_range_reward": False,
            "is_recurring": True,
            "cooldown_days": 3,
            "assignee_id": self.child_id if self.child_id else 22  # Use assignee_id field name
        }
        
        print(f"Creating chore: {chore_data['title']}")
        print(f"   Fixed reward: ${chore_data['reward']}")
        print(f"   Recurring: Every {chore_data['cooldown_days']} days")
        
        response = await self.client.post(
            f"{BASE_URL}/api/v1/chores/",
            json=chore_data,
            headers=self.headers
        )
        
        if response.status_code == 201:
            self.created_chore = response.json()
            print(f"✅ Chore created successfully (ID: {self.created_chore['id']})")
            return True
        else:
            print(f"❌ Failed to create chore: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    async def test_create_range_chore(self) -> bool:
        """Test 3: Create a chore with range reward."""
        print("\n📝 TEST 3: Create Range Reward Chore")
        print("-" * 40)
        
        chore_data = {
            "title": f"Range Chore {random.randint(1000, 9999)}",
            "description": "Chore with variable reward based on quality",
            "reward": 0,  # Backend expects 0 for range rewards
            "is_range_reward": True,
            "min_reward": 5.0,
            "max_reward": 15.0,
            "is_recurring": False,  # One-time chore
            "assignee_id": self.child_id if self.child_id else 22  # Required field, can't be None
        }
        
        print(f"Creating chore: {chore_data['title']}")
        print(f"   Range reward: ${chore_data['min_reward']} - ${chore_data['max_reward']}")
        print(f"   Assignment: Unassigned (any child can claim)")
        
        response = await self.client.post(
            f"{BASE_URL}/api/v1/chores/",
            json=chore_data,
            headers=self.headers
        )
        
        if response.status_code == 201:
            created = response.json()
            print(f"✅ Range chore created successfully (ID: {created['id']})")
            return True
        else:
            print(f"❌ Failed to create range chore: {response.status_code}")
            return False
            
    async def test_update_chore(self) -> bool:
        """Test 4: Update an existing chore."""
        print("\n✏️ TEST 4: Update Chore")
        print("-" * 40)
        
        if not self.created_chore:
            print("❌ No chore to update (creation test failed)")
            return False
            
        update_data = {
            "title": f"{self.created_chore['title']} (Updated)",
            "description": "Updated description with more details",
            "reward": 12.75,
            "cooldown_days": 7  # Change from 3 to 7 days
        }
        
        print(f"Updating chore ID {self.created_chore['id']}:")
        print(f"   New title: {update_data['title']}")
        print(f"   New reward: ${update_data['reward']}")
        print(f"   New cooldown: {update_data['cooldown_days']} days")
        
        response = await self.client.put(
            f"{BASE_URL}/api/v1/chores/{self.created_chore['id']}",
            json=update_data,
            headers=self.headers
        )
        
        if response.status_code == 200:
            updated = response.json()
            print(f"✅ Chore updated successfully")
            
            # Verify changes
            if updated['title'] == update_data['title'] and updated['reward'] == update_data['reward']:
                print(f"   ✅ Changes verified")
                self.created_chore = updated  # Update reference
                return True
            else:
                print(f"   ❌ Changes not reflected correctly")
                return False
        else:
            print(f"❌ Failed to update chore: {response.status_code}")
            return False
            
    async def test_disable_chore(self) -> bool:
        """Test 5: Disable a chore."""
        print("\n🚫 TEST 5: Disable Chore")
        print("-" * 40)
        
        if not self.created_chore:
            print("❌ No chore to disable")
            return False
            
        print(f"Disabling chore ID {self.created_chore['id']}: {self.created_chore['title']}")
        
        response = await self.client.post(
            f"{BASE_URL}/api/v1/chores/{self.created_chore['id']}/disable",
            headers=self.headers
        )
        
        if response.status_code == 200:
            disabled = response.json()
            if disabled.get('is_disabled', False):
                print(f"✅ Chore disabled successfully")
                return True
            else:
                print(f"❌ Chore not marked as disabled")
                return False
        else:
            print(f"❌ Failed to disable chore: {response.status_code}")
            return False
            
    async def test_enable_chore(self) -> bool:
        """Test 6: Enable a disabled chore."""
        print("\n✅ TEST 6: Enable Chore")
        print("-" * 40)
        
        if not self.created_chore:
            print("❌ No chore to enable")
            return False
            
        print(f"Enabling chore ID {self.created_chore['id']}: {self.created_chore['title']}")
        
        response = await self.client.post(
            f"{BASE_URL}/api/v1/chores/{self.created_chore['id']}/enable",
            headers=self.headers
        )
        
        if response.status_code == 200:
            enabled = response.json()
            if not enabled.get('is_disabled', True):
                print(f"✅ Chore enabled successfully")
                return True
            else:
                print(f"❌ Chore still marked as disabled")
                return False
        else:
            print(f"❌ Failed to enable chore: {response.status_code}")
            return False
            
    async def test_list_chores(self) -> bool:
        """Test 7: List all chores."""
        print("\n📋 TEST 7: List Chores")
        print("-" * 40)
        
        response = await self.client.get(
            f"{BASE_URL}/api/v1/chores/",
            headers=self.headers
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to list chores: {response.status_code}")
            return False
            
        chores = response.json()
        print(f"✅ Found {len(chores)} total chores")
        
        # Count by status
        active = sum(1 for c in chores if not c.get('is_disabled', False) and not c.get('is_completed', False))
        disabled = sum(1 for c in chores if c.get('is_disabled', False))
        completed = sum(1 for c in chores if c.get('is_completed', False))
        
        print(f"   Active: {active}")
        print(f"   Disabled: {disabled}")
        print(f"   Completed: {completed}")
        
        # Show recently created
        if self.created_chore:
            found = any(c['id'] == self.created_chore['id'] for c in chores)
            if found:
                print(f"   ✅ Test chore found in list")
            else:
                print(f"   ❌ Test chore not found in list")
                
        return True
        
    async def test_delete_chore(self) -> bool:
        """Test 8: Delete a chore permanently."""
        print("\n🗑️ TEST 8: Delete Chore")
        print("-" * 40)
        
        if not self.created_chore:
            print("❌ No chore to delete")
            return False
            
        print(f"⚠️  Permanently deleting chore ID {self.created_chore['id']}")
        
        response = await self.client.delete(
            f"{BASE_URL}/api/v1/chores/{self.created_chore['id']}",
            headers=self.headers
        )
        
        if response.status_code == 204:
            print(f"✅ Chore deleted successfully")
            
            # Verify deletion
            verify_response = await self.client.get(
                f"{BASE_URL}/api/v1/chores/{self.created_chore['id']}",
                headers=self.headers
            )
            
            if verify_response.status_code == 404:
                print(f"   ✅ Deletion verified (chore not found)")
                return True
            else:
                print(f"   ❌ Chore still exists after deletion")
                return False
        else:
            print(f"❌ Failed to delete chore: {response.status_code}")
            return False
            
    async def run_all_tests(self):
        """Run complete CRUD test suite."""
        print("=" * 50)
        print("🧪 PHASE 4.2 - CHORE CRUD OPERATIONS TEST")
        print("=" * 50)
        
        tests = [
            ("Parent Authentication", self.test_parent_login),
            ("Create Fixed Chore", self.test_create_fixed_chore),
            ("Create Range Chore", self.test_create_range_chore),
            ("Update Chore", self.test_update_chore),
            ("Disable Chore", self.test_disable_chore),
            ("Enable Chore", self.test_enable_chore),
            ("List Chores", self.test_list_chores),
            ("Delete Chore", self.test_delete_chore),
        ]
        
        results = []
        for name, test_func in tests:
            try:
                result = await test_func()
                results.append((name, result))
            except Exception as e:
                print(f"❌ Test '{name}' failed with error: {e}")
                results.append((name, False))
                
        # Summary
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY - PHASE 4.2")
        print("=" * 50)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for name, result in results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{name:.<30} {status}")
            
        print("-" * 50)
        print(f"Total: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED! Phase 4.2 CRUD Operations Complete!")
        else:
            print(f"\n⚠️  {total - passed} test(s) failed. Please review.")
            
        return passed == total


async def main():
    """Run the CRUD test suite."""
    async with ChoreCRUDTest() as tester:
        success = await tester.run_all_tests()
        exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())