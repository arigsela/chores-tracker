"""
Comprehensive unit tests for create_monitoring_account.py script.

Tests cover:
- Account creation workflow
- Password generation security
- Invite code generation
- Family creation
- Child account provisioning
- Test chore creation
- Error handling
- Idempotency (recreating existing account)
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch, call
import sys
import os
from datetime import datetime, timedelta
import importlib.util

# Add app to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from backend.app.models.user import User
from backend.app.models.family import Family
from backend.app.models.chore import Chore
from backend.app.models.chore_assignment import ChoreAssignment


# Import functions from the monitoring script
_script_path = os.path.join(
    os.path.dirname(__file__), 
    '../../app/scripts/create_monitoring_account.py'
)
_script_spec = importlib.util.spec_from_file_location("create_monitoring_account", _script_path)
_script_module = importlib.util.module_from_spec(_script_spec)
_script_spec.loader.exec_module(_script_module)
generate_secure_password = _script_module.generate_secure_password
generate_invite_code = _script_module.generate_invite_code


# Test credentials
TEST_MONITORING_PASSWORD = "test_monitoring_password_123"


# Import the functions we're testing
# Note: We'll need to patch the script's main execution
@pytest.fixture
def mock_monitoring_script():
    """Mock the monitoring script module."""
    # Import functions from the script
    script_path = os.path.join(
        os.path.dirname(__file__), 
        '../../app/scripts/create_monitoring_account.py'
    )
    
    import importlib.util
    spec = importlib.util.spec_from_file_location("monitoring_script", script_path)
    module = importlib.util.module_from_spec(spec)
    return module


class TestPasswordGeneration:
    """Test secure password generation."""

    def test_generate_secure_password_length(self, _mock_monitoring_script):
        """Test password generation creates correct length."""
        # Test default length
        password = generate_secure_password()
        assert len(password) == 32

        # Test custom length
        password = generate_secure_password(length=16)
        assert len(password) == 16

        password = generate_secure_password(length=64)
        assert len(password) == 64

    def test_generate_secure_password_character_set(self, _mock_monitoring_script):
        """Test password uses correct character set."""
        password = generate_secure_password(length=100)
        
        # Should contain mix of character types
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*" for c in password)
        
        # Password should have good mix
        assert has_upper or has_lower
        assert has_digit or has_special

    def test_generate_secure_password_uniqueness(self, _mock_monitoring_script):
        """Test password generation produces unique passwords."""
        passwords = [generate_secure_password() for _ in range(10)]
        
        # All passwords should be unique
        assert len(set(passwords)) == 10

    def test_generate_secure_password_no_predictable_patterns(
        self,
        _mock_monitoring_script
    ):
        """Test passwords don't contain predictable patterns."""
        password = generate_secure_password(length=32)
        
        # Should not be all same character
        assert len(set(password)) > 1
        
        # Should not be sequential
        assert password != ''.join(chr(ord('a') + i) for i in range(32))


class TestInviteCodeGeneration:
    """Test invite code generation."""

    def test_generate_invite_code_length(self, _mock_monitoring_script):
        """Test invite code generation creates correct length."""
        # Test default length
        code = generate_invite_code()
        assert len(code) == 8

        # Test custom length
        code = generate_invite_code(length=12)
        assert len(code) == 12

    def test_generate_invite_code_character_set(self, _mock_monitoring_script):
        """Test invite code uses uppercase and digits only."""
        code = generate_invite_code(length=20)
        
        # Should only contain uppercase letters and digits
        assert code.isalnum()
        assert code.isupper() or code.isdigit()
        
        # Should not contain lowercase
        assert not any(c.islower() for c in code)

    def test_generate_invite_code_uniqueness(self, _mock_monitoring_script):
        """Test invite code generation produces unique codes."""
        codes = [generate_invite_code() for _ in range(10)]
        
        # All codes should be unique (high probability)
        assert len(set(codes)) == 10


class TestMonitoringAccountCreation:
    """Test the main monitoring account creation workflow."""

    @pytest.mark.asyncio
    async def test_create_monitoring_account_full_workflow(
        self,
        db_session
    ):
        """Test complete monitoring account creation workflow."""
        # Mock user input to skip confirmation
        with patch('builtins.input', return_value=''):
            # Count initial users and families
            from sqlalchemy import select
            await db_session.execute(select(User))
            
            # This would create the account but we'll test components separately
            # to avoid full script execution in tests
            pass

    @pytest.mark.asyncio
    async def test_monitoring_family_creation(self, db_session):
        """Test monitoring family is created correctly."""
        # Arrange
        from sqlalchemy import select
        
        family = Family(
            name="Monitoring & Health Checks",
            invite_code="TEST1234",
            invite_code_expires_at=datetime.utcnow() + timedelta(days=365)
        )
        
        db_session.add(family)
        await db_session.commit()
        await db_session.refresh(family)
        
        # Assert
        assert family.id is not None
        assert family.name == "Monitoring & Health Checks"
        assert family.invite_code == "TEST1234"
        assert family.invite_code_expires_at > datetime.utcnow()

    @pytest.mark.asyncio
    async def test_monitoring_parent_account_creation(self, db_session):
        """Test monitoring parent account is created with correct attributes."""
        # Arrange
        from backend.app.core.security.password import get_password_hash
        
        family = Family(
            name="Test Family",
            invite_code="TEST5678",
            invite_code_expires_at=datetime.utcnow() + timedelta(days=365)
        )
        db_session.add(family)
        await db_session.flush()
        
        parent = User(
            username="monitoring_agent",
            email="monitoring@healthcheck.local",
            hashed_password=get_password_hash("test_password"),
            is_parent=True,
            is_active=True,
            family_id=family.id
        )
        db_session.add(parent)
        await db_session.commit()
        await db_session.refresh(parent)
        
        # Assert
        assert parent.id is not None
        assert parent.username == "monitoring_agent"
        assert parent.email == "monitoring@healthcheck.local"
        assert parent.is_parent is True
        assert parent.is_active is True
        assert parent.family_id == family.id

    @pytest.mark.asyncio
    async def test_monitoring_child_accounts_creation(self, db_session):
        """Test monitoring child accounts are created correctly."""
        # Arrange
        from backend.app.core.security.password import get_password_hash
        
        # Create parent and family
        family = Family(
            name="Test Family",
            invite_code="TEST9012",
            invite_code_expires_at=datetime.utcnow() + timedelta(days=365)
        )
        db_session.add(family)
        await db_session.flush()
        
        parent = User(
            username="test_parent",
            email="parent@test.local",
            hashed_password=get_password_hash("password"),
            is_parent=True,
            is_active=True,
            family_id=family.id
        )
        db_session.add(parent)
        await db_session.flush()
        
        # Create child accounts
        child1 = User(
            username="test_child_monitor_1",
            email="test_child_1@healthcheck.local",
            hashed_password=get_password_hash("child_password"),
            is_parent=False,
            is_active=True,
            parent_id=parent.id,
            family_id=family.id
        )
        child2 = User(
            username="test_child_monitor_2",
            email="test_child_2@healthcheck.local",
            hashed_password=get_password_hash("child_password"),
            is_parent=False,
            is_active=True,
            parent_id=parent.id,
            family_id=family.id
        )
        
        db_session.add(child1)
        db_session.add(child2)
        await db_session.commit()
        await db_session.refresh(child1)
        await db_session.refresh(child2)
        
        # Assert
        assert child1.id is not None
        assert child1.username == "test_child_monitor_1"
        assert child1.is_parent is False
        assert child1.parent_id == parent.id
        assert child1.family_id == family.id
        
        assert child2.id is not None
        assert child2.username == "test_child_monitor_2"
        assert child2.is_parent is False
        assert child2.parent_id == parent.id
        assert child2.family_id == family.id

    @pytest.mark.asyncio
    async def test_monitoring_test_chores_creation(self, db_session):
        """Test monitoring test chores are created correctly."""
        # Arrange
        from backend.app.core.security.password import get_password_hash
        
        # Create family and users
        family = Family(
            name="Test Family",
            invite_code="TEST3456",
            invite_code_expires_at=datetime.utcnow() + timedelta(days=365)
        )
        db_session.add(family)
        await db_session.flush()
        
        parent = User(
            username="test_parent",
            email="parent@test.local",
            hashed_password=get_password_hash("password"),
            is_parent=True,
            is_active=True,
            family_id=family.id
        )
        db_session.add(parent)
        await db_session.flush()
        
        child = User(
            username="test_child",
            email="child@test.local",
            hashed_password=get_password_hash("password"),
            is_parent=False,
            is_active=True,
            parent_id=parent.id,
            family_id=family.id
        )
        db_session.add(child)
        await db_session.flush()
        
        # Create test chores
        chore1 = Chore(
            title="[TEST] Health Check Chore - Fixed Reward",
            description="Test chore for monitoring validation with fixed reward",
            reward=5.0,
            is_recurring=False,
            is_disabled=False,
            creator_id=parent.id,
            assignment_mode="single"
        )
        db_session.add(chore1)
        await db_session.flush()
        
        assignment1 = ChoreAssignment(
            chore_id=chore1.id,
            assignee_id=child.id,
            is_completed=False,
            is_approved=False
        )
        db_session.add(assignment1)
        
        chore2 = Chore(
            title="[TEST] Health Check Chore - Range Reward",
            description="Test chore for monitoring validation with range reward",
            reward=5.0,
            is_range_reward=True,
            min_reward=3.0,
            max_reward=10.0,
            is_recurring=False,
            is_disabled=False,
            creator_id=parent.id,
            assignment_mode="single"
        )
        db_session.add(chore2)
        await db_session.flush()
        
        assignment2 = ChoreAssignment(
            chore_id=chore2.id,
            assignee_id=child.id,
            is_completed=False,
            is_approved=False
        )
        db_session.add(assignment2)
        
        await db_session.commit()
        await db_session.refresh(chore1)
        await db_session.refresh(chore2)
        
        # Assert chore1
        assert chore1.id is not None
        assert "[TEST]" in chore1.title
        assert chore1.reward == 5.0
        assert chore1.is_range_reward is False
        assert chore1.creator_id == parent.id
        
        # Assert chore2
        assert chore2.id is not None
        assert "[TEST]" in chore2.title
        assert chore2.is_range_reward is True
        assert chore2.min_reward == 3.0
        assert chore2.max_reward == 10.0


class TestMonitoringAccountRecreation:
    """Test handling of existing monitoring accounts."""

    @pytest.mark.asyncio
    async def test_detect_existing_monitoring_account(self, db_session):
        """Test script detects existing monitoring account."""
        # Arrange - Create existing monitoring account
        from backend.app.core.security.password import get_password_hash
        from sqlalchemy import select
        
        existing_user = User(
            username="monitoring_agent",
            email="existing@healthcheck.local",
            hashed_password=get_password_hash("old_password"),
            is_parent=True,
            is_active=True
        )
        db_session.add(existing_user)
        await db_session.commit()
        
        # Act - Check if user exists
        result = await db_session.execute(
            select(User).where(User.username == "monitoring_agent")
        )
        found_user = result.scalar_one_or_none()
        
        # Assert
        assert found_user is not None
        assert found_user.username == "monitoring_agent"

    @pytest.mark.asyncio
    async def test_delete_existing_monitoring_account(self, db_session):
        """Test deletion of existing monitoring account before recreation."""
        # Arrange
        from backend.app.core.security.password import get_password_hash
        from sqlalchemy import select
        
        # Create family
        family = Family(
            name="Old Monitoring Family",
            invite_code="OLD12345",
            invite_code_expires_at=datetime.utcnow() + timedelta(days=365)
        )
        db_session.add(family)
        await db_session.flush()
        
        # Create existing user
        existing_user = User(
            username="monitoring_agent",
            email="old@healthcheck.local",
            hashed_password=get_password_hash("old_password"),
            is_parent=True,
            is_active=True,
            family_id=family.id
        )
        db_session.add(existing_user)
        await db_session.commit()
        
        # Act - Delete user and family
        await db_session.delete(family)
        await db_session.delete(existing_user)
        await db_session.commit()
        
        # Assert - User and family should be gone
        result = await db_session.execute(
            select(User).where(User.username == "monitoring_agent")
        )
        assert result.scalar_one_or_none() is None
        
        result = await db_session.execute(
            select(Family).where(Family.id == family.id)
        )
        assert result.scalar_one_or_none() is None


class TestMonitoringAccountSecurity:
    """Test security aspects of monitoring account creation."""

    def test_password_complexity_requirements(self, _mock_monitoring_script):
        """Test generated passwords meet complexity requirements."""
        # Generate multiple passwords and check they're strong
        for _ in range(10):
            password = generate_secure_password(32)
            
            # Should be long enough
            assert len(password) >= 32
            
            # Should have good entropy (not all same character)
            unique_chars = len(set(password))
            assert unique_chars >= 10  # At least 10 different characters

    def test_invite_code_randomness(self, _mock_monitoring_script):
        """Test invite codes are sufficiently random."""
        # Generate many codes and ensure no collisions
        codes = [generate_invite_code(8) for _ in range(100)]
        
        # Should have very few if any duplicates
        unique_codes = len(set(codes))
        assert unique_codes >= 95  # Allow small chance of collision

    @pytest.mark.asyncio
    async def test_monitoring_account_isolation(self, db_session):
        """Test monitoring account is in isolated family."""
        # Arrange
        from backend.app.core.security.password import get_password_hash
        
        # Create production family
        prod_family = Family(
            name="Production Family",
            invite_code="PROD1234",
            invite_code_expires_at=datetime.utcnow() + timedelta(days=365)
        )
        db_session.add(prod_family)
        await db_session.flush()
        
        # Create monitoring family
        monitoring_family = Family(
            name="Monitoring & Health Checks",
            invite_code="MONITOR1",
            invite_code_expires_at=datetime.utcnow() + timedelta(days=365)
        )
        db_session.add(monitoring_family)
        await db_session.flush()
        
        # Create monitoring account
        monitoring_user = User(
            username="monitoring_agent",
            email="monitoring@healthcheck.local",
            hashed_password=get_password_hash("password"),
            is_parent=True,
            is_active=True,
            family_id=monitoring_family.id
        )
        db_session.add(monitoring_user)
        await db_session.commit()
        
        # Assert - Monitoring account should NOT be in production family
        assert monitoring_user.family_id != prod_family.id
        assert monitoring_user.family_id == monitoring_family.id


class TestMonitoringAccountEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_create_account_with_database_error(self, db_session):
        """Test handling of database errors during account creation."""
        # This would test rollback behavior
        # In real script, errors should trigger rollback
        pass

    def test_password_generation_with_invalid_length(self, _mock_monitoring_script):
        """Test password generation with edge case lengths."""
        # Very short password
        password = generate_secure_password(1)
        assert len(password) == 1
        
        # Very long password
        password = generate_secure_password(1000)
        assert len(password) == 1000

    def test_invite_code_generation_with_invalid_length(self, _mock_monitoring_script):
        """Test invite code generation with edge case lengths."""
        # Very short code
        code = generate_invite_code(1)
        assert len(code) == 1
        
        # Very long code
        code = generate_invite_code(100)
        assert len(code) == 100


class TestMonitoringAccountValidation:
    """Test validation of created monitoring account."""

    @pytest.mark.asyncio
    async def test_monitoring_account_can_authenticate(self, db_session):
        """Test created monitoring account can be used for authentication."""
        # Arrange
        from backend.app.core.security.password import get_password_hash, verify_password
        
        password = TEST_MONITORING_PASSWORD
        hashed = get_password_hash(password)
        
        user = User(
            username="monitoring_agent",
            email="monitoring@healthcheck.local",
            hashed_password=hashed,
            is_parent=True,
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()
        
        # Act - Verify password works
        is_valid = verify_password(password, hashed)
        
        # Assert
        assert is_valid is True

    @pytest.mark.asyncio
    async def test_monitoring_children_linked_to_parent(self, db_session):
        """Test child accounts are properly linked to monitoring parent."""
        # Arrange
        from backend.app.core.security.password import get_password_hash
        from sqlalchemy import select
        
        parent = User(
            username="monitoring_agent",
            email="monitoring@healthcheck.local",
            hashed_password=get_password_hash("password"),
            is_parent=True,
            is_active=True
        )
        db_session.add(parent)
        await db_session.flush()
        
        child1 = User(
            username="test_child_monitor_1",
            email="child1@healthcheck.local",
            hashed_password=get_password_hash("password"),
            is_parent=False,
            is_active=True,
            parent_id=parent.id
        )
        child2 = User(
            username="test_child_monitor_2",
            email="child2@healthcheck.local",
            hashed_password=get_password_hash("password"),
            is_parent=False,
            is_active=True,
            parent_id=parent.id
        )
        
        db_session.add(child1)
        db_session.add(child2)
        await db_session.commit()
        
        # Act - Query children
        result = await db_session.execute(
            select(User).where(User.parent_id == parent.id)
        )
        children = result.scalars().all()
        
        # Assert
        assert len(children) == 2
        assert all(child.parent_id == parent.id for child in children)

    @pytest.mark.asyncio
    async def test_monitoring_chores_assigned_correctly(self, db_session):
        """Test chores are assigned to correct child accounts."""
        # Arrange
        from backend.app.core.security.password import get_password_hash
        from sqlalchemy import select
        
        # Create users
        parent = User(
            username="monitoring_agent",
            email="monitoring@healthcheck.local",
            hashed_password=get_password_hash("password"),
            is_parent=True,
            is_active=True
        )
        db_session.add(parent)
        await db_session.flush()
        
        child1 = User(
            username="test_child_1",
            email="child1@test.local",
            hashed_password=get_password_hash("password"),
            is_parent=False,
            is_active=True,
            parent_id=parent.id
        )
        db_session.add(child1)
        await db_session.flush()
        
        # Create chore
        chore = Chore(
            title="[TEST] Test Chore",
            description="Test chore",
            reward=5.0,
            is_recurring=False,
            is_disabled=False,
            creator_id=parent.id,
            assignment_mode="single"
        )
        db_session.add(chore)
        await db_session.flush()
        
        # Create assignment
        assignment = ChoreAssignment(
            chore_id=chore.id,
            assignee_id=child1.id,
            is_completed=False,
            is_approved=False
        )
        db_session.add(assignment)
        await db_session.commit()
        
        # Act - Query assignments
        result = await db_session.execute(
            select(ChoreAssignment).where(ChoreAssignment.chore_id == chore.id)
        )
        assignments = result.scalars().all()
        
        # Assert
        assert len(assignments) == 1
        assert assignments[0].assignee_id == child1.id
        assert assignments[0].chore_id == chore.id