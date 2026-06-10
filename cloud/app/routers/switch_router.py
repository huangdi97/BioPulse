"""模式切换路由：在 visit / research 模式间切换并签发新 token。"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from shared.auth import create_access_token
from shared.auth_scope import require_scope
from shared.base import success

router = APIRouter(prefix="/auth", tags=["模式切换"])


class ModeSwitchRequest(BaseModel):
    """模式切换请求体。"""

    new_scope: str = Field(..., pattern="^(pharma|research|surgery|opportunity|salesCoach|visit)$")


class ModeSwitchResponse(BaseModel):
    """模式切换响应体。"""

    access_token: str
    token_type: str = "bearer"
    scope: str
    role: str


@router.post("/switch-mode", summary="切换用户模式", description="在visit和research模式之间切换并签发新Token", tags=["模式切换"])
def switch_mode(
    body: ModeSwitchRequest,
    current_user: dict = Depends(require_scope("visit")),
):
    user_id = current_user.get("id") or current_user.get("sub")
    role = current_user.get("role", "rep")
    new_token = create_access_token(user_id, role, body.new_scope)
    return success(data={
        "access_token": new_token,
        "token_type": "bearer",
        "scope": body.new_scope,
        "role": role,
    })
