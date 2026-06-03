import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from starlette import status

from cloud.app.database import get_db
from cloud.app.repositories import McpToolsRepository
from cloud.app.services.mcp_guard_service import McpGuardService
from shared.auth_scope import require_scope
from shared.base import success

router = APIRouter(prefix="/mcp", tags=["MCP"])


class ToolRegister(BaseModel):
    tool_name: str
    description: str = ""
    endpoint_url: str = ""
    input_schema: dict = {}
    output_schema: dict = {}


def _row(r):
    if not r:
        return None
    d = dict(r)
    for k in ("input_schema", "output_schema"):
        if k in d and isinstance(d[k], str):
            try:
                d[k] = json.loads(d[k])
            except (json.JSONDecodeError, TypeError):
                pass
    return d


@router.post("/tools/register", status_code=status.HTTP_201_CREATED)
def register_tool(body: ToolRegister, current_user=Depends(require_scope("visit")), db=Depends(get_db)):
    """注册一个新的 MCP 工具。

    Args:
        body: 工具信息（名称、描述、端点、输入/输出 schema）。

    Returns:
        注册后的工具记录。
    """
    uid = int(current_user["sub"])
    role = current_user.get("role", "rep")

    McpGuardService.check_tool_access(body.tool_name, role)
    if not McpGuardService.validate_tool_version(body.tool_name, "1.0.0"):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail=f"Tool '{body.tool_name}' version mismatch, expected {McpGuardService.TOOL_REGISTRY.get(body.tool_name, {}).get('version', 'unknown')}",
        )

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    repo = McpToolsRepository(db)
    repo.create(
        {
            "tool_name": body.tool_name,
            "description": body.description,
            "endpoint_url": body.endpoint_url,
            "input_schema": json.dumps(body.input_schema, ensure_ascii=False),
            "output_schema": json.dumps(body.output_schema, ensure_ascii=False),
            "created_by": uid,
            "created_at": now,
            "updated_at": now,
        }
    )
    row = repo.get_by_tool_name(body.tool_name)
    return success(data=_row(row))


@router.get("/tools/list")
def list_tools(
    enabled: Optional[int] = Query(None),
    current_user=Depends(require_scope("visit")),
    db=Depends(get_db),
):
    """获取已注册的工具列表。

    Args:
        enabled: 按启用状态筛选。

    Returns:
        工具列表。
    """
    role = current_user.get("role", "rep")
    McpGuardService.check_tool_access("pubmed_search", role)

    repo = McpToolsRepository(db)
    rows = repo.list_filtered(enabled=enabled)
    return success(data=[_row(r) for r in rows])


@router.patch("/tools/{tool_id}/toggle")
def toggle_tool(tool_id: int, current_user=Depends(require_scope("visit")), db=Depends(get_db)):
    """切换工具的启用/禁用状态。

    Args:
        tool_id: 工具 ID。

    Returns:
        更新后的工具信息。
    """
    role = current_user.get("role", "rep")
    McpGuardService.check_tool_access("pubmed_search", role)

    repo = McpToolsRepository(db)
    existing = repo.get_by_id(tool_id)
    if not existing:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Tool not found")
    repo.toggle_enabled(tool_id)
    updated = repo.get_by_id(tool_id)
    return success(data=_row(updated))


@router.delete("/tools/{tool_id}", status_code=status.HTTP_200_OK)
def delete_tool(tool_id: int, current_user=Depends(require_scope("visit")), db=Depends(get_db)):
    """删除指定工具。

    Args:
        tool_id: 要删除的工具 ID。

    Returns:
        被删除的工具 ID。
    """
    role = current_user.get("role", "rep")
    McpGuardService.check_tool_access("market_intel", role)

    repo = McpToolsRepository(db)
    existing = repo.get_by_id(tool_id)
    if not existing:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Tool not found")
    repo.delete(tool_id)
    return success(data={"deleted": tool_id})
