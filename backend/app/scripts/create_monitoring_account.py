#!/usr/bin/env python3
"""
Script to create a dedicated monitoring service account for health checks.

This account is used by AI agents and monitoring tools to perform:
- Authentication health checks (JWT login flow)
- API endpoint availability testing
- End-to-end functional validation

The monitoring account has:
- Parent role (for read access to most endpoints)
- Dedicated family (isolated from production data)
- Test child users for functional testing
- Test chores for validation workflows

Security:
- Credentials should be stored in secrets manager
- Account has minimal permissions (read-only in practice)
- Belongs to isolated test family
- All activities are logged for audit
"""

import asyncio
import sys
import os
import secrets
import string
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import select
from backend.app.db.base import AsyncSessionLocal
from backend.app.models.user import User
from backend.app.models.family import Family
from backend.app.models.chore import Chore
from backend.app.models.chore_assignment import ChoreAssignment
from backend.app.core.security.password import get_password_hash


def generate_secure_password(length: int = 32) -> str:
    """Generate a cryptographically secure password."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_invite_code(length: int = 8) -> str:
    """Generate a random invite code."""
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


async def create_monitoring_account():
    """Create monitoring service account with test data."""

    # Generate secure credentials
    monitoring_password = generate_secure_password()
    test_child_password = generate_secure_password(16)  # Shorter for test accounts

    async with AsyncSessionLocal() as db:
        try:
            # Check if monitoring account already exists
            result = await db.execute(
                select(User).where(User.username == "monitoring_agent")
            )
            existing_user = result.scalar_one_or_none()

            if existing_user:
                print("⚠️  Monitoring account already exists!")
                print(f"   Username: {existing_user.username}")
                print(f"   ID: {existing_user.id}")
                print(f"   Email: {existing_user.email}")
                print("\n❓ Delete existing account and recreate? (yes/no)")
                response = input().strip().lower()
                if response != "yes":
                    print("✋ Aborted. Existing account unchanged.")
                    return

                # Delete existing monitoring account and family
                if existing_user.family_id:
                    family_result = await db.execute(
                        select(Family).where(Family.id == existing_user.family_id)
                    )
                    family = family_result.scalar_one_or_none()
                    if family:
                        await db.delete(family)

                await db.delete(existing_user)
                await db.commit()
                print("🗑️  Deleted existing monitoring account\n")

            # Step 1: Create monitoring family
            print("📋 Creating monitoring family...")
            family = Family(
                name="Monitoring & Health Checks",
                invite_code=generate_invite_code(),
                invite_code_expires_at=datetime.utcnow() + timedelta(days=365)
            )
            db.add(family)
            await db.flush()  # Get family ID

            print(f"✅ Created family (ID: {family.id}, Invite: {family.invite_code})")

            # Step 2: Create monitoring parent account
            print("\n👤 Creating monitoring parent account...")
            parent = User(
                username="monitoring_agent",
                email="monitoring@healthcheck.local",
                hashed_password=get_password_hash(monitoring_password),
                is_parent=True,
                is_active=True,
                family_id=family.id
            )
            db.add(parent)
            await db.flush()  # Get parent ID

            print(f"✅ Created monitoring parent (ID: {parent.id})")

            # Step 3: Create test child accounts
            print("\n👶 Creating test child accounts...")
            test_children = []

            child1 = User(
                username="test_child_monitor_1",
                email="test_child_1@healthcheck.local",
                hashed_password=get_password_hash(test_child_password),
                is_parent=False,
                is_active=True,
                parent_id=parent.id,
                family_id=family.id
            )
            db.add(child1)
            test_children.append(child1)

            child2 = User(
                username="test_child_monitor_2",
                email="test_child_2@healthcheck.local",
                hashed_password=get_password_hash(test_child_password),
                is_parent=False,
                is_active=True,
                parent_id=parent.id,
                family_id=family.id
            )
            db.add(child2)
            test_children.append(child2)

            await db.flush()  # Get child IDs

            for idx, child in enumerate(test_children, 1):
                print(f"✅ Created test child {idx} (ID: {child.id})")

            # Step 4: Create test chores for validation
            print("\n📝 Creating test chores...")

            # Test chore 1: Simple fixed reward chore
            chore1 = Chore(
                title="[TEST] Health Check Chore - Fixed Reward",
                description="Test chore for monitoring validation with fixed reward",
                reward=5.0,
                is_recurring=False,
                is_disabled=False,
                creator_id=parent.id,
                assignment_mode="single"
            )
            db.add(chore1)
            await db.flush()

            # Create assignment for chore1
            assignment1 = ChoreAssignment(
                chore_id=chore1.id,
                assignee_id=child1.id,
                is_completed=False,
                is_approved=False
            )
            db.add(assignment1)

            print(f"✅ Created test chore 1 (ID: {chore1.id}, assigned to child 1)")

            # Test chore 2: Range reward chore
            chore2 = Chore(
                title="[TEST] Health Check Chore - Range Reward",
                description="Test chore for monitoring validation with range reward",
                reward=5.0,
                is_range_reward=True,
                min_reward=3.0,
                max_reward=10.0,
                is_recurring=False,
                is_disabled=False,
                creator_id=parent.id,
                assignment_mode="single"
            )
            db.add(chore2)
            await db.flush()

            # Create assignment for chore2
            assignment2 = ChoreAssignment(
                chore_id=chore2.id,
                assignee_id=child2.id,
                is_completed=False,
                is_approved=False
            )
            db.add(assignment2)

            print(f"✅ Created test chore 2 (ID: {chore2.id}, assigned to child 2)")

            # Commit all changes
            await db.commit()

            # Print summary
            print("\n" + "=" * 70)
            print("🎉 MONITORING SERVICE ACCOUNT CREATED SUCCESSFULLY!")
            print("=" * 70)

            print("\n📌 PARENT ACCOUNT (Main Monitoring Account)")
            print(f"   Username: monitoring_agent")
            print(f"   Email:    monitoring@healthcheck.local")
            print(f"   Password: {monitoring_password}")
            print(f"   User ID:  {parent.id}")
            print(f"   Family:   {family.name} (ID: {family.id})")

            print("\n📌 TEST CHILD ACCOUNTS")
            for idx, child in enumerate(test_children, 1):
                print(f"   Child {idx}: {child.username} (ID: {child.id})")
            print(f"   Password (both): {test_child_password}")

            print("\n📌 TEST CHORES")
            print(f"   Chore 1: {chore1.title} (ID: {chore1.id})")
            print(f"   Chore 2: {chore2.title} (ID: {chore2.id})")

            print("\n⚠️  SECURITY NOTICE")
            print("   1. Store credentials in your secrets manager (NOT in code)")
            print("   2. Use environment variables for your AI agent:")
            print("      - MONITORING_USERNAME=monitoring_agent")
            print("      - MONITORING_PASSWORD=<password_above>")
            print("   3. These credentials provide read access to test data only")
            print("   4. All monitoring activities are logged for audit")

            print("\n📝 NEXT STEPS")
            print("   1. Save credentials to your secrets manager")
            print("   2. Read the AI agent integration guide:")
            print("      docs/ai-agent-health-check-integration.md")
            print("   3. Configure your AI agent with the provided credentials")
            print("   4. Test the integration with the example workflow")

            print("\n✅ Setup complete!")
            print("=" * 70)

        except Exception as e:
            print(f"\n❌ Error creating monitoring account: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    print("🚀 Monitoring Service Account Setup")
    print("=" * 70)
    print("This script will create:")
    print("  • Monitoring parent account (monitoring_agent)")
    print("  • Dedicated monitoring family (isolated from production)")
    print("  • 2 test child accounts for functional validation")
    print("  • 2 test chores for API testing")
    print("\n⚠️  WARNING: Credentials will be displayed ONCE. Save them securely!")
    print("=" * 70)
    print("\nPress ENTER to continue or Ctrl+C to cancel...")
    input()

    asyncio.run(create_monitoring_account())
