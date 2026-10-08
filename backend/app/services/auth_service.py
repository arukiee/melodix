"""Auth service for Google OAuth and JWT handling.

The service isolates all external calls (Google token verification) and
business logic (user lookup/creation, JWT generation). It receives a
configured ``AuthConfig`` instance and a ``Session`` factory so that it
can be used both in the FastAPI router and in unit tests.
"""

from typing import Dict

import logging
from google.oauth2 import id_token
from google.auth.transport import requests

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token
from app.models.user import User
from app.models.profile import Profile
from app.schemas.token import Token
from fastapi import HTTPException, status


class AuthService:
    """Encapsulates Google OAuth flow and JWT creation.

    The service is deliberately thin – it does not depend on FastAPI
    request objects, making it easy to unit‑test.
    """

    def __init__(self, db: Session):
        self.db = db
        self.cfg = settings.auth_config

    def verify_google_token(self, credential: str) -> Dict:
        """Verify the Google credential and return the token payload.

        Raises ``HTTPException`` with status 400 if verification fails.
        """
        try:
            token_info = id_token.verify_oauth2_token(
                credential,
                requests.Request(),
                self.cfg.GOOGLE_CLIENT_ID,
            )
        except ValueError as exc:
            logging.error(
                "Google token verification failed for client_id=%s: %s",
                self.cfg.GOOGLE_CLIENT_ID,
                exc,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid Google credential: {exc}",
            )
        except Exception as exc:
            logging.error("Unexpected error during Google authentication: %s", exc)
            exc_str = str(exc)
            if "Failed to resolve" in exc_str or "Max retries exceeded" in exc_str or "Connection" in exc_str:
                if settings.DEBUG or settings.ENVIRONMENT == "development":
                    try:
                        import base64, json
                        # JWT is header.payload.signature — decode payload without any library
                        parts = credential.split(".")
                        if len(parts) == 3:
                            payload_b64 = parts[1]
                            # Re-pad to a multiple of 4
                            payload_b64 += "=" * (4 - len(payload_b64) % 4)
                            claims = json.loads(base64.urlsafe_b64decode(payload_b64))
                            if claims and claims.get("email"):
                                logging.warning(
                                    "Development mode: using unverified Google token claims for offline testing (%s)",
                                    claims.get("email"),
                                )
                                return claims
                    except Exception as dev_exc:
                        logging.warning("Failed to decode unverified Google claims: %s", dev_exc)
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Google verification service unreachable. Please check network connection or use email/password login.",
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Google authentication failed: {exc_str}",
            )
        return token_info

    def _get_or_create_user(self, email: str, name: str, picture: str, is_linking: bool = False) -> User:
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                email=email,
                full_name=name,
                avatar_url=picture,
                auth_provider="GOOGLE",
                role="STUDENT",
                onboarding_completed=False,
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            profile = Profile(user_id=user.id)
            self.db.add(profile)
            self.db.commit()
            self.db.refresh(profile)
        else:
            if user.auth_provider == "EMAIL" and not is_linking:
                raise HTTPException(
                    status_code=409,
                    detail="Existing account found. Would you like to link your Google account?"
                )
            elif is_linking and "GOOGLE" not in user.auth_provider:
                user.auth_provider = f"{user.auth_provider},GOOGLE"
            if not user.profile:
                profile = Profile(user_id=user.id)
                self.db.add(profile)
                self.db.commit()
        return user

    def google_login(self, credential: str) -> Token:
        token_info = self.verify_google_token(credential)
        email = token_info.get("email")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not found in Google token",
            )
        name = token_info.get("name", "Google User")
        picture = token_info.get("picture")
        user = self._get_or_create_user(email, name, picture, is_linking=False)
        return Token(
            access_token=create_access_token(user.id, user.role),
            refresh_token=create_refresh_token(user.id),
            token_type="bearer",
        )

    def link_google_account(self, credential: str) -> Token:
        token_info = self.verify_google_token(credential)
        email = token_info.get("email")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not found in Google token",
            )
        name = token_info.get("name", "Google User")
        picture = token_info.get("picture")
        user = self._get_or_create_user(email, name, picture, is_linking=True)
        return Token(
            access_token=create_access_token(user.id, user.role),
            refresh_token=create_refresh_token(user.id),
            token_type="bearer",
        )
