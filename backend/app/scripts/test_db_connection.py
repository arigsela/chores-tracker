#!/usr/bin/env python3
"""
Test database connection script for debugging PostgreSQL connectivity issues.
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
        print("DATABASE_URL environment variable not set")
        return False

    print(f"Testing connection to: {database_url}")

    try:
        # Create engine
        engine = create_async_engine(database_url, echo=True)

        # Test connection
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version() as version"))
            version = result.fetchone()
            print("Successfully connected to PostgreSQL!")
            print(f"Database version: {version[0]}")

        await engine.dispose()
        return True

    except Exception as e:
        print(f"Connection failed: {e}")
        print(f"Error type: {type(e).__name__}")

        # Provide specific troubleshooting based on error type
        if "asyncio extension requires an async driver" in str(e):
            print("\nTROUBLESHOOTING:")
            print("   - Ensure asyncpg is installed for async PostgreSQL support")
            print("   - Rebuild Docker container after changes")

        elif "password authentication failed" in str(e):
            print("\nTROUBLESHOOTING:")
            print("   - Check POSTGRES_USER and POSTGRES_PASSWORD in .env")
            print("   - Verify pg_hba.conf allows the connection method")

        elif "Connection refused" in str(e):
            print("\nTROUBLESHOOTING:")
            print("   - Ensure PostgreSQL service is running")
            print("   - Check if port 5432 is accessible")
            print("   - Verify host/port in DATABASE_URL")

        elif "database" in str(e).lower() and "does not exist" in str(e).lower():
            print("\nTROUBLESHOOTING:")
            print("   - Check POSTGRES_DB in .env")
            print("   - Create the database if it doesn't exist")

        return False


if __name__ == "__main__":
    success = asyncio.run(test_connection())
    sys.exit(0 if success else 1)
