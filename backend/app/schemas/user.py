from pydantic import BaseModel, EmailStr
from typing import Optional, List

class UserBase(BaseModel):
    email: EmailStr
    username: str
    is_parent: bool = False

class UserCreate(UserBase):
    password: str
    parent_id: Optional[int] = None

class UserResponse(UserBase):
    id: int
    is_active: bool = True

    class Config:
        from_attributes = True