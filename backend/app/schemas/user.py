from pydantic import BaseModel, EmailStr
from typing import Optional, List

class UserBase(BaseModel):
    email: EmailStr
    username: str
    is_parent: bool = False

class UserCreate(UserBase):
    password: str
    parent_id: Optional[int] = None

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserResponse(UserBase):
    id: int
    is_active: bool = True
    parent_id: Optional[int] = None

    class Config:
        from_attributes = True