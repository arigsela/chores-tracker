#!/usr/bin/env python3
"""
Test database connection script for debugging MySQL connectivity issues.
"""
import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def test_connection():
    """Test database connection with detailed error reporting."""
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        return False

    print(f"🔍 Testing connection to: {database_url}")

    try:
        # Create engine
        engine = create_async_engine(database_url, echo=True)

        # Test connection
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT VERSION() as version"))
            version = result.fetchone()
            print(f"✅ Successfully connected to MySQL!")
            print(f"📋 Database version: {version[0]}")

        await engine.dispose()
        return True

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print(f"🔧 Error type: {type(e).__name__}")

        # Provide specific troubleshooting based on error type
        if "asyncio extension requires an async driver" in str(e):
            print("\n🔧 TROUBLESHOOTING:")
            print("   - Remove mysqlclient and pymysql from requirements.txt")
            print("   - Ensure only aiomysql is installed for async MySQL support")
            print("   - Rebuild Docker container after changes")

        elif "Authentication plugin" in str(e):
            print("\n🔧 TROUBLESHOOTING:")
            print("   - Add --default-authentication-plugin=mysql_native_password to MySQL command")
            print("   - Or use caching_sha2_password authentication")

        elif "Connection refused" in str(e):
            print("\n🔧 TROUBLESHOOTING:")
            print("   - Ensure MySQL service is running")
            print("   - Check if port 3306 is accessible")
            print("   - Verify host/port in DATABASE_URL")

        return False

if __name__ == "__main__":
    success = asyncio.run(test_connection())
    sys.exit(0 if success else 1)