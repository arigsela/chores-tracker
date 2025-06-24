"""
Test Unit of Work edge cases and error handling.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import Mock, AsyncMock, patch

from backend.app.core.unit_of_work import UnitOfWork, get_unit_of_work
from backend.app.models.user import User
from backend.app.models.chore import Chore


class TestUnitOfWorkEdgeCases:
    """Test Unit of Work edge cases and error scenarios."""
    
    @pytest.mark.asyncio
    async def test_unit_of_work_properties(self):
        """Test UnitOfWork property accessors."""
        uow = UnitOfWork()
        
        # Test repository properties before entering context
        assert uow._users is None
        assert uow._chores is None
        
        # Access properties - should create instances
        users_repo = uow.users
        chores_repo = uow.chores
        
        assert users_repo is not None
        assert chores_repo is not None
        
        # Access again - should return same instances
        assert uow.users is users_repo
        assert uow.chores is chores_repo
    
    @pytest.mark.asyncio
    async def test_unit_of_work_manual_rollback(self):
        """Test manual rollback functionality."""
        uow = UnitOfWork()
        
        async with uow:
            # Mock the session
            uow.session = AsyncMock()
            
            # Call rollback
            await uow.rollback()
            
            # Verify rollback was called
            uow.session.rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_unit_of_work_close_without_session(self):
        """Test closing UnitOfWork without active session."""
        uow = UnitOfWork()
        
        # Close without entering context (no session)
        await uow.close()  # Should not raise error
        
        assert uow.session is None
    
    @pytest.mark.asyncio
    async def test_unit_of_work_exception_handling(self):
        """Test UnitOfWork handles exceptions properly."""
        uow = UnitOfWork()
        mock_session = AsyncMock()
        
        with pytest.raises(ValueError):
            async with uow:
                # Mock the session
                uow.session = mock_session
                
                # Raise an exception
                raise ValueError("Test error")
        
        # Verify rollback was called due to exception
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_unit_of_work_commit_without_session(self):
        """Test committing without active session."""
        uow = UnitOfWork()
        
        # Try to commit without session
        await uow.commit()  # Should not raise error
    
    @pytest.mark.asyncio
    async def test_unit_of_work_rollback_without_session(self):
        """Test rollback without active session."""
        uow = UnitOfWork()
        
        # Try to rollback without session
        await uow.rollback()  # Should not raise error
    
    @pytest.mark.asyncio
    async def test_get_unit_of_work_context_manager(self):
        """Test get_unit_of_work dependency function."""
        # Test the context manager
        async with get_unit_of_work() as uow:
            assert isinstance(uow, UnitOfWork)
            # Mock session to test functionality
            uow.session = AsyncMock()
    
    @pytest.mark.asyncio
    async def test_unit_of_work_nested_transactions(self):
        """Test UnitOfWork behavior with nested operations."""
        uow = UnitOfWork()
        
        async with uow:
            # Mock the session
            uow.session = AsyncMock()
            
            # Simulate nested operations
            user_repo = uow.users
            chore_repo = uow.chores
            
            # Both should use the same session
            assert user_repo is not None
            assert chore_repo is not None
            
            # Commit once
            await uow.commit()
            
            # Session commit should be called once
            uow.session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_unit_of_work_session_factory_custom(self):
        """Test UnitOfWork with custom session factory."""
        # Create mock session factory
        mock_session = AsyncMock()
        mock_factory = Mock(return_value=mock_session)
        
        # Create UoW with custom factory
        uow = UnitOfWork(session_factory=mock_factory)
        
        async with uow:
            # Verify custom factory was used
            mock_factory.assert_called_once()
            assert uow.session is mock_session
    
    @pytest.mark.asyncio
    async def test_unit_of_work_multiple_commits(self):
        """Test multiple commits within same UnitOfWork."""
        uow = UnitOfWork()
        
        async with uow:
            # Mock the session
            uow.session = AsyncMock()
            
            # First commit
            await uow.commit()
            
            # Second commit
            await uow.commit()
            
            # Both commits should work
            assert uow.session.commit.call_count == 2
    
    @pytest.mark.asyncio
    async def test_unit_of_work_rollback_then_commit(self):
        """Test rollback followed by commit."""
        uow = UnitOfWork()
        
        async with uow:
            # Mock the session
            uow.session = AsyncMock()
            
            # Rollback first
            await uow.rollback()
            
            # Then commit
            await uow.commit()
            
            # Both should be called
            uow.session.rollback.assert_called_once()
            uow.session.commit.assert_called_once()