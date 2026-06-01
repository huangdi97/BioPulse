from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from starlette import status

from cloud.app.services.user_service import UserService
from shared.auth_scope import require_scope
from shared.base import success

router = APIRouter(prefix="/users", tags=["users"])


class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    is_active: bool
    created_at: str


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    role: Optional[str] = None
    is_active: Optional[bool] = None


def _require_admin(current_user: dict) -> None:
    if current_user.get("role") != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Admin access required")


@router.get("/")
def list_users(
    current_user: dict = Depends(require_scope("visit")),
    service: UserService = Depends(),
) -> Any:
    _require_admin(current_user)
    users = service.list_users()
    return success(data=users)


@router.get("/{user_id:int}")
def get_user(
    user_id: int,
    current_user: dict = Depends(require_scope("visit")),
    service: UserService = Depends(),
) -> Any:
    _require_admin(current_user)
    row = service.get_user(user_id)
    return success(data=row)


@router.patch("/{user_id:int}")
def update_user(
    user_id: int,
    body: UserUpdate,
    current_user: dict = Depends(require_scope("visit")),
    service: UserService = Depends(),
) -> Any:
    _require_admin(current_user)

    updates = {}
    if body.role is not None:
        updates["role"] = body.role
    if body.is_active is not None:
        updates["is_active"] = int(body.is_active)

    service.update_user(user_id, updates)
    return success()


@router.delete("/{user_id:int}")
def delete_user(
    user_id: int,
    current_user: dict = Depends(require_scope("visit")),
    service: UserService = Depends(),
) -> Any:
    _require_admin(current_user)

    if str(current_user["sub"]) == str(user_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Cannot disable your own account")

    service.delete_user(user_id)
    return success()
