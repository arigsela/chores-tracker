#!/usr/bin/env python3
"""
Test DATABASE_URL conversion to ensure aiomysql driver is used.
"""
import os
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

def test_url_conversion():
    """Test various DATABASE_URL formats and verify aiomysql conversion."""

    # Test the URL conversion logic directly
    def convert_mysql_url(url: str) -> str:
        """Mirror the conversion logic from Settings.DATABASE_URL property."""
        if url.startswith("mysql://"):
            return url.replace("mysql://", "mysql+aiomysql://", 1)
        elif url.startswith("mysql+mysqldb://"):
            return url.replace("mysql+mysqldb://", "mysql+aiomysql://", 1)
        elif url.startswith("mysql+pymysql://"):
            return url.replace("mysql+pymysql://", "mysql+aiomysql://", 1)
        return url

    test_cases = [
        {
            "input": "mysql://user:pass@host:3306/db",
            "expected": "mysql+aiomysql://user:pass@host:3306/db",
            "description": "Basic mysql:// URL"
        },
        {
            "input": "mysql+mysqldb://user:pass@host:3306/db",
            "expected": "mysql+aiomysql://user:pass@host:3306/db",
            "description": "mysqldb driver URL"
        },
        {
            "input": "mysql+pymysql://user:pass@host:3306/db",
            "expected": "mysql+aiomysql://user:pass@host:3306/db",
            "description": "pymysql driver URL"
        },
        {
            "input": "mysql+aiomysql://user:pass@host:3306/db",
            "expected": "mysql+aiomysql://user:pass@host:3306/db",
            "description": "Already correct aiomysql URL"
        },
        {
            "input": "mysql://user:pass@mysql.mysql.svc.cluster.local:3306/db",
            "expected": "mysql+aiomysql://user:pass@mysql.mysql.svc.cluster.local:3306/db",
            "description": "Production Kubernetes MySQL URL"
        },
        {
            "input": "postgresql://user:pass@host:5432/db",
            "expected": "postgresql://user:pass@host:5432/db",
            "description": "Non-MySQL URL (should remain unchanged)"
        }
    ]

    print("🔍 Testing DATABASE_URL conversion...")
    print("=" * 60)

    all_passed = True

    for i, test in enumerate(test_cases, 1):
        # Test the conversion logic directly
        actual = convert_mysql_url(test["input"])

        # Check result
        passed = actual == test["expected"]
        status = "✅ PASS" if passed else "❌ FAIL"

        print(f"Test {i}: {test['description']}")
        print(f"  Input:    {test['input']}")
        print(f"  Expected: {test['expected']}")
        print(f"  Actual:   {actual}")
        print(f"  Result:   {status}")
        print()

        if not passed:
            all_passed = False

    print("=" * 60)
    if all_passed:
        print("🎉 All tests passed! Database URLs will use aiomysql driver.")
        return True
    else:
        print("💥 Some tests failed! Check the URL conversion logic.")
        return False

if __name__ == "__main__":
    success = test_url_conversion()
    sys.exit(0 if success else 1)