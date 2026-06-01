from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from cloud.app.services.api_token_service import ApiTokenService
from shared.auth import get_current_user
from shared.base import success

router = APIRouter(prefix="/tokens", tags=["tokens"])


class CreateTokenRequest(BaseModel):
    name: str


class TokenResponse(BaseModel):
    id: int
    name: str
    created_at: str
    is_active: bool


@router.post("/")
def create_token(
    body: CreateTokenRequest,
    current_user: dict = Depends(get_current_user),
    service: ApiTokenService = Depends(),
) -> Any:
    user_id = int(current_user["sub"])
    return success(data=service.create_token(body.name, user_id))


@router.get("/")
def list_tokens(
    current_user: dict = Depends(get_current_user),
    service: ApiTokenService = Depends(),
) -> Any:
    user_id = int(current_user["sub"])
    return success(data=service.list_tokens(user_id))


@router.delete("/{token_id:int}")
def revoke_token(
    token_id: int,
    current_user: dict = Depends(get_current_user),
    service: ApiTokenService = Depends(),
) -> Any:
    user_id = int(current_user["sub"])
    service.revoke_token(token_id, user_id)
    return success()
