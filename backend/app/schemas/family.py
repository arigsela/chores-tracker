"""Pydantic schemas for family-related API operations."""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime


class FamilyBase(BaseModel):
    """Base family schema."""
    name: Optional[str] = Field(None, max_length=255, description="Family name")


class FamilyCreate(FamilyBase):
    """Schema for family creation requests."""
    pass


class FamilyResponse(FamilyBase):
    """Schema for family responses."""
    id: int
    invite_code: str = Field(..., description="8-character family invite code")
    invite_code_expires_at: Optional[datetime] = Field(None, description="Invite code expiration time")
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class InviteCodeGenerateRequest(BaseModel):
    """Request to generate new invite code."""
    expires_in_days: Optional[int] = Field(
        None, 
        ge=1, 
        le=365, 
        description="Number of days until code expires (optional)"
    )


class InviteCodeResponse(BaseModel):
    """Response with invite code details."""
    invite_code: str = Field(..., description="8-character invite code")
    expires_at: Optional[datetime] = Field(None, description="Expiration time if set")
    family_name: Optional[str] = Field(None, description="Name of the family")


class FamilyJoinRequest(BaseModel):
    """Request to join family by invite code."""
    invite_code: str = Field(
        ..., 
        min_length=8, 
        max_length=8, 
        description="8-character family invite code"
    )
    
    @field_validator('invite_code')
    @classmethod
    def validate_invite_code(cls, v):
        if not v.isupper():
            raise ValueError('Invite code must be uppercase')
        if not v.isalnum():
            raise ValueError('Invite code must contain only letters and numbers')
        return v


class FamilyJoinResponse(BaseModel):
    """Response after joining family."""
    success: bool
    family_id: int
    family_name: Optional[str]
    message: str


class FamilyMemberResponse(BaseModel):
    """Schema for family member information."""
    id: int
    username: str
    email: Optional[str] = None
    is_parent: bool
    is_active: bool
    parent_id: Optional[int] = None  # For legacy compatibility
    joined_at: datetime = Field(..., alias="created_at")
    
    model_config = {"from_attributes": True, "populate_by_name": True}


class FamilyMembersResponse(BaseModel):
    """Response containing all family members."""
    family_id: int
    family_name: Optional[str]
    total_members: int
    parents: List[FamilyMemberResponse]
    children: List[FamilyMemberResponse]


class FamilyStatsResponse(BaseModel):
    """Family statistics response."""
    family_id: int
    name: Optional[str]
    invite_code: str
    created_at: datetime
    total_members: int
    total_parents: int
    total_children: int
    total_chores: int
    completed_chores: int
    approved_chores: int
    total_rewards_earned: float


class FamilyContextResponse(BaseModel):
    """User's family context information."""
    has_family: bool
    family: Optional[FamilyResponse] = None
    role: str = Field(..., description="User role: 'parent', 'child', or 'no_family'")
    can_invite: bool = Field(..., description="Whether user can generate invite codes")
    can_manage: bool = Field(..., description="Whether user can manage family settings")


class RemoveUserFromFamilyRequest(BaseModel):
    """Request to remove a user from family."""
    user_id: int = Field(..., description="ID of user to remove from family")
    reason: Optional[str] = Field(None, max_length=500, description="Optional reason for removal")


class RemoveUserFromFamilyResponse(BaseModel):
    """Response after removing user from family."""
    success: bool
    message: str
    removed_user_id: int


class FamilyInviteCodeCleanupResponse(BaseModel):
    """Response from invite code cleanup operation."""
    cleaned_count: int = Field(..., description="Number of expired codes that were regenerated")
    message: str