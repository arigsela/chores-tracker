#!/usr/bin/env python3
"""
Production migration state fix - runs the migration fix with production safety checks.

This script is designed to be run in production Kubernetes environments
to fix the "Table 'families' already exists" error.
"""
import asyncio
import os
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

async def production_migration_fix():
    """Run production-safe migration state fix."""

    print("🏭 Production Migration State Fix")
    print("=" * 60)

    # Environment check
    env = os.getenv("ENVIRONMENT", "development")
    print(f"🌍 Environment: {env}")

    if env != "production":
        print("⚠️  Not running in production environment")
        print("This script is designed for production Kubernetes deployments")

    try:
        from backend.app.core.config import settings
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text

        print(f"🔗 Database URL: {settings.DATABASE_URL}")
        print("🔧 Attempting to fix migration state...")

        # Create engine
        engine = create_async_engine(settings.DATABASE_URL, echo=False)

        async with engine.connect() as conn:
            # Check current state
            result = await conn.execute(text("SELECT version_num FROM alembic_version"))
            current_versions = [row[0] for row in result.fetchall()]
            print(f"📌 Current Alembic version: {current_versions}")

            # Check if families table exists
            result = await conn.execute(text("SHOW TABLES LIKE 'families'"))
            families_exists = bool(result.fetchone())
            print(f"✅ families table exists: {families_exists}")

            if not families_exists:
                print("❌ families table doesn't exist - this script is not needed")
                return False

            # Check if already at head
            head_migration = "a988bdaeacef"
            if head_migration in current_versions:
                print(f"✅ Already at head revision - no fix needed")
                return True

            print(f"\n🔧 Updating to head revision: {head_migration}")

            # Update alembic version
            await conn.execute(
                text("UPDATE alembic_version SET version_num = :version"),
                {"version": head_migration}
            )
            await conn.commit()

            print("✅ Migration state updated successfully")
            print("💡 Alembic migrations should now work correctly")

            return True

        await engine.dispose()

    except Exception as e:
        print(f"❌ Production migration fix failed: {e}")
        print("🚨 Manual intervention may be required")
        return False

if __name__ == "__main__":
    print("Running production migration state fix...")
    success = asyncio.run(production_migration_fix())

    if success:
        print("\n🎉 Production migration fix completed successfully!")
        print("You can now redeploy the application and migrations should work.")
        sys.exit(0)
    else:
        print("\n💥 Production migration fix failed!")
        print("Check the database state manually or contact support.")
        sys.exit(1)