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

from google.oauth2 import id_token
from google.auth.transport import requests

@router.post("/google", response_model=Token)
async def google_auth(request: GoogleLoginRequest, db: Session = Depends(get_db)):
    try:
        # Verify the token with Google
        token_info = id_token.verify_oauth2_token(
            request.credential,
            requests.Request(),
            settings.GOOGLE_CLIENT_ID
        )
        
        email = token_info.get("email")
        name = token_info.get("name", "Google User")
        picture = token_info.get("picture")

        if not email:
            raise HTTPException(status_code=400, detail="Email not found in Google token")

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid Google token")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        # User doesn't exist, create them
        user = User(
            email=email,
            full_name=name,
            avatar_url=picture,
            auth_provider="GOOGLE",
            role="STUDENT",
            onboarding_completed=False
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create Profile
        profile = Profile(user_id=user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    else:
        # User exists, link Google if it was email based before
        if user.auth_provider == "EMAIL":
            user.auth_provider = "GOOGLE"
            db.commit()

    return {
        "access_token": create_access_token(user.id, user.role),
        "refresh_token": create_refresh_token(user.id),
        "token_type": "bearer",
    }

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
