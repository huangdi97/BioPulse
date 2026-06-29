"""租户管理路由。"""

import json
import os
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from starlette import status

from shared.auth_scope import require_scope
from shared.base import success

router = APIRouter(prefix="/api/v1/tenants", tags=["租户"])

TENANT_CONFIGS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "tenant_configs"))


class TenantConfig(BaseModel):
    tenant_id: str
    name: str
    enabled_agents: List[str] = []
    model_selection: dict = {}
    feature_modules: dict = {}
    rate_limits: dict = {}


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    enabled_agents: Optional[List[str]] = None
    model_selection: Optional[dict] = None
    feature_modules: Optional[dict] = None
    rate_limits: Optional[dict] = None


def _config_path(tenant_id: str) -> str:
    return os.path.join(TENANT_CONFIGS_DIR, f"{tenant_id}.json")


def _read_config(tenant_id: str) -> dict:
    path = _config_path(tenant_id)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Tenant {tenant_id} not found")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_config(tenant_id: str, data: dict) -> None:
    path = _config_path(tenant_id)
    os.makedirs(TENANT_CONFIGS_DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_tenant(
    body: TenantConfig,
    _: dict = Depends(require_scope("admin")),
) -> Any:
    path = _config_path(body.tenant_id)
    if os.path.exists(path):
        raise HTTPException(status_code=409, detail=f"Tenant {body.tenant_id} already exists")
    _write_config(body.tenant_id, body.model_dump())
    return success(data=body.model_dump())


@router.get("/")
def list_tenants(
    _: dict = Depends(require_scope("admin")),
) -> Any:
    if not os.path.exists(TENANT_CONFIGS_DIR):
        return success(data=[])
    configs = []
    for fname in sorted(os.listdir(TENANT_CONFIGS_DIR)):
        if fname.endswith(".json"):
            with open(os.path.join(TENANT_CONFIGS_DIR, fname), "r", encoding="utf-8") as f:
                configs.append(json.load(f))
    return success(data=configs)


@router.get("/{tenant_id}")
def get_tenant(
    tenant_id: str,
    _: dict = Depends(require_scope("admin")),
) -> Any:
    return success(data=_read_config(tenant_id))


@router.patch("/{tenant_id}")
def update_tenant(
    tenant_id: str,
    body: TenantUpdate,
    _: dict = Depends(require_scope("admin")),
) -> Any:
    config = _read_config(tenant_id)
    update_data = body.model_dump(exclude_unset=True)
    config.update(update_data)
    _write_config(tenant_id, config)
    return success(data=config)


@router.delete("/{tenant_id}", status_code=status.HTTP_200_OK)
def delete_tenant(
    tenant_id: str,
    _: dict = Depends(require_scope("admin")),
) -> Any:
    path = _config_path(tenant_id)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Tenant {tenant_id} not found")
    os.remove(path)
    return success()
