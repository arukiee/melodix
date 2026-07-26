"""JWT utilities – create and decode tokens."""

from datetime import datetime, timedelta
from typing import Any, Dict

from jose import JWTError, jwt

from ..config.settings import settings
from .constants import TOKEN_TYPE_ACCESS, TOKEN_TYPE_REFRESH

def _encode(data: Dict[str, Any], expires: timedelta) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + expires
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT.secret_key, algorithm=settings.JWT.algorithm)

def create_access_token(subject: str, extra: Dict[str, Any] | None = None) -> str:
    payload = {"sub": subject, "type": TOKEN_TYPE_ACCESS}
    if extra:
        payload.update(extra)
    return _encode(payload, timedelta(minutes=settings.JWT.access_token_expires_minutes))

def create_refresh_token(subject: str) -> str:
    payload = {"sub": subject, "type": TOKEN_TYPE_REFRESH}
    return _encode(payload, timedelta(days=settings.JWT.refresh_token_expires_days))

def decode_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, settings.JWT.secret_key, algorithms=[settings.JWT.algorithm])
    except JWTError as exc:
        raise ValueError("Invalid JWT") from exc
