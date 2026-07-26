"""Password hashing utilities."""

from passlib.context import CryptContext
from .constants import PASSWORD_SCHEMES

pwd_context = CryptContext(schemes=PASSWORD_SCHEMES, deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
