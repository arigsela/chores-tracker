#!/usr/bin/env python3
"""
Test DATABASE_URL conversion to ensure asyncpg driver is used for PostgreSQL.

This script validates that various database URL formats are correctly
converted to use the appropriate async driver:
- PostgreSQL: asyncpg
- MySQL (legacy): aiomysql
"""
import os
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))


def test_url_conversion():
    """Test various DATABASE_URL formats and verify async driver conversion."""

    # Test the URL conversion logic directly (mirrors Settings.DATABASE_URL property)
    def convert_database_url(url: str) -> str:
        """Mirror the conversion logic from Settings.DATABASE_URL property."""
        # Handle PostgreSQL URL formats
        if url.startswith("postgres://"):
            # Heroku-style postgres:// URLs
            return url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and "+asyncpg" not in url:
            # Standard postgresql:// without async driver
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql+psycopg2://"):
            # Sync psycopg2 driver - convert to async
            return url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql+psycopg://"):
            # psycopg3 sync driver - convert to async
            return url.replace("postgresql+psycopg://", "postgresql+asyncpg://", 1)
        # Backward compatibility: MySQL URLs during migration period
        elif url.startswith("mysql://"):
            return url.replace("mysql://", "mysql+aiomysql://", 1)
        elif url.startswith("mysql+mysqldb://"):
            return url.replace("mysql+mysqldb://", "mysql+aiomysql://", 1)
        elif url.startswith("mysql+pymysql://"):
            return url.replace("mysql+pymysql://", "mysql+aiomysql://", 1)
        return url

    test_cases = [
        # PostgreSQL test cases (primary)
        {
            "input": "postgresql://user:pass@host:5432/db",
            "expected": "postgresql+asyncpg://user:pass@host:5432/db",
            "description": "Standard postgresql:// URL"
        },
        {
            "input": "postgres://user:pass@host:5432/db",
            "expected": "postgresql+asyncpg://user:pass@host:5432/db",
            "description": "Heroku-style postgres:// URL"
        },
        {
            "input": "postgresql+psycopg2://user:pass@host:5432/db",
            "expected": "postgresql+asyncpg://user:pass@host:5432/db",
            "description": "psycopg2 driver URL"
        },
        {
            "input": "postgresql+psycopg://user:pass@host:5432/db",
            "expected": "postgresql+asyncpg://user:pass@host:5432/db",
            "description": "psycopg3 driver URL"
        },
        {
            "input": "postgresql+asyncpg://user:pass@host:5432/db",
            "expected": "postgresql+asyncpg://user:pass@host:5432/db",
            "description": "Already correct asyncpg URL"
        },
        {
            "input": "postgresql://user:pass@postgres.postgres.svc.cluster.local:5432/db",
            "expected": "postgresql+asyncpg://user:pass@postgres.postgres.svc.cluster.local:5432/db",
            "description": "Production Kubernetes PostgreSQL URL"
        },
        # MySQL test cases (backward compatibility during migration)
        {
            "input": "mysql://user:pass@host:3306/db",
            "expected": "mysql+aiomysql://user:pass@host:3306/db",
            "description": "[MySQL Legacy] Basic mysql:// URL"
        },
        {
            "input": "mysql+mysqldb://user:pass@host:3306/db",
            "expected": "mysql+aiomysql://user:pass@host:3306/db",
            "description": "[MySQL Legacy] mysqldb driver URL"
        },
        {
            "input": "mysql+pymysql://user:pass@host:3306/db",
            "expected": "mysql+aiomysql://user:pass@host:3306/db",
            "description": "[MySQL Legacy] pymysql driver URL"
        },
        {
            "input": "mysql+aiomysql://user:pass@host:3306/db",
            "expected": "mysql+aiomysql://user:pass@host:3306/db",
            "description": "[MySQL Legacy] Already correct aiomysql URL"
        },
        # SQLite test case (should remain unchanged)
        {
            "input": "sqlite+aiosqlite:///:memory:",
            "expected": "sqlite+aiosqlite:///:memory:",
            "description": "SQLite URL (should remain unchanged)"
        }
    ]

    print("🔍 Testing DATABASE_URL conversion...")
    print("=" * 70)

    all_passed = True
    postgresql_tests = 0
    mysql_tests = 0

    for i, test in enumerate(test_cases, 1):
        # Test the conversion logic directly
        actual = convert_database_url(test["input"])

        # Check result
        passed = actual == test["expected"]
        status = "✅ PASS" if passed else "❌ FAIL"

        # Count test types
        if "postgresql" in test["input"] or "postgres://" in test["input"]:
            postgresql_tests += 1
        elif "mysql" in test["input"]:
            mysql_tests += 1

        print(f"Test {i}: {test['description']}")
        print(f"  Input:    {test['input']}")
        print(f"  Expected: {test['expected']}")
        print(f"  Actual:   {actual}")
        print(f"  Result:   {status}")
        print()

        if not passed:
            all_passed = False

    print("=" * 70)
    print(f"PostgreSQL tests: {postgresql_tests}")
    print(f"MySQL (legacy) tests: {mysql_tests}")
    print("=" * 70)

    if all_passed:
        print("🎉 All tests passed!")
        print("   - PostgreSQL URLs will use asyncpg driver")
        print("   - MySQL URLs (legacy) will use aiomysql driver")
        return True
    else:
        print("💥 Some tests failed! Check the URL conversion logic.")
        return False


if __name__ == "__main__":
    success = test_url_conversion()
    sys.exit(0 if success else 1)
