"""
End-to-End Family Workflow Tests for Multi-Parent Family Management

These tests validate the complete user journeys for multi-parent families as specified
in the multi-parent family implementation plan Phase 5.2.

Test Scenarios:
1. Single Parent → Multi-Parent Conversion Workflow
2. New Family Creation Workflow  
3. Cross-Family Security Isolation Workflow
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.repositories.user import UserRepository
from backend.app.repositories.chore import ChoreRepository
from backend.app.services.family import FamilyService
from backend.app.core.security.jwt import create_access_token


@pytest.mark.asyncio 
class TestE2EFamilyWorkflows:
    """End-to-end tests for multi-parent family workflows."""
    
    async def create_test_user(self, db_session: AsyncSession, username: str, email: str, is_parent: bool = True):
        """Helper to create test users."""
        user_repo = UserRepository()
        return await user_repo.create(
            db_session,
            obj_in={
                "username": username,
                "password": "testpass123",
                "email": email,
                "is_parent": is_parent
            }
        )

    async def get_auth_headers(self, user_id: int):
        """Helper to get authorization headers."""
        token = create_access_token(subject=str(user_id))
        return {"Authorization": f"Bearer {token}"}

    async def create_test_chore(self, db_session: AsyncSession, creator_id: int, assignee_id: int, title: str = "Test Chore"):
        """Helper to create test chores with single assignment."""
        from backend.app.models.chore import Chore
        from backend.app.models.chore_assignment import ChoreAssignment

        # Create chore with multi-assignment architecture
        chore = Chore(
            title=title,
            description="Test chore description",
            reward=5.0,
            is_range_reward=False,
            cooldown_days=0,
            is_recurring=False,
            is_disabled=False,
            assignment_mode="single",
            creator_id=creator_id
        )
        db_session.add(chore)
        await db_session.flush()  # Get chore.id

        # Create assignment
        assignment = ChoreAssignment(
            chore_id=chore.id,
            assignee_id=assignee_id,
            is_completed=False,
            is_approved=False
        )
        db_session.add(assignment)
        await db_session.commit()
        await db_session.refresh(chore)
        return chore


@pytest.mark.asyncio
class TestJourney1_SingleToMultiParent(TestE2EFamilyWorkflows):
    """Journey 1: Existing parent converts to multi-parent family."""
    
    async def test_complete_single_to_multi_parent_workflow(self, client: AsyncClient, db_session: AsyncSession):
        """
        Test the complete workflow from single parent to multi-parent family.
        
        Workflow Steps:
        1. Parent1 exists with children and chores
        2. Parent1 creates family and generates invite code
        3. Parent2 registers and joins family using invite code
        4. Both parents can see same children and chores
        5. Both parents can create and manage chores for same children
        6. Chore approvals work from both parents
        """
        
        # Step 1: Create initial parent with child
        parent1 = await self.create_test_user(db_session, "parent1", "parent1@test.com", is_parent=True)
        child1 = await self.create_test_user(db_session, "child1", "child1@test.com", is_parent=False)
        
        # Create initial chore from parent1 to child1
        chore1 = await self.create_test_chore(db_session, parent1.id, child1.id, "Initial Chore")
        
        parent1_headers = await self.get_auth_headers(parent1.id)
        
        # Step 2: Parent1 creates family
        family_response = await client.post(
            "/api/v1/families/create",
            json={"name": "Test Family"},
            headers=parent1_headers
        )
        assert family_response.status_code == 201
        family_data = family_response.json()
        invite_code = family_data["invite_code"]
        family_id = family_data["id"]
        
        # Assign child to family (simulates the proper family inheritance that should happen automatically)
        from backend.app.repositories.user import UserRepository
        user_repo = UserRepository()
        await user_repo.update(db_session, id=child1.id, obj_in={"family_id": family_id})
        
        # Commit the session to ensure the child assignment is persisted
        await db_session.commit()
        
        # Verify parent1 is now in the family
        context_response = await client.get("/api/v1/families/context", headers=parent1_headers)
        assert context_response.status_code == 200
        context_data = context_response.json()
        assert context_data["has_family"] is True
        assert context_data["family"]["id"] == family_id
        
        # Step 3: Create and register Parent2
        parent2 = await self.create_test_user(db_session, "parent2", "parent2@test.com", is_parent=True)
        parent2_headers = await self.get_auth_headers(parent2.id)
        
        # Parent2 joins family using invite code
        join_response = await client.post(
            "/api/v1/families/join",
            json={"invite_code": invite_code},
            headers=parent2_headers
        )
        assert join_response.status_code == 200
        join_data = join_response.json()
        assert join_data["success"] is True
        assert join_data["family_id"] == family_id
        
        # Step 4: Verify both parents can see family members
        members_response1 = await client.get("/api/v1/families/members", headers=parent1_headers)
        members_response2 = await client.get("/api/v1/families/members", headers=parent2_headers)
        
        assert members_response1.status_code == 200
        assert members_response2.status_code == 200
        
        members1_data = members_response1.json()
        members2_data = members_response2.json()
        
        # Both should see the same family structure
        assert members1_data["total_members"] == members2_data["total_members"]
        assert len(members1_data["parents"]) == 2  # parent1 and parent2
        assert len(members2_data["parents"]) == 2
        
        # Verify child is in family for both parents
        children_response1 = await client.get("/api/v1/users/my-family-children", headers=parent1_headers)
        children_response2 = await client.get("/api/v1/users/my-family-children", headers=parent2_headers)
        
        assert children_response1.status_code == 200
        assert children_response2.status_code == 200
        
        children1_data = children_response1.json()
        children2_data = children_response2.json()
        
        
        # Both parents should see the same child
        assert len(children1_data) == len(children2_data) == 1
        assert children1_data[0]["id"] == children2_data[0]["id"] == child1.id
        
        # Step 5: Both parents can create chores for the same child
        chore2_response = await client.post(
            "/api/v1/chores",
            json={
                "title": "Parent2 Chore", 
                "description": "Chore created by parent2",
                "reward": 10.0,
                "assignee_id": child1.id,
                "is_recurring": False
            },
            headers=parent2_headers
        )
        assert chore2_response.status_code == 201
        chore2_data = chore2_response.json()
        
        # Step 6: Parent1 can see and approve chores created by Parent2
        pending_approvals1 = await client.get("/api/v1/chores/pending-approval", headers=parent1_headers)
        assert pending_approvals1.status_code == 200
        
        # Mark chore2 as completed (child1 completes the chore)
        child1_headers = await self.get_auth_headers(child1.id)
        complete_response = await client.post(
            f"/api/v1/chores/{chore2_data['id']}/complete",
            headers=child1_headers  # Child completes their own chore
        )
        assert complete_response.status_code == 200
        
        # Parent1 can approve Parent2's chore
        approve_response = await client.post(
            f"/api/v1/chores/{chore2_data['id']}/approve",
            json={"final_reward": 10.0},
            headers=parent1_headers
        )
        assert approve_response.status_code == 200
        
        # Verify family stats show collaboration
        stats_response = await client.get("/api/v1/families/stats", headers=parent1_headers)
        assert stats_response.status_code == 200
        stats_data = stats_response.json()
        
        assert stats_data["total_parents"] == 2
        assert stats_data["total_children"] == 1
        assert stats_data["total_chores"] >= 2  # At least the two chores we created
        

    async def test_family_invite_code_expiration_and_regeneration(self, client: AsyncClient, db_session: AsyncSession):
        """Test invite code lifecycle management."""
        parent1 = await self.create_test_user(db_session, "parent1", "parent1@test.com")
        parent1_headers = await self.get_auth_headers(parent1.id)
        
        # Create family
        family_response = await client.post(
            "/api/v1/families/create",
            json={"name": "Test Family"},
            headers=parent1_headers
        )
        assert family_response.status_code == 201
        
        # Generate new invite code with expiration
        new_code_response = await client.post(
            "/api/v1/families/invite-code/generate",
            json={"expires_in_days": 7},
            headers=parent1_headers
        )
        assert new_code_response.status_code == 200
        new_code_data = new_code_response.json()
        
        assert len(new_code_data["invite_code"]) == 8
        assert new_code_data["expires_at"] is not None
        assert new_code_data["family_name"] == "Test Family"


@pytest.mark.asyncio  
class TestJourney2_NewFamilyCreation(TestE2EFamilyWorkflows):
    """Journey 2: New family creation from scratch."""
    
    async def test_complete_new_family_creation_workflow(self, client: AsyncClient, db_session: AsyncSession):
        """
        Test complete new family creation workflow.
        
        Workflow Steps:
        1. First parent registers (no invite code)
        2. System creates new family automatically  
        3. Parent can create children and manage chores
        4. Family invite functionality is available
        5. Second parent can join later
        """
        
        # Step 1: Create first parent user
        parent1 = await self.create_test_user(db_session, "newparent", "new@test.com")
        parent1_headers = await self.get_auth_headers(parent1.id)
        
        # Step 2: Parent creates new family
        family_response = await client.post(
            "/api/v1/families/create", 
            json={"name": "Brand New Family"},
            headers=parent1_headers
        )
        assert family_response.status_code == 201
        family_data = family_response.json()
        
        assert family_data["name"] == "Brand New Family"
        assert len(family_data["invite_code"]) == 8
        family_id = family_data["id"]
        
        # Step 3: Parent can create children
        child_response = await client.post(
            "/api/v1/users/",
            json={
                "username": "newchild",
                "password": "childpass123",
                "email": "child@test.com",
                "is_parent": False,
                "parent_id": parent1.id
            },
            headers=parent1_headers
        )
        assert child_response.status_code == 201
        child_data = child_response.json()
        
        # Step 4: Parent can create chores for child
        chore_response = await client.post(
            "/api/v1/chores",
            json={
                "title": "First Family Chore",
                "description": "Initial chore in new family",
                "reward": 15.0,
                "assignee_id": child_data["id"],
                "is_recurring": False
            },
            headers=parent1_headers
        )
        assert chore_response.status_code == 201
        
        # Step 5: Verify family invite functionality works
        invite_response = await client.get("/api/v1/families/context", headers=parent1_headers)
        assert invite_response.status_code == 200
        invite_data = invite_response.json()
        
        assert invite_data["can_invite"] is True
        assert invite_data["can_manage"] is True
        assert invite_data["family"]["id"] == family_id
        
        # Step 6: Second parent can join later
        parent2 = await self.create_test_user(db_session, "secondparent", "second@test.com")
        parent2_headers = await self.get_auth_headers(parent2.id)
        
        join_response = await client.post(
            "/api/v1/families/join",
            json={"invite_code": family_data["invite_code"]},
            headers=parent2_headers
        )
        assert join_response.status_code == 200
        
        # Verify family now has two parents
        members_response = await client.get("/api/v1/families/members", headers=parent1_headers)
        assert members_response.status_code == 200
        members_data = members_response.json()
        
        assert members_data["total_members"] == 3  # 2 parents + 1 child
        assert len(members_data["parents"]) == 2
        assert len(members_data["children"]) == 1


@pytest.mark.asyncio
class TestJourney3_CrossFamilySecurity(TestE2EFamilyWorkflows):
    """Journey 3: Cross-family security isolation."""
    
    async def test_cross_family_data_isolation(self, client: AsyncClient, db_session: AsyncSession):
        """
        Test that families cannot access each other's data.
        
        Security Tests:
        1. Create two separate families
        2. Verify Parent A cannot access Parent B's family data
        3. Test API endpoint family_id filtering
        4. Validate children only see own family data
        """
        
        # Step 1: Create Family A
        parentA = await self.create_test_user(db_session, "parentA", "parentA@test.com")
        childA = await self.create_test_user(db_session, "childA", "childA@test.com", is_parent=False)
        
        parentA_headers = await self.get_auth_headers(parentA.id)
        
        familyA_response = await client.post(
            "/api/v1/families/create",
            json={"name": "Family A"},
            headers=parentA_headers
        )
        assert familyA_response.status_code == 201
        familyA_data = familyA_response.json()
        
        # Step 2: Create Family B  
        parentB = await self.create_test_user(db_session, "parentB", "parentB@test.com")
        childB = await self.create_test_user(db_session, "childB", "childB@test.com", is_parent=False) 
        
        parentB_headers = await self.get_auth_headers(parentB.id)
        
        familyB_response = await client.post(
            "/api/v1/families/create", 
            json={"name": "Family B"},
            headers=parentB_headers
        )
        assert familyB_response.status_code == 201
        familyB_data = familyB_response.json()
        
        # Assign children to their respective families (simulate family inheritance)
        from backend.app.repositories.user import UserRepository
        user_repo = UserRepository()
        await user_repo.update(db_session, id=childA.id, obj_in={"family_id": familyA_data["id"]})
        await user_repo.update(db_session, id=childB.id, obj_in={"family_id": familyB_data["id"]})
        
        # Step 3: Create chores in each family
        choreA = await self.create_test_chore(db_session, parentA.id, childA.id, "Family A Chore")
        choreB = await self.create_test_chore(db_session, parentB.id, childB.id, "Family B Chore")
        
        # Step 4: Verify Parent A cannot see Family B's data
        
        # Parent A should not see Parent B's family members
        membersA_response = await client.get("/api/v1/families/members", headers=parentA_headers)
        assert membersA_response.status_code == 200
        membersA_data = membersA_response.json()
        
        # Should only see own family members
        assert membersA_data["family_id"] == familyA_data["id"] 
        assert membersA_data["total_members"] == 2  # parentA + childA
        
        # Parent A should not see Parent B's children
        childrenA_response = await client.get("/api/v1/users/my-family-children", headers=parentA_headers)
        assert childrenA_response.status_code == 200
        childrenA_data = childrenA_response.json()
        
        assert len(childrenA_data) == 1
        assert childrenA_data[0]["id"] == childA.id
        # Should not contain childB
        child_ids = [child["id"] for child in childrenA_data]
        assert childB.id not in child_ids
        
        # Step 5: Verify API endpoints filter by family_id
        
        # Parent A's chores should not include Parent B's chores  
        choresA_response = await client.get("/api/v1/chores", headers=parentA_headers)
        assert choresA_response.status_code == 200
        choresA_data = choresA_response.json()
        
        chore_ids_A = [chore["id"] for chore in choresA_data]
        assert choreA.id in chore_ids_A
        assert choreB.id not in chore_ids_A  # Security: Should not see Family B's chores
        
        # Step 6: Verify children only see own family data
        childA_headers = await self.get_auth_headers(childA.id)
        childB_headers = await self.get_auth_headers(childB.id) 
        
        # Child A should only see chores from Family A
        childA_chores_response = await client.get("/api/v1/chores", headers=childA_headers)
        assert childA_chores_response.status_code == 200
        childA_chores_data = childA_chores_response.json()
        
        childA_chore_ids = [chore["id"] for chore in childA_chores_data]
        assert choreA.id in childA_chore_ids
        assert choreB.id not in childA_chore_ids  # Security: Child A cannot see Family B chores
        
        # Step 7: Test invalid family access attempts
        
        # Parent A should not be able to access Family B's stats directly
        # (This would require API endpoint modifications to test direct family_id manipulation)
        
        # Verify family stats are properly isolated
        statsA_response = await client.get("/api/v1/families/stats", headers=parentA_headers) 
        assert statsA_response.status_code == 200
        statsA_data = statsA_response.json()
        
        assert statsA_data["family_id"] == familyA_data["id"]
        assert statsA_data["total_members"] == 2  # Only Family A members
        
        statsB_response = await client.get("/api/v1/families/stats", headers=parentB_headers)
        assert statsB_response.status_code == 200 
        statsB_data = statsB_response.json()
        
        assert statsB_data["family_id"] == familyB_data["id"]
        assert statsB_data["total_members"] == 2  # Only Family B members
        
        # Family stats should be completely separate
        assert statsA_data["family_id"] != statsB_data["family_id"]


    async def test_invite_code_security(self, client: AsyncClient, db_session: AsyncSession):
        """Test invite code security and access control."""
        
        # Create family
        parent = await self.create_test_user(db_session, "parent", "parent@test.com")
        parent_headers = await self.get_auth_headers(parent.id)
        
        family_response = await client.post(
            "/api/v1/families/create",
            json={"name": "Secure Family"},
            headers=parent_headers
        )
        assert family_response.status_code == 201
        family_data = family_response.json()
        invite_code = family_data["invite_code"]
        
        # Create unauthorized user (not a parent)
        child = await self.create_test_user(db_session, "child", "child@test.com", is_parent=False)
        child_headers = await self.get_auth_headers(child.id)
        
        # Children should not be able to join families using invite codes
        join_response = await client.post(
            "/api/v1/families/join",
            json={"invite_code": invite_code},
            headers=child_headers
        )
        assert join_response.status_code == 403  # Forbidden - only parents can join families
        
        # Test invalid invite codes
        parent2 = await self.create_test_user(db_session, "parent2", "parent2@test.com")
        parent2_headers = await self.get_auth_headers(parent2.id)
        
        invalid_join_response = await client.post(
            "/api/v1/families/join",
            json={"invite_code": "INVALID1"},
            headers=parent2_headers
        )
        assert invalid_join_response.status_code == 404  # Not found - invalid code
        
        # Test malformed invite codes
        malformed_join_response = await client.post(
            "/api/v1/families/join", 
            json={"invite_code": "bad"},  # Too short
            headers=parent2_headers
        )
        assert malformed_join_response.status_code == 422  # Validation error