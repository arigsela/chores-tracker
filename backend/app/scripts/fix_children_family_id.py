#!/usr/bin/env python3
"""
Fix family_id for children to match their parent's family_id.

This script identifies all children who have a parent_id but no family_id,
and updates their family_id to match their parent's family_id.
"""
import asyncio
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

async def fix_family_ids():
    """Synchronize children's family_id with their parent's family_id."""

    from backend.app.core.config import settings
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy import text

    print("🔧 Fixing Children's Family IDs")
    print("=" * 80)

    # Create engine
    engine = create_async_engine(settings.DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        # First, identify children with mismatched family_id
        print("\n🔍 Finding children with missing or mismatched family_id...")
        result = await conn.execute(text("""
            SELECT
                c.id as child_id,
                c.username as child_username,
                c.family_id as child_family_id,
                p.id as parent_id,
                p.username as parent_username,
                p.family_id as parent_family_id
            FROM users c
            JOIN users p ON c.parent_id = p.id
            WHERE (c.family_id IS NULL OR c.family_id != p.family_id)
              AND p.family_id IS NOT NULL
        """))

        mismatches = result.fetchall()

        if not mismatches:
            print("✅ No mismatches found! All children have correct family_id.")
            return True

        print(f"📋 Found {len(mismatches)} children with incorrect family_id:\n")
        for child_id, child_username, child_family_id, parent_id, parent_username, parent_family_id in mismatches:
            print(f"  - {child_username} (ID:{child_id}): family_id={child_family_id} -> should be {parent_family_id} (from parent {parent_username})")

        # Confirm before proceeding (in production, you might want to add a --dry-run flag)
        print(f"\n⚠️  About to update {len(mismatches)} children's family_id...")

        # Perform the update
        print("\n🔄 Updating family_id for children...")
        update_result = await conn.execute(text("""
            UPDATE users c
            JOIN users p ON c.parent_id = p.id
            SET c.family_id = p.family_id
            WHERE (c.family_id IS NULL OR c.family_id != p.family_id)
              AND p.family_id IS NOT NULL
        """))

        rows_updated = update_result.rowcount
        print(f"✅ Updated {rows_updated} children's family_id")

        # Verify the fix
        print("\n🔍 Verifying the fix...")
        result = await conn.execute(text("""
            SELECT
                c.username as child_username,
                c.family_id as child_family_id,
                p.username as parent_username,
                p.family_id as parent_family_id
            FROM users c
            JOIN users p ON c.parent_id = p.id
            WHERE p.family_id IS NOT NULL
        """))

        verification = result.fetchall()
        all_match = True
        for child_username, child_family_id, parent_username, parent_family_id in verification:
            if child_family_id != parent_family_id:
                print(f"  ❌ STILL MISMATCHED: {child_username} (family_id={child_family_id}) != {parent_username} (family_id={parent_family_id})")
                all_match = False
            else:
                print(f"  ✅ {child_username} now has family_id={child_family_id} (matches parent {parent_username})")

        print("\n" + "=" * 80)
        if all_match:
            print("🎉 All children now have correct family_id!")
            return True
        else:
            print("❌ Some children still have incorrect family_id")
            return False

    await engine.dispose()

if __name__ == "__main__":
    success = asyncio.run(fix_family_ids())
    sys.exit(0 if success else 1)
