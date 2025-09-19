#!/usr/bin/env python3
"""
Fix Alembic migration state when database schema is ahead of migration tracking.

This script manually updates the alembic_version table to reflect the actual
database state when tables exist but Alembic doesn't know about them.
"""
import asyncio
import os
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

async def fix_migration_state():
    """Fix the Alembic migration state by marking families migration as completed."""

    print("🔧 Fixing Alembic migration state...")
    print("=" * 60)

    try:
        from backend.app.core.config import settings
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text

        # Create engine
        engine = create_async_engine(settings.DATABASE_URL, echo=False)

        async with engine.connect() as conn:
            # First, check current state
            result = await conn.execute(text("SELECT version_num FROM alembic_version"))
            current_versions = [row[0] for row in result.fetchall()]
            print(f"📌 Current Alembic version(s): {current_versions}")

            # Check if families table exists
            result = await conn.execute(text("SHOW TABLES LIKE 'families'"))
            families_exists = bool(result.fetchone())
            print(f"✅ families table exists: {families_exists}")

            if not families_exists:
                print("❌ families table doesn't exist - migration state fix not needed")
                return False

            # Check if the head migration is already recorded
            head_migration = "a988bdaeacef"  # The latest head revision
            if head_migration in current_versions:
                print(f"✅ Migration {head_migration} (head) already recorded - no fix needed")
                return True

            print(f"\n🔧 Updating Alembic version to head revision (skipping conflicting migrations)...")

            try:
                # Update the alembic_version table to the head revision
                # This effectively marks all previous migrations as completed
                await conn.execute(
                    text("UPDATE alembic_version SET version_num = :version"),
                    {"version": head_migration}
                )

                await conn.commit()

                # Verify the update
                result = await conn.execute(text("SELECT version_num FROM alembic_version"))
                new_versions = [row[0] for row in result.fetchall()]
                print(f"✅ Updated Alembic version to: {new_versions}")

                print("✅ Migration state fix committed successfully")

                return True

            except Exception as e:
                await conn.rollback()
                print(f"❌ Failed to update migration state: {e}")
                return False

        await engine.dispose()

    except Exception as e:
        print(f"❌ Migration state fix failed: {e}")
        return False

async def verify_fix():
    """Verify that the migration state is now correct."""

    print("\n🔍 Verifying migration state fix...")
    print("=" * 60)

    try:
        from backend.app.core.config import settings
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text

        # Create engine
        engine = create_async_engine(settings.DATABASE_URL, echo=False)

        async with engine.connect() as conn:
            # Check alembic version
            result = await conn.execute(text("SELECT version_num FROM alembic_version"))
            versions = [row[0] for row in result.fetchall()]

            # Check families table structure
            result = await conn.execute(text("DESCRIBE families"))
            families_columns = [row[0] for row in result.fetchall()]

            # Check users table for family_id column
            result = await conn.execute(text("DESCRIBE users"))
            users_columns = [row[0] for row in result.fetchall()]

            print(f"✅ Alembic version: {versions}")
            print(f"✅ families table columns: {families_columns}")
            print(f"✅ family_id in users table: {'family_id' in users_columns}")

            # Verify expected schema matches
            expected_families_columns = ['id', 'name', 'invite_code', 'invite_code_expires_at', 'created_at', 'updated_at']
            families_schema_correct = all(col in families_columns for col in expected_families_columns)

            if families_schema_correct and 'family_id' in users_columns and 'a988bdaeacef' in versions:
                print("🎉 Migration state is now correct!")
                return True
            else:
                print("⚠️  Some issues remain with the schema")
                return False

        await engine.dispose()

    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

async def main():
    """Main function to fix and verify migration state."""

    print("🧪 Alembic Migration State Fix Tool")
    print("This script fixes database/Alembic sync issues")
    print()

    # Ask for confirmation in production
    env = os.getenv("ENVIRONMENT", "development")
    if env != "development":
        print(f"⚠️  Running in {env} environment")
        print("This will modify the alembic_version table.")
        print("Make sure you have a database backup before proceeding!")
        print()

    fix_success = await fix_migration_state()

    if fix_success:
        verify_success = await verify_fix()

        if verify_success:
            print("\n" + "=" * 60)
            print("🎉 Migration state fix completed successfully!")
            print("💡 Alembic migrations should now run without conflicts")
            return True

    print("\n" + "=" * 60)
    print("💥 Migration state fix failed!")
    return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)