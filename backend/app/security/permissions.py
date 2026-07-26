"""RBAC helpers and permission checks."""

from typing import Iterable

def has_role(user: dict, required_roles: Iterable[str]) -> bool:
    return bool(set(user.get("roles", [])) & set(required_roles))

def require_roles(*roles: str):
    from fastapi import Depends, HTTPException, status
    from .dependencies import get_current_user

    def dependency(user: dict = Depends(get_current_user)):
        if not has_role(user, roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return user
    return Depends(dependency)
