#!/usr/bin/env python3
"""Verify seeded chores in database."""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import select, func
from backend.app.db.base import AsyncSessionLocal
from backend.app.models.chore import Chore


async def verify_chores():
    """Verify seeded chores."""
    async with AsyncSessionLocal() as db:
        # Get total count
        result = await db.execute(select(func.count(Chore.id)))
        total_count = result.scalar()

        print("="*60)
        print("CHORES DATABASE VERIFICATION")
        print("="*60)
        print(f"Total chores in database: {total_count}")
        print()

        # Get chores by assignment mode
        result = await db.execute(
            select(Chore.assignment_mode, func.count(Chore.id))
            .group_by(Chore.assignment_mode)
        )
        mode_counts = result.all()

        print("Chores by assignment mode:")
        for mode, count in mode_counts:
            print(f"  {mode}: {count}")
        print()

        # Get chores by frequency
        result = await db.execute(
            select(Chore.cooldown_days, func.count(Chore.id))
            .where(Chore.is_recurring == True)
            .group_by(Chore.cooldown_days)
        )
        freq_counts = result.all()

        print("Recurring chores by cooldown:")
        for days, count in freq_counts:
            print(f"  {days} day(s): {count} chores")

        # Get non-recurring count
        result = await db.execute(
            select(func.count(Chore.id))
            .where(Chore.is_recurring == False)
        )
        non_recurring = result.scalar()
        print(f"  Non-recurring: {non_recurring} chore(s)")
        print()

        # List all chores
        result = await db.execute(
            select(Chore.id, Chore.title, Chore.assignment_mode, Chore.reward, Chore.is_recurring)
            .order_by(Chore.id)
        )
        chores = result.all()

        print(f"All chores ({len(chores)}):")
        print("-" * 60)
        for chore_id, title, mode, reward, recurring in chores:
            mode_icon = "🏊" if mode == "unassigned" else "👤" if mode == "single" else "👥"
            rec_icon = "🔁" if recurring else "1️⃣"
            print(f"{chore_id:3d}. {rec_icon} {mode_icon} {title[:40]:<40} ${reward:.2f}")


if __name__ == "__main__":
    asyncio.run(verify_chores())
