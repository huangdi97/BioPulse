import os
import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from starlette import status

from cloud.app.database import DB_PATH
from cloud.app.services.config_service import ConfigService
from shared.auth import verify_token
from shared.base import success

router = APIRouter(prefix="/admin/settings", tags=["配置"])


class SettingsBody(BaseModel):
    settings: dict


def get_db_direct():
    """获取数据库直连。Returns: sqlite3 连接对象."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_current_user(request: Request) -> dict:
    """从请求头解析当前用户。
    Args: request 请求对象. Returns: 用户字典.
    """
    auth = request.headers.get("Authorization", "")
    scheme, _, token = auth.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth header")
    payload = verify_token(token)
    return payload


@router.get("")
def get_all(user: dict = Depends(get_current_user)):
    """获取所有配置项。Returns: 配置字典."""
    db = get_db_direct()
    service = ConfigService(db)
    result = service.get_all()
    db.close()
    return success(data=result)


@router.put("")
def update(body: SettingsBody, user: dict = Depends(get_current_user)):
    """更新配置项。
    Args: body 配置字典. Returns: 更新结果.
    """
    db = get_db_direct()
    service = ConfigService(db)
    result = service.update(body.settings)
    db.close()
    return success(data=result)
