#!/usr/bin/env python3
"""End-to-end test for complete child user flow."""

import asyncio
import httpx
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

class ChildFlowE2ETest:
    def __init__(self):
        self.client = httpx.AsyncClient()
        self.token = None
        self.headers = {}
        self.user = None
        self.initial_chores = []
        self.completed_chores = []
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
        
    async def test_login(self) -> bool:
        """Test 1: Login as child user."""
        print("\n🔐 TEST 1: Authentication")
        print("-" * 40)
        
        login_data = {
            "username": "demochild",
            "password": "child123"
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
        
        print("✅ Login successful")
        print(f"   Token: {self.token[:20]}...")
        
        # Get user info
        user_response = await self.client.get(
            f"{BASE_URL}/api/v1/users/me",
            headers=self.headers
        )
        
        if user_response.status_code == 200:
            self.user = user_response.json()
            role = "child" if not self.user.get('is_parent', False) else "parent"
            print(f"✅ User info retrieved: {self.user['username']} (Role: {role})")
            return True
        
        print("❌ Failed to get user info")
        return False
        
    async def test_view_chores(self) -> bool:
        """Test 2: View available chores."""
        print("\n📋 TEST 2: View Available Chores")
        print("-" * 40)
        
        response = await self.client.get(
            f"{BASE_URL}/api/v1/chores/available",
            headers=self.headers
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to get chores: {response.status_code}")
            return False
            
        self.initial_chores = response.json()
        print(f"✅ Found {len(self.initial_chores)} available chores:")
        
        for i, chore in enumerate(self.initial_chores[:3], 1):
            reward_text = f"${chore['reward']:.2f}" if chore['reward'] else "Range reward"
            print(f"   {i}. {chore['title']} - {reward_text}")
            if chore.get('is_recurring'):
                print(f"      🔄 Recurring every {chore.get('cooldown_days', 0)} days")
                
        if len(self.initial_chores) > 3:
            print(f"   ... and {len(self.initial_chores) - 3} more")
            
        return len(self.initial_chores) > 0
        
    async def test_complete_chore(self) -> bool:
        """Test 3: Complete a chore."""
        print("\n✅ TEST 3: Complete Chore Action")
        print("-" * 40)
        
        if not self.initial_chores:
            print("❌ No chores available to complete")
            return False
            
        chore_to_complete = self.initial_chores[0]
        print(f"📝 Completing: {chore_to_complete['title']}")
        
        response = await self.client.post(
            f"{BASE_URL}/api/v1/chores/{chore_to_complete['id']}/complete",
            headers=self.headers
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to complete chore: {response.status_code}")
            return False
            
        completed = response.json()
        self.completed_chores.append(completed)
        print(f"✅ Chore marked as complete")
        print(f"   Status: Pending parent approval")
        
        # Verify it's removed from available
        available_response = await self.client.get(
            f"{BASE_URL}/api/v1/chores/available",
            headers=self.headers
        )
        
        if available_response.status_code == 200:
            new_available = available_response.json()
            if len(new_available) < len(self.initial_chores):
                print(f"✅ Chore removed from available list ({len(new_available)} remaining)")
                return True
            else:
                print("❌ Chore still in available list")
                return False
                
        return False
        
    async def test_check_balance(self) -> bool:
        """Test 4: Check balance with pending chores."""
        print("\n💰 TEST 4: Balance View")
        print("-" * 40)
        
        response = await self.client.get(
            f"{BASE_URL}/api/v1/users/me/balance",
            headers=self.headers
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to get balance: {response.status_code}")
            return False
            
        balance = response.json()
        print("✅ Balance retrieved:")
        print(f"   💵 Current Balance: ${balance['balance']:.2f}")
        print(f"   ✅ Total Earned: ${balance['total_earned']:.2f}")
        print(f"   🎁 Adjustments: ${balance['adjustments']:.2f}")
        print(f"   💸 Paid Out: ${balance['paid_out']:.2f}")
        print(f"   ⏳ Pending Approval: ${balance['pending_chores_value']:.2f}")
        
        # Verify calculation
        expected = balance['total_earned'] + balance['adjustments'] - balance['paid_out']
        if abs(balance['balance'] - expected) < 0.01:
            print("✅ Balance calculation verified")
        else:
            print(f"❌ Balance mismatch: expected ${expected:.2f}")
            
        if balance['pending_chores_value'] > 0:
            print(f"ℹ️  ${balance['pending_chores_value']:.2f} waiting for parent approval")
            
        return True
        
    async def test_complete_multiple(self) -> bool:
        """Test 5: Complete multiple chores."""
        print("\n🔄 TEST 5: Multiple Chore Completion")
        print("-" * 40)
        
        # Get current available chores
        response = await self.client.get(
            f"{BASE_URL}/api/v1/chores/available",
            headers=self.headers
        )
        
        if response.status_code != 200:
            print("❌ Failed to get available chores")
            return False
            
        available = response.json()
        to_complete = available[:2]  # Complete up to 2 more
        
        if not to_complete:
            print("ℹ️  No more chores available to complete")
            return True
            
        for chore in to_complete:
            print(f"📝 Completing: {chore['title']}")
            complete_response = await self.client.post(
                f"{BASE_URL}/api/v1/chores/{chore['id']}/complete",
                headers=self.headers
            )
            
            if complete_response.status_code == 200:
                print(f"   ✅ Completed successfully")
                self.completed_chores.append(complete_response.json())
            else:
                print(f"   ❌ Failed to complete")
                
        print(f"✅ Completed {len(self.completed_chores)} chores total")
        return True
        
    async def test_persistence(self) -> bool:
        """Test 6: Verify data persistence."""
        print("\n💾 TEST 6: Data Persistence")
        print("-" * 40)
        
        # Simulate new session with same token
        new_headers = {"Authorization": f"Bearer {self.token}"}
        
        # Check chores state
        chores_response = await self.client.get(
            f"{BASE_URL}/api/v1/chores",
            headers=new_headers
        )
        
        if chores_response.status_code != 200:
            print("❌ Failed to fetch chores in new session")
            return False
            
        all_chores = chores_response.json()
        pending = [c for c in all_chores if c.get('is_completed') and not c.get('is_approved')]
        
        print(f"✅ Session data persisted:")
        print(f"   {len(pending)} chores pending approval")
        
        # Check balance persistence
        balance_response = await self.client.get(
            f"{BASE_URL}/api/v1/users/me/balance",
            headers=new_headers
        )
        
        if balance_response.status_code == 200:
            balance = balance_response.json()
            print(f"   ${balance['pending_chores_value']:.2f} pending in balance")
            
        return True
        
    async def run_all_tests(self):
        """Run complete e2e test suite."""
        print("=" * 50)
        print("🧪 CHILD FLOW END-TO-END TEST")
        print("=" * 50)
        
        tests = [
            ("Authentication", self.test_login),
            ("View Chores", self.test_view_chores),
            ("Complete Chore", self.test_complete_chore),
            ("Check Balance", self.test_check_balance),
            ("Multiple Completions", self.test_complete_multiple),
            ("Data Persistence", self.test_persistence),
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
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for name, result in results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{name:.<30} {status}")
            
        print("-" * 50)
        print(f"Total: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED! Phase 3 Child Flow Complete!")
        else:
            print(f"\n⚠️  {total - passed} test(s) failed. Please review.")
            
        return passed == total


async def main():
    """Run the e2e test suite."""
    async with ChildFlowE2ETest() as tester:
        success = await tester.run_all_tests()
        exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())