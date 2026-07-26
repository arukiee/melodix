from pydantic import BaseModel, EmailStr
from typing import Optional, List
import uuid

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    
class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None

class UserInDBBase(UserBase):
    id: uuid.UUID
    role: str
    auth_provider: str
    avatar_url: Optional[str] = None
    onboarding_completed: bool
    is_active: bool

    class Config:
        from_attributes = True

class User(UserInDBBase):
    pass

class ProfileBase(BaseModel):
    bio: Optional[str] = None
    skill_level: Optional[str] = None
    preferred_instrument: Optional[str] = None
    daily_practice_goal: Optional[int] = None
    preferred_genres: Optional[List[str]] = None
    learning_preferences: Optional[dict] = None

class ProfileUpdate(ProfileBase):
    pass

class Profile(ProfileBase):
    id: uuid.UUID
    user_id: uuid.UUID

    class Config:
        from_attributes = True

class UserWithProfile(User):
    profile: Optional[Profile] = None
