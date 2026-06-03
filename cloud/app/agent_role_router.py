from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from starlette import status

from cloud.app.database import get_db
from cloud.app.repositories import AgentRolesRepository
from shared.auth_scope import require_scope
from shared.base import success

router = APIRouter(prefix="/agent/roles", tags=["Agent系统"])


class RoleCreate(BaseModel):
    name: str
    role_type: str = "sales_rep"
    description: str = ""
    system_prompt: str
    input_schema: str = "{}"
    output_schema: str = "{}"
    temperature: float = 0.7
    max_tokens: int = 2048
    allowed_tools: str = "[]"


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    role_type: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    input_schema: Optional[str] = None
    output_schema: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    allowed_tools: Optional[str] = None
    is_active: Optional[int] = None


def rd(row) -> dict:
    """将角色行数据格式化为字典。Args: row (sqlite3.Row) 数据库行。Returns: dict 格式化后的角色字典"""
    return {
        "id": row["id"],
        "name": row["name"],
        "role_type": row["role_type"],
        "description": row["description"],
        "system_prompt": row["system_prompt"],
        "input_schema": row["input_schema"],
        "output_schema": row["output_schema"],
        "temperature": row["temperature"],
        "max_tokens": row["max_tokens"],
        "allowed_tools": row["allowed_tools"],
        "is_active": row["is_active"],
        "created_by": row["created_by"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _404(repo, rid):
    row = repo.get_by_id(rid)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Role not found")
    return row


@router.post("", status_code=status.HTTP_201_CREATED)
def create_role(body: RoleCreate, current_user=Depends(require_scope("visit")), db=Depends(get_db)):
    """创建Agent角色并返回角色数据。Args: body (RoleCreate) 角色创建体; current_user 用户; db SQLite连接。Returns: dict 成功响应"""
    uid = int(current_user["sub"])
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    repo = AgentRolesRepository(db)
    rid = repo.create(
        {
            "name": body.name,
            "role_type": body.role_type,
            "description": body.description,
            "system_prompt": body.system_prompt,
            "input_schema": body.input_schema,
            "output_schema": body.output_schema,
            "temperature": body.temperature,
            "max_tokens": body.max_tokens,
            "allowed_tools": body.allowed_tools,
            "created_by": uid,
            "created_at": now,
            "updated_at": now,
        }
    )
    row = repo.get_by_id(rid)
    return success(data=rd(row))


@router.get("")
def list_roles(
    role_type: Optional[str] = Query(None),
    is_active: Optional[int] = Query(None),
    current_user=Depends(require_scope("visit")),
    db=Depends(get_db),
):
    """按类型和状态筛选Agent角色列表。
    Args: role_type (Optional[str]) 角色类型; is_active (Optional[int]) 启用状态; current_user 用户; db SQLite连接。
    Returns: dict 成功响应"""
    repo = AgentRolesRepository(db)
    conds, pars = [], []
    if is_active is not None:
        conds.append("is_active=?")
        pars.append(is_active)
    else:
        conds.append("is_active=1")
    if role_type:
        conds.append("role_type=?")
        pars.append(role_type)
    rows = repo.list_all(conditions=conds, params=pars, order_by="created_at DESC")
    return success(data=[rd(r) for r in rows])


@router.get("/{role_id}")
def get_role(role_id: int, current_user=Depends(require_scope("visit")), db=Depends(get_db)):
    """获取指定角色的详细信息。Args: role_id (int) 角色ID; current_user 用户; db SQLite连接。Returns: dict 成功响应"""
    repo = AgentRolesRepository(db)
    row = _404(repo, role_id)
    return success(data=rd(row))


@router.patch("/{role_id}")
def update_role(
    role_id: int,
    body: RoleUpdate,
    current_user=Depends(require_scope("visit")),
    db=Depends(get_db),
):
    """部分更新Agent角色字段。Args: role_id (int) 角色ID; body (RoleUpdate) 角色更新体; current_user 用户; db SQLite连接。Returns: dict 成功响应"""
    repo = AgentRolesRepository(db)
    _404(repo, role_id)
    updates = {}
    for f in [
        "name",
        "role_type",
        "description",
        "system_prompt",
        "input_schema",
        "output_schema",
    ]:
        v = getattr(body, f)
        if v is not None:
            updates[f] = v
    if body.temperature is not None:
        updates["temperature"] = body.temperature
    if body.max_tokens is not None:
        updates["max_tokens"] = body.max_tokens
    if body.allowed_tools is not None:
        updates["allowed_tools"] = body.allowed_tools
    if body.is_active is not None:
        updates["is_active"] = body.is_active
    if updates:
        updates["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        repo.update(role_id, updates)
    row = repo.get_by_id(role_id)
    return success(data=rd(row))


@router.delete("/{role_id}")
def delete_role(role_id: int, current_user=Depends(require_scope("visit")), db=Depends(get_db)):
    """软删除指定Agent角色。Args: role_id (int) 角色ID; current_user 用户; db SQLite连接。Returns: dict 成功响应"""
    repo = AgentRolesRepository(db)
    _404(repo, role_id)
    repo.soft_delete(role_id)
    return success()
