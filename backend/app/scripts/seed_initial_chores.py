#!/usr/bin/env python3
"""Seed initial 37 chores from family's handwritten list.

This script creates all chores using the multi-assignment API.
All chores start as unassigned pool or single mode with no assignees,
allowing for flexible assignment later.

Usage:
    docker compose exec api python -m backend.app.scripts.seed_initial_chores
"""

import asyncio
import httpx
import sys
from typing import Dict, List, Any

BASE_URL = "http://localhost:8000"

# All 37 chores from the initial chores list
CHORES_DATA: List[Dict[str, Any]] = [
    # ===== DAILY CHORES (cooldown_days=1) =====
    {
        "title": "Pull tree sprouts",
        "description": "Remove tree sprouts from yard",
        "reward": 1.75,  # Midpoint of 0.5-3.0
        "is_range_reward": True,
        "min_reward": 0.5,
        "max_reward": 3.0,
        "is_recurring": True,
        "cooldown_days": 1,
        "assignment_mode": "unassigned",
        "assignee_ids": []
    },
    {
        "title": "Empty dishwasher",
        "description": "Unload clean dishes from dishwasher",
        "reward": 1.0,
        "is_range_reward": False,
        "is_recurring": True,
        "cooldown_days": 1,  # "We limit" = daily limit
        "assignment_mode": "unassigned",
        "assignee_ids": []
    },
    {
        "title": "Load dishwasher",
        "description": "Load dirty dishes into dishwasher",
        "reward": 3.0,  # Midpoint of 1-5
        "is_range_reward": True,
        "min_reward": 1.0,
        "max_reward": 5.0,
        "is_recurring": True,
        "cooldown_days": 1,
        "assignment_mode": "unassigned",
        "assignee_ids": []
    },
    {
        "title": "Wash dishes that don't go in dishwasher",
        "description": "Hand wash pots, pans, and delicate items",
        "reward": 3.0,  # Midpoint of 1-5
        "is_range_reward": True,
        "min_reward": 1.0,
        "max_reward": 5.0,
        "is_recurring": True,
        "cooldown_days": 1,
        "assignment_mode": "unassigned",
        "assignee_ids": []
    },
    {
        "title": "Clean downstairs couch",
        "description": "Remove items, straighten cushions, vacuum couch",
        "reward": 3.0,  # Midpoint of 1-5
        "is_range_reward": True,
        "min_reward": 1.0,
        "max_reward": 5.0,
        "is_recurring": True,
        "cooldown_days": 1,
        "assignment_mode": "unassigned",
        "assignee_ids": []
    },
    {
        "title": "Walk Teddy",
        "description": "Take Teddy for a 30 minute walk",
        "reward": 1.0,
        "is_range_reward": False,
        "is_recurring": True,
        "cooldown_days": 1,
        "assignment_mode": "unassigned",
        "assignee_ids": []
    },
    {
        "title": "Pick up coats in door of door",
        "description": "Hang up coats and organize entrance area",
        "reward": 2.0,  # Midpoint of 1-3
        "is_range_reward": True,
        "min_reward": 1.0,
        "max_reward": 3.0,
        "is_recurring": True,
        "cooldown_days": 1,
        "assignment_mode": "unassigned",
        "assignee_ids": []
    },

    # ===== WEEKLY CHORES (cooldown_days=7) =====
    {
        "title": "Organize shoes",
        "description": "Arrange shoes neatly in designated area",
        "reward": 2.0,  # Fixed reward (not specified in list)
        "is_range_reward": False,
        "is_recurring": True,
        "cooldown_days": 7,
        "assignment_mode": "unassigned",
        "assignee_ids": []
    },
    {
        "title": "Mop entrance hall",
        "description": "Sweep and mop entrance hall floor",
        "reward": 1.0,
        "is_range_reward": False,
        "is_recurring": True,
        "cooldown_days": 7,
        "assignment_mode": "unassigned",
        "assignee_ids": []
    },
    {
        "title": "Clear stairs of stuff",
        "description": "Remove items from stairs and return to proper locations",
        "reward": 2.0,  # Midpoint of 1-3
        "is_range_reward": True,
        "min_reward": 1.0,
        "max_reward": 3.0,
        "is_recurring": True,
        "cooldown_days": 7,
        "assignment_mode": "unassigned",
        "assignee_ids": []
    },
    {
        "title": "Vacuum stairs",
        "description": "Vacuum all stairs thoroughly",
        "reward": 2.0,  # Midpoint of 1-3
        "is_range_reward": True,
        "min_reward": 1.0,
        "max_reward": 3.0,
        "is_recurring": True,
        "cooldown_days": 7,
        "assignment_mode": "unassigned",
        "assignee_ids": []
    },
    {
        "title": "Vacuum back kitchen stairs",
        "description": "Vacuum back kitchen stairway",
        "reward": 2.0,  # Midpoint of 1-3
        "is_range_reward": True,
        "min_reward": 1.0,
        "max_reward": 3.0,
        "is_recurring": True,
        "cooldown_days": 7,
        "assignment_mode": "unassigned",
        "assignee_ids": []
    },
    {
        "title": "Vacuum bad office",
        "description": "Vacuum office floor completely",
        "reward": 3.0,  # Midpoint of 1-5
        "is_range_reward": True,
        "min_reward": 1.0,
        "max_reward": 5.0,
        "is_recurring": True,
        "cooldown_days": 7,
        "assignment_mode": "unassigned",
        "assignee_ids": []
    },
    {
        "title": "Vacuum living room",
        "description": "Vacuum entire living room floor",
        "reward": 4.5,  # Midpoint of 1-8
        "is_range_reward": True,
        "min_reward": 1.0,
        "max_reward": 8.0,
        "is_recurring": True,
        "cooldown_days": 7,
        "assignment_mode": "unassigned",
        "assignee_ids": []
    },
    {
        "title": "Vacuum hall",
        "description": "Vacuum hallway floor",
        "reward": 2.0,  # Midpoint of 1-3
        "is_range_reward": True,
        "min_reward": 1.0,
        "max_reward": 3.0,
        "is_recurring": True,
        "cooldown_days": 7,
        "assignment_mode": "unassigned",
        "assignee_ids": []
    },
    {
        "title": "Vacuum dining room",
        "description": "Vacuum dining room floor",
        "reward": 3.0,  # Midpoint of 1-5
        "is_range_reward": True,
        "min_reward": 1.0,
        "max_reward": 5.0,
        "is_recurring": True,
        "cooldown_days": 7,
        "assignment_mode": "unassigned",
        "assignee_ids": []
    },
    {
        "title": "Clean Art mini table",
        "description": "Wipe down and organize art mini table",
        "reward": 2.0,  # Midpoint of 1-3
        "is_range_reward": True,
        "min_reward": 1.0,
        "max_reward": 3.0,
        "is_recurring": True,
        "cooldown_days": 7,
        "assignment_mode": "unassigned",
        "assignee_ids": []
    },
    {
        "title": "Clean front kitchen cabinets",
        "description": "Wipe down front of kitchen cabinets",
        "reward": 1.0,
        "is_range_reward": False,
        "is_recurring": True,
        "cooldown_days": 7,
        "assignment_mode": "unassigned",
        "assignee_ids": []
    },
    {
        "title": "Clean glass door",
        "description": "Clean fingerprints and smudges from glass door",
        "reward": 1.0,
        "is_range_reward": False,
        "is_recurring": True,
        "cooldown_days": 7,
        "assignment_mode": "unassigned",
        "assignee_ids": []
    },
    {
        "title": "Clean downstairs bathroom",
        "description": "Clean sink, toilet, and floor in downstairs bathroom",
        "reward": 3.0,  # Midpoint of 1-5
        "is_range_reward": True,
        "min_reward": 1.0,
        "max_reward": 5.0,
        "is_recurring": True,
        "cooldown_days": 7,
        "assignment_mode": "unassigned",
        "assignee_ids": []
    },
    {
        "title": "Clean upstairs bathroom",
        "description": "Clean sink, toilet, shower/tub, and floor in upstairs bathroom",
        "reward": 3.5,  # Midpoint of 1-6
        "is_range_reward": True,
        "min_reward": 1.0,
        "max_reward": 6.0,
        "is_recurring": True,
        "cooldown_days": 7,
        "assignment_mode": "unassigned",
        "assignee_ids": []
    },
    {
        "title": "Clean living room surfaces",
        "description": "Dust and wipe down all living room surfaces",
        "reward": 3.0,  # Midpoint of 1-5
        "is_range_reward": True,
        "min_reward": 1.0,
        "max_reward": 5.0,
        "is_recurring": True,
        "cooldown_days": 7,
        "assignment_mode": "unassigned",
        "assignee_ids": []
    },
    {
        "title": "Sweep front path",
        "description": "Sweep front walkway and porch",
        "reward": 1.0,
        "is_range_reward": False,
        "is_recurring": True,
        "cooldown_days": 7,
        "assignment_mode": "unassigned",
        "assignee_ids": []
    },
    {
        "title": "Take out trash bags",
        "description": "Collect trash from all rooms and take to outdoor bins",
        "reward": 2.0,  # Midpoint of 1-3
        "is_range_reward": True,
        "min_reward": 1.0,
        "max_reward": 3.0,
        "is_recurring": True,
        "cooldown_days": 7,
        "assignment_mode": "unassigned",
        "assignee_ids": []
    },
    {
        "title": "Bring in trash can from street",
        "description": "Bring empty trash can back from curb after pickup",
        "reward": 1.0,
        "is_range_reward": False,
        "is_recurring": True,
        "cooldown_days": 7,
        "assignment_mode": "unassigned",
        "assignee_ids": []
    },

    # ===== PERSONAL ROOM CHORES (unassigned initially, change to single + assign later) =====
    {
        "title": "Clean Jason's room",
        "description": "Organize, vacuum, and dust Jason's room",
        "reward": 4.0,  # Midpoint of 1-7
        "is_range_reward": True,
        "min_reward": 1.0,
        "max_reward": 7.0,
        "is_recurring": True,
        "cooldown_days": 7,
        "assignment_mode": "unassigned",  # Change to 'single' and assign to Jason later via UI/API
        "assignee_ids": []
    },
    {
        "title": "Clean guest room",
        "description": "Organize, vacuum, and dust guest room",
        "reward": 3.0,  # Midpoint of 1-5
        "is_range_reward": True,
        "min_reward": 1.0,
        "max_reward": 5.0,
        "is_recurring": True,
        "cooldown_days": 7,
        "assignment_mode": "unassigned",  # Change to 'single' and assign later via UI/API
        "assignee_ids": []
    },
    {
        "title": "Clean basement Kate area",
        "description": "Organize, vacuum, and clean Kate's basement area",
        "reward": 3.0,  # Midpoint of 1-5
        "is_range_reward": True,
        "min_reward": 1.0,
        "max_reward": 5.0,
        "is_recurring": True,
        "cooldown_days": 7,
        "assignment_mode": "unassigned",  # Change to 'single' and assign to Kate later via UI/API
        "assignee_ids": []
    },

    # ===== ON-DEMAND / NON-RECURRING CHORES =====
    {
        "title": "Babysit Eleanor",
        "description": "Watch and care for Eleanor",
        "reward": 5.5,  # Midpoint of 1-10
        "is_range_reward": True,
        "min_reward": 1.0,
        "max_reward": 10.0,
        "is_recurring": False,  # On-demand task
        "cooldown_days": 0,
        "assignment_mode": "unassigned",
        "assignee_ids": []
    },
]


async def get_or_prompt_parent_credentials() -> tuple[str, str]:
    """Get parent credentials from command line args or use defaults."""
    # Check command line arguments
    if len(sys.argv) >= 3:
        username = sys.argv[1]
        password = sys.argv[2]
        print(f"\nUsing credentials from command line: {username}")
        return username, password

    # Use defaults
    username = "testparent2"
    password = "parentpass123"

    print("\n" + "="*60)
    print("PARENT USER CREDENTIALS")
    print("="*60)
    print(f"Using default credentials: {username}")
    print("(To use different credentials, run with: python -m backend.app.scripts.seed_initial_chores USERNAME PASSWORD)")

    return username, password


async def login_as_parent(client: httpx.AsyncClient, username: str, password: str) -> str:
    """Login as parent and return JWT token."""
    print(f"\nLogging in as '{username}'...")

    login_data = {
        "username": username,
        "password": password
    }

    response = await client.post(
        f"{BASE_URL}/api/v1/users/login",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    if response.status_code != 200:
        print(f"❌ Login failed: {response.text}")
        print("\nPlease create parent user first:")
        print(f"  docker compose exec api python -m backend.app.scripts.create_parent_user")
        sys.exit(1)

    token = response.json()["access_token"]
    print("✓ Login successful")
    return token


async def create_chores(client: httpx.AsyncClient, token: str) -> None:
    """Create all chores using the multi-assignment API."""
    headers = {"Authorization": f"Bearer {token}"}

    print("\n" + "="*60)
    print(f"CREATING {len(CHORES_DATA)} CHORES")
    print("="*60)

    created_count = 0
    failed_count = 0

    for idx, chore_data in enumerate(CHORES_DATA, 1):
        print(f"\n[{idx}/{len(CHORES_DATA)}] Creating: {chore_data['title']}")
        print(f"  Mode: {chore_data['assignment_mode']}")
        print(f"  Reward: ${chore_data['reward']:.2f}" +
              (f" (${chore_data['min_reward']:.2f}-${chore_data['max_reward']:.2f})"
               if chore_data.get('is_range_reward') else ""))
        print(f"  Recurring: {'Yes' if chore_data['is_recurring'] else 'No'}" +
              (f" (every {chore_data['cooldown_days']} day{'s' if chore_data['cooldown_days'] != 1 else ''})"
               if chore_data['is_recurring'] else ""))

        response = await client.post(
            f"{BASE_URL}/api/v1/chores",
            json=chore_data,
            headers=headers
        )

        if response.status_code == 201:
            chore = response.json()
            print(f"  ✓ Created (ID: {chore['id']})")
            created_count += 1
        else:
            print(f"  ✗ Failed: Status {response.status_code}")
            print(f"  Error: {response.text}")
            failed_count += 1

    # Print summary
    print("\n" + "="*60)
    print("SEEDING SUMMARY")
    print("="*60)
    print(f"✓ Successfully created: {created_count} chores")
    if failed_count > 0:
        print(f"✗ Failed: {failed_count} chores")
    print()

    # Print breakdown by type
    pool_count = sum(1 for c in CHORES_DATA if c["assignment_mode"] == "unassigned")
    single_count = sum(1 for c in CHORES_DATA if c["assignment_mode"] == "single")
    daily_count = sum(1 for c in CHORES_DATA if c.get("cooldown_days") == 1)
    weekly_count = sum(1 for c in CHORES_DATA if c.get("cooldown_days") == 7)

    print("Chores by assignment mode:")
    print(f"  🏊 Unassigned pool: {pool_count}")
    if single_count > 0:
        print(f"  👤 Single (unassigned): {single_count}")
    print()
    print("Chores by frequency:")
    print(f"  📅 Daily: {daily_count}")
    print(f"  📅 Weekly: {weekly_count}")
    print(f"  📅 On-demand: 1")
    print()
    print("Next steps:")
    print("  1. View chores in database:")
    print("     docker compose exec mysql mysql -u root -p -e \"SELECT id, title, assignment_mode, is_recurring FROM chores_tracker.chores;\"")
    print()
    print("  2. (Optional) Change personal room chores to 'single' mode and assign:")
    print("     - 'Clean Jason's room' → change to single mode, assign to Jason")
    print("     - 'Clean guest room' → change to single mode, assign to appropriate child")
    print("     - 'Clean basement Kate area' → change to single mode, assign to Kate")
    print("     Use: PATCH /api/v1/chores/{chore_id} with assignment_mode='single' and assignee_ids=[child_id]")
    print()
    print("  3. Test via API or frontend UI")


async def main():
    """Main entry point."""
    print("="*60)
    print("SEED INITIAL CHORES SCRIPT")
    print("="*60)
    print("This script will create 37 chores from the initial chores list.")
    print()
    print("Breakdown:")
    print("  - 34 unassigned pool chores (shared household tasks)")
    print("  - 3 personal room chores (start as pool, change to single later)")
    print("  - Mix of daily, weekly, and on-demand tasks")
    print()

    # Get parent credentials
    username, password = await get_or_prompt_parent_credentials()

    # Create HTTP client
    async with httpx.AsyncClient() as client:
        # Login as parent
        token = await login_as_parent(client, username, password)

        # Create all chores
        await create_chores(client, token)


if __name__ == "__main__":
    asyncio.run(main())
