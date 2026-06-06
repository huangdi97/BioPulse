"""管理员设置路由。"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from starlette import status

from cloud.app.services.settings_service import SettingsService
from shared.auth import verify_token
from shared.base import success

router = APIRouter(prefix="/admin/settings", tags=["配置"])


class SettingsBody(BaseModel):
    settings: dict


def get_current_user(request: Request) -> dict:
    auth = request.headers.get("Authorization", "")
    scheme, _, token = auth.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth header")
    payload = verify_token(token)
    return payload


@router.get("")
def get_all(user: dict = Depends(get_current_user)):
    service = SettingsService()
    result = service.get_all()
    return success(data=result)


@router.put("")
def update(body: SettingsBody, user: dict = Depends(get_current_user)):
    service = SettingsService()
    for key, value in body.settings.items():
        service.set(key, value)
    result = service.get_all()
    return success(data=result)
