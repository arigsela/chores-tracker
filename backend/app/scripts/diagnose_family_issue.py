#!/usr/bin/env python3
"""
Diagnose family_id vs parent_id relationship issues.
"""
import asyncio
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

async def diagnose():
    """Check parent_id and family_id relationships."""

    from backend.app.core.config import settings
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy import text

    print("🔍 Diagnosing Family Relationships")
    print("=" * 80)

    # Create engine
    engine = create_async_engine(settings.DATABASE_URL, echo=False)

    async with engine.connect() as conn:
        # Check families table
        print("\n📋 Families Table:")
        print("-" * 80)
        result = await conn.execute(text("SELECT * FROM families"))
        families = result.fetchall()
        cols = result.keys()
        for row in families:
            data = dict(zip(cols, row))
            print(f"  ID: {data.get('id')}, Name: {data.get('name')}, Parent ID: {data.get('parent_user_id')}")

        # Check users table with both parent_id and family_id
        print("\n👥 Users Table (with parent_id and family_id):")
        print("-" * 80)
        result = await conn.execute(text(
            "SELECT id, username, is_parent, parent_id, family_id FROM users ORDER BY id"
        ))
        users = result.fetchall()

        for row in users:
            user_id, username, is_parent, parent_id, family_id = row
            parent_str = f"Parent ID: {parent_id}" if parent_id else "No parent"
            family_str = f"Family ID: {family_id}" if family_id else "No family"
            role = "Parent" if is_parent else "Child"
            print(f"  ID: {user_id}, Username: {username}, Role: {role}, {parent_str}, {family_str}")

        # Check for mismatches
        print("\n⚠️  Checking for Mismatches:")
        print("-" * 80)

        # Check if asela's children have different family_id
        result = await conn.execute(text(
            "SELECT u1.username as parent_user, u1.family_id as parent_family_id, "
            "u2.username as child_user, u2.family_id as child_family_id "
            "FROM users u1 "
            "JOIN users u2 ON u2.parent_id = u1.id "
            "WHERE u1.family_id IS NOT NULL OR u2.family_id IS NOT NULL"
        ))

        mismatches = result.fetchall()
        if mismatches:
            for row in mismatches:
                parent_user, parent_fam_id, child_user, child_fam_id = row
                if parent_fam_id != child_fam_id:
                    print(f"  ❌ MISMATCH: {parent_user} (family_id={parent_fam_id}) != {child_user} (family_id={child_fam_id})")
                else:
                    print(f"  ✅ OK: {parent_user} and {child_user} both in family_id={parent_fam_id}")
        else:
            print("  No family_id relationships found")

        # Specific check for asela
        print("\n🎯 Specific Check for 'asela':")
        print("-" * 80)
        result = await conn.execute(text(
            "SELECT id, username, is_parent, parent_id, family_id FROM users WHERE username = 'asela'"
        ))
        asela = result.fetchone()
        if asela:
            asela_id, asela_username, asela_is_parent, asela_parent_id, asela_family_id = asela
            print(f"  asela: ID={asela_id}, family_id={asela_family_id}")

            # Get children by parent_id
            result = await conn.execute(text(
                "SELECT id, username, family_id FROM users WHERE parent_id = :parent_id"
            ), {"parent_id": asela_id})
            children = result.fetchall()
            print(f"\n  Children (by parent_id={asela_id}):")
            for child_id, child_username, child_family_id in children:
                match_status = "✅ MATCH" if child_family_id == asela_family_id else "❌ MISMATCH"
                print(f"    - {child_username}: ID={child_id}, family_id={child_family_id} {match_status}")

    await engine.dispose()
    print("\n" + "=" * 80)
    print("✅ Diagnosis complete")

if __name__ == "__main__":
    asyncio.run(diagnose())
