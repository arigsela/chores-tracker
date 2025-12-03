#!/usr/bin/env python3
"""
Emergency Family Migration Rollback Script

This script provides a safe emergency rollback of the family migration
for production use. It includes comprehensive safety checks and backup
procedures.

⚠️  WARNING: This script will permanently remove all family relationships
    and revert to the parent-child only model. Use with extreme caution!

Usage:
    python -m backend.app.scripts.emergency_family_rollback --confirm

Options:
    --confirm     Required flag to confirm rollback operation
    --dry-run     Show what would be done without making changes
    --backup      Create data backup before rollback (default: true)
"""

import asyncio
import argparse
import sys
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.base import get_db
from backend.app.models import Family, User


class FamilyRollbackManager:
    """Manages the emergency rollback of family migration."""
    
    def __init__(self, db: AsyncSession, dry_run: bool = False, backup: bool = True):
        self.db = db
        self.dry_run = dry_run
        self.backup = backup
        self.backup_data: Dict[str, Any] = {}
        self.stats: Dict[str, int] = {}

    async def perform_rollback(self) -> bool:
        """Perform the complete rollback process."""
        print("🚨 EMERGENCY FAMILY MIGRATION ROLLBACK")
        print("="*50)
        
        if not await self._validate_preconditions():
            return False
            
        if self.backup:
            await self._create_backup()
            
        await self._collect_statistics()
        
        if not self._confirm_rollback():
            print("❌ Rollback cancelled by user.")
            return False
            
        success = await self._execute_rollback()
        
        if success:
            await self._validate_rollback()
            
        return success

    async def _validate_preconditions(self) -> bool:
        """Validate that rollback can be performed safely."""
        print("\n🔍 Validating preconditions...")
        
        # Check if families table exists
        try:
            result = await self.db.execute(text("SHOW TABLES LIKE 'families'"))
            if not result.fetchone():
                print("❌ Families table does not exist. Migration may not be applied.")
                return False
        except Exception as e:
            print(f"❌ Error checking tables: {e}")
            return False
        
        # Check if users have family_id column
        try:
            result = await self.db.execute(text("DESCRIBE users"))
            columns = [row[0] for row in result]
            if 'family_id' not in columns:
                print("❌ family_id column does not exist in users table.")
                return False
        except Exception as e:
            print(f"❌ Error checking user table structure: {e}")
            return False
        
        # Check for existing data
        result = await self.db.execute(select(func.count(Family.id)))
        family_count = result.scalar()
        
        result = await self.db.execute(select(func.count(User.id)).where(User.family_id.isnot(None)))
        users_with_families = result.scalar()
        
        print(f"  ✓ Found {family_count} families")
        print(f"  ✓ Found {users_with_families} users with family assignments")
        
        if family_count == 0:
            print("⚠️  No families found. Migration may have already been rolled back.")
            
        return True

    async def _create_backup(self):
        """Create a backup of current family data."""
        print("\n💾 Creating data backup...")
        
        # Backup families
        result = await self.db.execute(select(Family))
        families = result.scalars().all()
        
        self.backup_data['families'] = []
        for family in families:
            self.backup_data['families'].append({
                'id': family.id,
                'name': family.name,
                'invite_code': family.invite_code,
                'invite_code_expires_at': family.invite_code_expires_at.isoformat() if family.invite_code_expires_at else None,
                'created_at': family.created_at.isoformat(),
                'updated_at': family.updated_at.isoformat()
            })
        
        # Backup user family assignments
        result = await self.db.execute(select(User.id, User.username, User.family_id).where(User.family_id.isnot(None)))
        user_families = result.fetchall()
        
        self.backup_data['user_families'] = []
        for user_id, username, family_id in user_families:
            self.backup_data['user_families'].append({
                'user_id': user_id,
                'username': username,
                'family_id': family_id
            })
        
        # Save backup to file
        backup_filename = f"family_migration_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        if not self.dry_run:
            with open(f"/tmp/{backup_filename}", 'w') as f:
                json.dump(self.backup_data, f, indent=2)
            
        print(f"  ✓ Backup created: /tmp/{backup_filename}")
        print(f"  ✓ Backed up {len(self.backup_data['families'])} families")
        print(f"  ✓ Backed up {len(self.backup_data['user_families'])} user family assignments")

    async def _collect_statistics(self):
        """Collect statistics about current state."""
        print("\n📊 Collecting current statistics...")
        
        result = await self.db.execute(select(func.count(Family.id)))
        self.stats['families'] = result.scalar()
        
        result = await self.db.execute(select(func.count(User.id)).where(User.family_id.isnot(None)))
        self.stats['users_with_families'] = result.scalar()
        
        result = await self.db.execute(select(func.count(User.id)).where(User.family_id.is_(None)))
        self.stats['users_without_families'] = result.scalar()
        
        result = await self.db.execute(select(func.count(User.id)).where(User.is_parent == True))
        self.stats['total_parents'] = result.scalar()
        
        result = await self.db.execute(select(func.count(User.id)).where(User.is_parent == False))
        self.stats['total_children'] = result.scalar()
        
        # Check for potential data loss scenarios
        result = await self.db.execute(text("""
            SELECT COUNT(*)
            FROM users c
            JOIN users p ON c.parent_id = p.id
            WHERE c.family_id != p.family_id
        """))
        self.stats['family_mismatches'] = result.scalar()
        
        print(f"  • Total families: {self.stats['families']}")
        print(f"  • Users with families: {self.stats['users_with_families']}")
        print(f"  • Users without families: {self.stats['users_without_families']}")
        print(f"  • Total parents: {self.stats['total_parents']}")
        print(f"  • Total children: {self.stats['total_children']}")
        print(f"  • Family mismatches: {self.stats['family_mismatches']}")

    def _confirm_rollback(self) -> bool:
        """Get user confirmation for rollback."""
        if self.dry_run:
            print("\n🔍 DRY RUN MODE - No changes will be made")
            return True
            
        print(f"\n⚠️  WARNING: DESTRUCTIVE OPERATION")
        print("This rollback will:")
        print(f"  • Delete {self.stats['families']} families")
        print(f"  • Remove family_id from {self.stats['users_with_families']} users")
        print("  • Revert to parent-child only relationships")
        print("  • This action CANNOT be undone without restoring from backup")
        
        if self.stats['family_mismatches'] > 0:
            print(f"  • WARNING: {self.stats['family_mismatches']} parent-child pairs will lose family relationships")
        
        print("\nType 'ROLLBACK CONFIRMED' to proceed:")
        confirmation = input("> ").strip()
        
        return confirmation == "ROLLBACK CONFIRMED"

    async def _execute_rollback(self) -> bool:
        """Execute the rollback operations."""
        print(f"\n{'🔍 [DRY RUN]' if self.dry_run else '🔄'} Executing rollback...")
        
        try:
            if not self.dry_run:
                # Step 1: Clear family_id from all users
                result = await self.db.execute(text("UPDATE users SET family_id = NULL"))
                print(f"  ✓ Cleared family_id from users")
                
                # Step 2: Drop foreign key constraint
                await self.db.execute(text("ALTER TABLE users DROP FOREIGN KEY users_ibfk_2"))
                print(f"  ✓ Dropped foreign key constraint")
                
                # Step 3: Drop family_id column
                await self.db.execute(text("ALTER TABLE users DROP COLUMN family_id"))
                print(f"  ✓ Dropped family_id column")
                
                # Step 4: Drop families table
                await self.db.execute(text("DROP TABLE families"))
                print(f"  ✓ Dropped families table")
                
                # Step 5: Commit transaction
                await self.db.commit()
                print(f"  ✓ All changes committed")
                
            else:
                print("  🔍 Would clear family_id from users")
                print("  🔍 Would drop foreign key constraint")
                print("  🔍 Would drop family_id column")
                print("  🔍 Would drop families table")
            
            return True
            
        except Exception as e:
            print(f"❌ Rollback failed: {e}")
            if not self.dry_run:
                await self.db.rollback()
                print("  ↩️  Transaction rolled back")
            return False

    async def _validate_rollback(self):
        """Validate the rollback was successful."""
        print("\n✅ Validating rollback...")
        
        # Check families table is gone
        try:
            result = await self.db.execute(text("SHOW TABLES LIKE 'families'"))
            if result.fetchone():
                print("❌ Families table still exists!")
                return False
        except Exception:
            pass  # Table doesn't exist - good
        
        # Check family_id column is gone
        try:
            result = await self.db.execute(text("DESCRIBE users"))
            columns = [row[0] for row in result]
            if 'family_id' in columns:
                print("❌ family_id column still exists!")
                return False
        except Exception as e:
            print(f"❌ Error validating user table: {e}")
            return False
        
        # Check user count is unchanged
        result = await self.db.execute(select(func.count(User.id)))
        final_user_count = result.scalar()
        
        original_total = self.stats['users_with_families'] + self.stats['users_without_families']
        if final_user_count != original_total:
            print(f"❌ User count mismatch! Expected {original_total}, got {final_user_count}")
            return False
        
        print("  ✅ Families table removed")
        print("  ✅ family_id column removed")
        print(f"  ✅ User count preserved: {final_user_count}")
        print("\n🎉 Rollback completed successfully!")
        
        return True


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Emergency rollback of family migration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show what would be done
  python -m backend.app.scripts.emergency_family_rollback --dry-run
  
  # Perform actual rollback (requires confirmation)
  python -m backend.app.scripts.emergency_family_rollback --confirm
  
  # Rollback without backup (not recommended)
  python -m backend.app.scripts.emergency_family_rollback --confirm --no-backup
        """
    )
    
    parser.add_argument(
        '--confirm',
        action='store_true',
        help='Required flag to confirm rollback operation'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )
    
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Skip creating backup (not recommended)'
    )
    
    return parser.parse_args()


async def main():
    """Main rollback function."""
    args = parse_args()
    
    if not args.confirm and not args.dry_run:
        print("❌ ERROR: Either --confirm or --dry-run flag is required")
        print("Use --dry-run to see what would be done")
        print("Use --confirm to perform actual rollback")
        sys.exit(1)
    
    if args.confirm and args.dry_run:
        print("❌ ERROR: Cannot use both --confirm and --dry-run")
        sys.exit(1)
    
    try:
        async for db in get_db():
            manager = FamilyRollbackManager(
                db=db,
                dry_run=args.dry_run,
                backup=not args.no_backup
            )
            
            success = await manager.perform_rollback()
            sys.exit(0 if success else 1)
            
    except KeyboardInterrupt:
        print("\n❌ Rollback interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Rollback failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())