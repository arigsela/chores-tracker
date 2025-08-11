#!/usr/bin/env python3
"""Test script for Phase 4.1 - Parent Children Management."""

import asyncio
import httpx
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

class ParentFlowTest:
    def __init__(self):
        self.client = httpx.AsyncClient()
        self.token = None
        self.headers = {}
        self.user = None
        self.children = []
        self.allowance_summary = []
        
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
        
        print("✅ Parent login successful")
        
        # Get user info
        user_response = await self.client.get(
            f"{BASE_URL}/api/v1/users/me",
            headers=self.headers
        )
        
        if user_response.status_code == 200:
            self.user = user_response.json()
            role = "parent" if self.user.get('is_parent', False) else "child"
            print(f"✅ User info: {self.user['username']} (Role: {role})")
            return True
        
        print("❌ Failed to get user info")
        return False
        
    async def test_get_children(self) -> bool:
        """Test 2: Get list of children."""
        print("\n👶 TEST 2: Get Children List")
        print("-" * 40)
        
        response = await self.client.get(
            f"{BASE_URL}/api/v1/users/my-children",
            headers=self.headers
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to get children: {response.status_code}")
            return False
            
        self.children = response.json()
        print(f"✅ Found {len(self.children)} children:")
        
        for child in self.children:
            print(f"   - {child['username']} (ID: {child['id']}, Active: {child['is_active']})")
            
        return len(self.children) > 0
        
    async def test_get_allowance_summary(self) -> bool:
        """Test 3: Get allowance summary for all children."""
        print("\n💰 TEST 3: Allowance Summary")
        print("-" * 40)
        
        response = await self.client.get(
            f"{BASE_URL}/api/v1/users/allowance-summary",
            headers=self.headers
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to get allowance summary: {response.status_code}")
            return False
            
        self.allowance_summary = response.json()
        print("✅ Allowance Summary Retrieved:")
        
        total_owed = 0
        for summary in self.allowance_summary:
            print(f"\n   {summary['username']}:")
            print(f"      Completed Chores: {summary['completed_chores']}")
            print(f"      Total Earned: ${summary['total_earned']:.2f}")
            print(f"      Adjustments: ${summary['total_adjustments']:.2f}")
            print(f"      Paid Out: ${summary['paid_out']:.2f}")
            print(f"      Balance Due: ${summary['balance_due']:.2f}")
            total_owed += summary['balance_due']
            
        print(f"\n   📊 Total Owed to All Children: ${total_owed:.2f}")
        return True
        
    async def test_get_child_chores(self) -> bool:
        """Test 4: Get chores for each child."""
        print("\n📋 TEST 4: Child Chores Details")
        print("-" * 40)
        
        if not self.children:
            print("❌ No children to test")
            return False
            
        for child in self.children:
            response = await self.client.get(
                f"{BASE_URL}/api/v1/chores/child/{child['id']}",
                headers=self.headers
            )
            
            if response.status_code != 200:
                print(f"❌ Failed to get chores for {child['username']}")
                continue
                
            chores = response.json()
            print(f"\n📝 {child['username']}'s Chores ({len(chores)} total):")
            
            # Categorize chores
            active = [c for c in chores if not c.get('is_completed', False)]
            pending = [c for c in chores if c.get('is_completed', False) and not c.get('is_approved', False)]
            approved = [c for c in chores if c.get('is_approved', False)]
            
            print(f"   ⚡ Active: {len(active)}")
            print(f"   ⏳ Pending Approval: {len(pending)}")
            print(f"   ✅ Approved: {len(approved)}")
            
            # Show pending chores details
            if pending:
                print(f"\n   Pending Chores for Approval:")
                for chore in pending[:3]:  # Show first 3
                    reward_text = f"${chore['reward']:.2f}" if chore['reward'] else f"${chore['min_reward']:.2f}-${chore['max_reward']:.2f}"
                    print(f"      - {chore['title']}: {reward_text}")
                    
        return True
        
    async def test_approve_chore(self) -> bool:
        """Test 5: Approve a pending chore."""
        print("\n✅ TEST 5: Approve Chore")
        print("-" * 40)
        
        # Find a child with pending chores
        pending_chore = None
        child_name = None
        
        for child in self.children:
            response = await self.client.get(
                f"{BASE_URL}/api/v1/chores/child/{child['id']}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                chores = response.json()
                pending = [c for c in chores if c.get('is_completed') and not c.get('is_approved')]
                if pending:
                    pending_chore = pending[0]
                    child_name = child['username']
                    break
                    
        if not pending_chore:
            print("ℹ️  No pending chores to approve")
            return True
            
        print(f"📝 Approving chore for {child_name}: {pending_chore['title']}")
        
        # Determine reward value
        approve_data = {}
        if pending_chore['is_range_reward']:
            # Use midpoint of range
            reward_value = (pending_chore['min_reward'] + pending_chore['max_reward']) / 2
            approve_data['reward_value'] = reward_value
            print(f"   Range reward: ${pending_chore['min_reward']:.2f} - ${pending_chore['max_reward']:.2f}")
            print(f"   Approving with: ${reward_value:.2f}")
        else:
            reward_value = pending_chore['reward']
            print(f"   Fixed reward: ${reward_value:.2f}")
            
        # Approve the chore
        response = await self.client.post(
            f"{BASE_URL}/api/v1/chores/{pending_chore['id']}/approve",
            headers=self.headers,
            json=approve_data
        )
        
        if response.status_code == 200:
            print(f"✅ Chore approved successfully!")
            
            # Check updated balance
            balance_response = await self.client.get(
                f"{BASE_URL}/api/v1/users/allowance-summary",
                headers=self.headers
            )
            
            if balance_response.status_code == 200:
                new_summary = balance_response.json()
                for summary in new_summary:
                    if summary['username'] == child_name:
                        print(f"   {child_name}'s new balance: ${summary['balance_due']:.2f}")
                        break
            return True
        else:
            print(f"❌ Failed to approve chore: {response.status_code}")
            return False
            
    async def test_pending_approvals(self) -> bool:
        """Test 6: Get all pending approvals."""
        print("\n📋 TEST 6: Pending Approvals List")
        print("-" * 40)
        
        response = await self.client.get(
            f"{BASE_URL}/api/v1/chores/pending-approval",
            headers=self.headers
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to get pending approvals: {response.status_code}")
            return False
            
        pending = response.json()
        print(f"✅ Found {len(pending)} chores pending approval")
        
        if pending:
            print("\n   Pending Approvals:")
            for chore in pending[:5]:  # Show first 5
                assignee = f"Child #{chore.get('assignee_id', 'Unknown')}"
                if chore['is_range_reward']:
                    reward = f"${chore['min_reward']:.2f}-${chore['max_reward']:.2f}"
                else:
                    reward = f"${chore['reward']:.2f}"
                print(f"      - {chore['title']} ({assignee}): {reward}")
                
        return True
        
    async def run_all_tests(self):
        """Run complete parent flow test suite."""
        print("=" * 50)
        print("🧪 PHASE 4.1 - PARENT FLOW TEST")
        print("=" * 50)
        
        tests = [
            ("Parent Authentication", self.test_parent_login),
            ("Get Children List", self.test_get_children),
            ("Allowance Summary", self.test_get_allowance_summary),
            ("Child Chores Details", self.test_get_child_chores),
            ("Approve Chore", self.test_approve_chore),
            ("Pending Approvals", self.test_pending_approvals),
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
        print("📊 TEST SUMMARY - PHASE 4.1")
        print("=" * 50)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for name, result in results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{name:.<35} {status}")
            
        print("-" * 50)
        print(f"Total: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED! Phase 4.1 Parent Flow Complete!")
        else:
            print(f"\n⚠️  {total - passed} test(s) failed. Please review.")
            
        return passed == total


async def main():
    """Run the parent flow test suite."""
    async with ParentFlowTest() as tester:
        success = await tester.run_all_tests()
        exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())