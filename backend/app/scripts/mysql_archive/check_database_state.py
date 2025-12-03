#!/usr/bin/env python3
"""
Check the current database state and Alembic version tracking.
"""
import asyncio
import os
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

async def check_database_state():
    """Check the current database tables and Alembic version."""

    print("🔍 Checking database state...")
    print("=" * 60)

    try:
        from backend.app.core.config import settings
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text

        # Create engine
        engine = create_async_engine(settings.DATABASE_URL, echo=False)

        async with engine.connect() as conn:
            # Check existing tables
            result = await conn.execute(text("SHOW TABLES"))
            tables = [row[0] for row in result.fetchall()]

            print(f"📋 Existing tables: {', '.join(tables)}")

            # Check if families table exists
            families_exists = 'families' in tables
            alembic_exists = 'alembic_version' in tables

            print(f"✅ families table exists: {families_exists}")
            print(f"✅ alembic_version table exists: {alembic_exists}")

            if alembic_exists:
                # Check current Alembic version
                result = await conn.execute(text("SELECT version_num FROM alembic_version"))
                versions = [row[0] for row in result.fetchall()]
                print(f"📌 Current Alembic version(s): {versions}")

                # Check if this version indicates families migration was run
                target_version = "f495eb296fbb"  # The families migration
                has_families_migration = target_version in versions
                print(f"🎯 Families migration ({target_version}) in version table: {has_families_migration}")

                if families_exists and not has_families_migration:
                    print("⚠️  PROBLEM: families table exists but Alembic doesn't know about it!")
                    print("   This suggests the migration state is out of sync.")
                    return False
                elif not families_exists and has_families_migration:
                    print("⚠️  PROBLEM: Alembic thinks families exists but table is missing!")
                    return False
                elif families_exists and has_families_migration:
                    print("✅ Database and Alembic state are in sync")
                    return True
                else:
                    print("ℹ️  Neither table nor migration version exist - normal for fresh DB")
                    return True
            else:
                print("⚠️  No alembic_version table found - this is unusual")
                return False

        await engine.dispose()

    except Exception as e:
        print(f"❌ Database check failed: {e}")
        return False

async def check_migration_history():
    """Check the Alembic migration history."""

    print("\n🔍 Checking Alembic migration history...")
    print("=" * 60)

    try:
        # Get migration files and their order
        migrations_dir = Path(__file__).parent.parent / "alembic" / "versions"
        migration_files = list(migrations_dir.glob("*.py"))

        print(f"📁 Found {len(migration_files)} migration files:")

        for migration_file in sorted(migration_files):
            filename = migration_file.name
            # Extract version from filename
            version = filename.split('_')[0]
            print(f"  - {version}: {filename}")

        # Check which migration comes after the problem one
        families_migration = "f495eb296fbb"
        previous_migration = "0339dc9bba67"

        print(f"\n🎯 Target migration chain:")
        print(f"  Previous: {previous_migration}")
        print(f"  Families: {families_migration}")

        return True

    except Exception as e:
        print(f"❌ Migration history check failed: {e}")
        return False

async def main():
    """Main function to run all checks."""

    print("🧪 Database State Diagnostic Tool")
    print("This script checks for Alembic/Database sync issues")
    print()

    db_success = await check_database_state()
    migration_success = await check_migration_history()

    print("\n" + "=" * 60)
    if db_success and migration_success:
        print("🎉 Database state checks completed successfully")
        return True
    else:
        print("💥 Database state issues detected!")
        print("\n💡 Possible solutions:")
        print("  1. Mark migration as completed: UPDATE alembic_version SET version_num = 'f495eb296fbb'")
        print("  2. Reset Alembic state: alembic stamp head")
        print("  3. Create new migration from current state: alembic revision --autogenerate")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)