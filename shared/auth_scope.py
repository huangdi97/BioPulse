"""Auth scope module."""

from functools import wraps
from typing import Callable, Union

from fastapi import Depends, HTTPException
from starlette import status

from shared.auth import get_current_user

VALID_ROLES = frozenset({"admin", "manager", "rep", "readonly"})


def require_scope(required_scope: Union[str, list[str]]):
    """FastAPI dependency that checks the JWT token's scope field.

    Usage:
        @router.get("/api/research/data", dependencies=[Depends(require_scope("research"))])
        @router.get("/api/data", dependencies=[Depends(require_scope(["pharma", "research"]))])

    If the token scope does not match the required scope (and is not "admin"),
    a 403 Forbidden response is returned.
    """

    def _checker(token: dict = Depends(get_current_user)):
        token_scope = token.get("scope")
        if token_scope is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="scope mismatch",
            )
        if isinstance(required_scope, list):
            if token_scope not in required_scope and token_scope != "admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="scope mismatch",
                )
        else:
            if token_scope != required_scope and token_scope != "admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="scope mismatch",
                )
        return token

    return _checker


def require_role(role: str):
    """FastAPI dependency that checks the JWT token's role field.

    Supports four roles: admin, manager, rep, readonly.
    The admin role has universal access regardless of the required role.

    Usage:
        @router.get("/admin/dashboard", dependencies=[Depends(require_role("admin"))])
        @router.get("/team/data", dependencies=[Depends(require_role("manager"))])

    If the token role is insufficient, a 403 Forbidden response is returned.
    """
    if role not in VALID_ROLES:
        raise ValueError(f"Invalid role '{role}'. Must be one of {sorted(VALID_ROLES)}")

    def _checker(token: dict = Depends(get_current_user)):
        token_role = token.get("role")
        if token_role is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="role mismatch",
            )
        if token_role != role and token_role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"role '{token_role}' cannot access resource requiring role '{role}'",
            )
        return token

    return _checker


def region_scope(region: str):
    """Decorator that checks the current user's region permission.

    The user's allowed regions are read from the JWT token's ``regions`` field
    (a list of region codes).  If the token has no ``regions`` field, the check
    is skipped for backward compatibility.

    Usage::

        @router.get("/data")
        @region_scope("east-china")
        def get_data(current_user: dict = Depends(get_current_user)):
            ...

    If the user does not have access to the specified region, a 403 Forbidden
    response is returned.
    """

    def decorator(endpoint: Callable) -> Callable:
        @wraps(endpoint)
        async def wrapper(*args, current_user: dict = Depends(get_current_user), **kwargs):
            regions = current_user.get("regions")
            if regions is not None and region not in regions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"user lacks access to region '{region}'",
                )
            return await endpoint(*args, current_user=current_user, **kwargs)

        return wrapper

    return decorator
