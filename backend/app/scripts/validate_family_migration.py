#!/usr/bin/env python3
"""
Family Migration Validation Script

This script validates the family migration has been applied correctly
and all data integrity constraints are satisfied.

Usage:
    python -m backend.app.scripts.validate_family_migration
"""

import asyncio
import sys
from typing import Dict, List, Any
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.base import get_db
from backend.app.models import Family, User


class FamilyMigrationValidator:
    """Validates the family migration data integrity and completeness."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.stats: Dict[str, Any] = {}

    async def validate_all(self) -> bool:
        """Run all validation checks. Returns True if all checks pass."""
        print("🔍 Starting Family Migration Validation...\n")
        
        await self._validate_basic_counts()
        await self._validate_family_structure()
        await self._validate_user_assignments()
        await self._validate_invite_codes()
        await self._validate_orphaned_data()
        await self._validate_parent_child_consistency()
        await self._validate_data_types()
        await self._performance_check()
        
        self._print_summary()
        
        return len(self.errors) == 0

    async def _validate_basic_counts(self):
        """Validate basic table counts and relationships."""
        print("📊 Validating basic counts...")
        
        # Get total user count
        result = await self.db.execute(select(func.count(User.id)))
        total_users = result.scalar()
        self.stats['total_users'] = total_users
        
        # Get users with families
        result = await self.db.execute(select(func.count(User.id)).where(User.family_id.isnot(None)))
        users_with_families = result.scalar()
        self.stats['users_with_families'] = users_with_families
        
        # Get total families
        result = await self.db.execute(select(func.count(Family.id)))
        total_families = result.scalar()
        self.stats['total_families'] = total_families
        
        # Get parent users
        result = await self.db.execute(select(func.count(User.id)).where(User.is_parent == True))
        total_parents = result.scalar()
        self.stats['total_parents'] = total_parents
        
        print(f"  ✓ Total users: {total_users}")
        print(f"  ✓ Users with families: {users_with_families}")
        print(f"  ✓ Total families: {total_families}")
        print(f"  ✓ Total parents: {total_parents}")
        
        # Validation checks
        if users_with_families != total_users:
            self.errors.append(f"Not all users have families: {users_with_families}/{total_users}")
        
        if total_families == 0:
            self.errors.append("No families found after migration")

    async def _validate_family_structure(self):
        """Validate family structure and membership."""
        print("\n🏠 Validating family structure...")
        
        # Check each family has at least one parent
        result = await self.db.execute(text("""
            SELECT f.id, f.name, COUNT(u.id) as member_count,
                   SUM(CASE WHEN u.is_parent = 1 THEN 1 ELSE 0 END) as parent_count,
                   SUM(CASE WHEN u.is_parent = 0 THEN 1 ELSE 0 END) as child_count
            FROM families f
            LEFT JOIN users u ON u.family_id = f.id
            GROUP BY f.id, f.name
        """))
        
        families_without_parents = 0
        families_without_members = 0
        
        for row in result:
            family_id, name, member_count, parent_count, child_count = row
            
            if member_count == 0:
                families_without_members += 1
                self.errors.append(f"Family '{name}' (ID: {family_id}) has no members")
            
            if parent_count == 0:
                families_without_parents += 1
                self.errors.append(f"Family '{name}' (ID: {family_id}) has no parents")
        
        print(f"  ✓ Families without members: {families_without_members}")
        print(f"  ✓ Families without parents: {families_without_parents}")
        
        self.stats['families_without_members'] = families_without_members
        self.stats['families_without_parents'] = families_without_parents

    async def _validate_user_assignments(self):
        """Validate user family assignments are correct."""
        print("\n👥 Validating user family assignments...")
        
        # Check for users with invalid family_id references
        result = await self.db.execute(text("""
            SELECT COUNT(*) 
            FROM users u
            LEFT JOIN families f ON u.family_id = f.id
            WHERE u.family_id IS NOT NULL AND f.id IS NULL
        """))
        invalid_family_refs = result.scalar()
        
        if invalid_family_refs > 0:
            self.errors.append(f"Found {invalid_family_refs} users with invalid family_id references")
        
        # Check parent-child family consistency
        result = await self.db.execute(text("""
            SELECT COUNT(*)
            FROM users c
            JOIN users p ON c.parent_id = p.id
            WHERE c.family_id != p.family_id
        """))
        inconsistent_families = result.scalar()
        
        if inconsistent_families > 0:
            self.errors.append(f"Found {inconsistent_families} children not in same family as their parent")
        
        print(f"  ✓ Invalid family references: {invalid_family_refs}")
        print(f"  ✓ Parent-child family mismatches: {inconsistent_families}")

    async def _validate_invite_codes(self):
        """Validate invite code uniqueness and format."""
        print("\n🔗 Validating invite codes...")
        
        # Check for duplicate invite codes
        result = await self.db.execute(text("""
            SELECT invite_code, COUNT(*) as count
            FROM families
            GROUP BY invite_code
            HAVING COUNT(*) > 1
        """))
        
        duplicate_codes = result.fetchall()
        if duplicate_codes:
            self.errors.append(f"Found {len(duplicate_codes)} duplicate invite codes")
            for code, count in duplicate_codes:
                self.errors.append(f"  Duplicate code: {code} (used {count} times)")
        
        # Check invite code format (should be 8 characters, uppercase alphanumeric)
        result = await self.db.execute(text("""
            SELECT COUNT(*)
            FROM families
            WHERE LENGTH(invite_code) != 8 
               OR invite_code != UPPER(invite_code)
               OR invite_code REGEXP '[^A-Z0-9]'
        """))
        invalid_format_codes = result.scalar()
        
        if invalid_format_codes > 0:
            self.warnings.append(f"Found {invalid_format_codes} invite codes with invalid format")
        
        print(f"  ✓ Duplicate invite codes: {len(duplicate_codes)}")
        print(f"  ✓ Invalid format codes: {invalid_format_codes}")

    async def _validate_orphaned_data(self):
        """Check for orphaned users or data inconsistencies."""
        print("\n🔍 Checking for orphaned data...")
        
        # Users without families (should be 0 after migration)
        result = await self.db.execute(select(func.count(User.id)).where(User.family_id.is_(None)))
        orphaned_users = result.scalar()
        
        if orphaned_users > 0:
            self.errors.append(f"Found {orphaned_users} users without family assignments")
            
            # Get details of orphaned users
            result = await self.db.execute(
                select(User.id, User.username, User.is_parent, User.parent_id)
                .where(User.family_id.is_(None))
            )
            for user in result:
                self.errors.append(f"  Orphaned user: {user.username} (ID: {user.id}, Parent: {user.is_parent})")
        
        # Empty families (families with no users)
        result = await self.db.execute(text("""
            SELECT COUNT(*)
            FROM families f
            LEFT JOIN users u ON u.family_id = f.id
            WHERE u.id IS NULL
        """))
        empty_families = result.scalar()
        
        if empty_families > 0:
            self.warnings.append(f"Found {empty_families} empty families")
        
        print(f"  ✓ Orphaned users: {orphaned_users}")
        print(f"  ✓ Empty families: {empty_families}")

    async def _validate_parent_child_consistency(self):
        """Validate parent-child relationships are consistent with family structure."""
        print("\n👨‍👩‍👧‍👦 Validating parent-child consistency...")
        
        # Children should be in the same family as their parent
        result = await self.db.execute(text("""
            SELECT c.username as child, p.username as parent, c.family_id as child_family, p.family_id as parent_family
            FROM users c
            JOIN users p ON c.parent_id = p.id
            WHERE c.family_id != p.family_id
        """))
        
        mismatched_families = result.fetchall()
        if mismatched_families:
            self.errors.append(f"Found {len(mismatched_families)} parent-child pairs in different families:")
            for child, parent, child_family, parent_family in mismatched_families:
                self.errors.append(f"  {child} (family {child_family}) -> {parent} (family {parent_family})")
        
        # Parents should be in families they created (based on family name)
        result = await self.db.execute(text("""
            SELECT u.username, f.name, f.id
            FROM users u
            JOIN families f ON u.family_id = f.id
            WHERE u.is_parent = 1 
              AND u.parent_id IS NULL 
              AND f.name != CONCAT(u.username, '''s Family')
        """))
        
        mismatched_names = result.fetchall()
        if mismatched_names:
            self.warnings.append(f"Found {len(mismatched_names)} parents not in their expected families:")
            for username, family_name, family_id in mismatched_names:
                self.warnings.append(f"  {username} in '{family_name}' (expected '{username}'s Family')")
        
        print(f"  ✓ Family mismatches: {len(mismatched_families)}")
        print(f"  ✓ Name mismatches: {len(mismatched_names)}")

    async def _validate_data_types(self):
        """Validate data types and constraints."""
        print("\n🔧 Validating data types and constraints...")
        
        # Check for NULL family names (should be allowed but track them)
        result = await self.db.execute(select(func.count(Family.id)).where(Family.name.is_(None)))
        null_family_names = result.scalar()
        
        # Check for expired invite codes (should be NULL initially)
        result = await self.db.execute(select(func.count(Family.id)).where(Family.invite_code_expires_at.isnot(None)))
        families_with_expiry = result.scalar()
        
        print(f"  ✓ Families with NULL names: {null_family_names}")
        print(f"  ✓ Families with expiry dates: {families_with_expiry}")
        
        if null_family_names > 0:
            self.warnings.append(f"Found {null_family_names} families with NULL names")

    async def _performance_check(self):
        """Check query performance with new family structure."""
        print("\n⚡ Running performance checks...")
        
        # Test family-based user query performance
        import time
        
        start_time = time.time()
        result = await self.db.execute(text("""
            SELECT f.name, COUNT(u.id) as member_count
            FROM families f
            LEFT JOIN users u ON u.family_id = f.id
            GROUP BY f.id, f.name
            ORDER BY member_count DESC
            LIMIT 10
        """))
        family_query_time = time.time() - start_time
        
        # Test parent-child query performance
        start_time = time.time()
        result = await self.db.execute(text("""
            SELECT p.username as parent, COUNT(c.id) as child_count
            FROM users p
            LEFT JOIN users c ON c.parent_id = p.id
            WHERE p.is_parent = 1
            GROUP BY p.id, p.username
            ORDER BY child_count DESC
            LIMIT 10
        """))
        parent_child_query_time = time.time() - start_time
        
        print(f"  ✓ Family query time: {family_query_time:.3f}s")
        print(f"  ✓ Parent-child query time: {parent_child_query_time:.3f}s")
        
        self.stats['family_query_time'] = family_query_time
        self.stats['parent_child_query_time'] = parent_child_query_time
        
        if family_query_time > 0.5:
            self.warnings.append(f"Family query is slow: {family_query_time:.3f}s")

    def _print_summary(self):
        """Print validation summary."""
        print("\n" + "="*60)
        print("📋 FAMILY MIGRATION VALIDATION SUMMARY")
        print("="*60)
        
        print(f"\n📊 Statistics:")
        for key, value in self.stats.items():
            if isinstance(value, float):
                print(f"  • {key.replace('_', ' ').title()}: {value:.3f}")
            else:
                print(f"  • {key.replace('_', ' ').title()}: {value}")
        
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"  • {error}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        if not self.errors and not self.warnings:
            print("\n✅ ALL VALIDATION CHECKS PASSED!")
            print("The family migration has been applied successfully.")
        elif not self.errors:
            print(f"\n✅ VALIDATION PASSED WITH {len(self.warnings)} WARNINGS")
            print("The migration is functional but has minor issues to review.")
        else:
            print(f"\n❌ VALIDATION FAILED WITH {len(self.errors)} ERRORS")
            print("The migration has critical issues that must be resolved.")
        
        print("="*60)


async def main():
    """Main validation function."""
    try:
        async for db in get_db():
            validator = FamilyMigrationValidator(db)
            success = await validator.validate_all()
            
            # Exit with appropriate code
            sys.exit(0 if success else 1)
            
    except Exception as e:
        print(f"❌ Validation failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())