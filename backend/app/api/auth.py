import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from typing import Any

from app.core.database import get_db
from app.core.config import settings
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from app.models.user import User
from app.models.profile import Profile
from app.schemas.token import Token, RefreshTokenRequest, GoogleLoginRequest
from app.schemas.user import UserCreate, UserWithProfile

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserWithProfile)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        if "GOOGLE" in user.auth_provider:
            raise HTTPException(status_code=409, detail="This email is already registered with Google. Please sign in with Google.")
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        password_hash=get_password_hash(user_in.password),
        auth_provider="EMAIL",
        role="STUDENT",
        onboarding_completed=False
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create default profile
    profile = Profile(user_id=new_user.id)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    
    return new_user

@router.post("/login", response_model=Token)
def login_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not user.password_hash:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    return {
        "access_token": create_access_token(user.id, user.role),
        "refresh_token": create_refresh_token(user.id),
        "token_type": "bearer",
    }

from app.services.auth_service import AuthService
from app.services.dependencies import get_auth_service

@router.post("/google", response_model=Token)
def google_auth(request: GoogleLoginRequest, auth_service: AuthService = Depends(get_auth_service)):
    return auth_service.google_login(request.credential)

@router.post("/google/link", response_model=Token)
def google_link(request: GoogleLoginRequest, auth_service: AuthService = Depends(get_auth_service)):
    return auth_service.link_google_account(request.credential)

@router.post("/refresh", response_model=Token)
def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(request.refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        if user_id is None or token_type != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid user")

    return {
        "access_token": create_access_token(user.id, user.role),
        "refresh_token": create_refresh_token(user.id),
        "token_type": "bearer",
    }
