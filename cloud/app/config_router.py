from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from starlette import status

from shared.auth_scope import require_scope
from shared.base import success
from cloud.app.services.config_service import ConfigService

router = APIRouter(prefix="/admin/configs", tags=["配置"])


class ConfigItem(BaseModel):
    key: str
    value: str
    description: str = ""


@router.get("/")
def list_configs(
    current_user: dict = Depends(require_scope("visit")),
    service: ConfigService = Depends(),
) -> Any:
    rows = service.list_configs()
    return success(data=rows)


@router.put("/")
def batch_upsert_configs(
    body: List[ConfigItem],
    current_user: dict = Depends(require_scope("visit")),
    service: ConfigService = Depends(),
) -> Any:
    user_id = int(current_user["sub"])
    rows = service.batch_upsert_configs(body, user_id)
    return success(data=rows)


@router.get("/{key}")
def get_config(
    key: str,
    current_user: dict = Depends(require_scope("visit")),
    service: ConfigService = Depends(),
) -> Any:
    return success(data=service.get_config(key))
