from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.profile import Profile as ProfileModel
from app.schemas.user import (
    UserWithProfile, UserUpdate,
    Profile as ProfileSchema, ProfileUpdate
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserWithProfile)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserWithProfile)
def update_users_me(
    updates: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if updates.full_name is not None:
        current_user.full_name = updates.full_name
    if updates.avatar_url is not None:
        current_user.avatar_url = updates.avatar_url
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/profile", response_model=ProfileSchema)
def read_users_profile(current_user: User = Depends(get_current_user)):
    if not current_user.profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return current_user.profile


@router.patch("/profile", response_model=ProfileSchema)
def update_users_profile(
    updates: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = current_user.profile
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return profile


@router.post("/complete-onboarding", response_model=UserWithProfile)
def complete_onboarding(
    updates: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Update profile fields from onboarding
    profile = current_user.profile
    if not profile:
        profile = ProfileModel(user_id=current_user.id)
        db.add(profile)

    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    # Mark onboarding as completed
    current_user.onboarding_completed = True
    db.commit()
    db.refresh(current_user)
    return current_user
