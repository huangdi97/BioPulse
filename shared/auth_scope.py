"""Auth scope module."""

from typing import Union

from fastapi import Depends, HTTPException
from starlette import status

from shared.auth import get_current_user


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
