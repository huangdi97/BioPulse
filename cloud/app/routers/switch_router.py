from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from shared.auth import create_access_token
from shared.auth_scope import require_scope

router = APIRouter(prefix="/auth", tags=["模式切换"])


class ModeSwitchRequest(BaseModel):
    new_scope: str = Field(..., pattern="^(visit|research)$")


class ModeSwitchResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    scope: str


@router.post("/switch-mode", summary="切换用户模式")
def switch_mode(
    body: ModeSwitchRequest,
    current_user: dict = Depends(require_scope("visit")),
):
    user_id = current_user.get("id") or current_user.get("sub")
    role = current_user.get("role", "rep")
    new_token = create_access_token(user_id, role, body.new_scope)
    return {
        "access_token": new_token,
        "token_type": "bearer",
        "scope": body.new_scope,
    }
