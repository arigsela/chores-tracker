from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List

class UserBase(BaseModel):
    username: str
    is_parent: bool = False
    email: Optional[EmailStr] = None

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
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    is_active: bool = True
    parent_id: Optional[int] = None