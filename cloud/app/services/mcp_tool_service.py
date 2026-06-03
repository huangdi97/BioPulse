import json
from datetime import datetime
from typing import Optional

from fastapi import Depends, HTTPException
from starlette import status

from cloud.app.database import get_db
from cloud.app.repositories import McpToolsRepository
from cloud.app.services.base import BaseService
from cloud.app.services.mcp_guard_service import McpGuardService


class McpToolService(BaseService):
    """McpTool 服务类。"""

    def __init__(self, db=Depends(get_db)):
        super().__init__(db)
        self.repo = McpToolsRepository(db)

    @staticmethod
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

    def register_tool(self, body, uid: int, role: str) -> dict:
        """register_tool 操作。

        Args:
            uid: 描述
            role: 描述

        Returns:
            描述
        """
        McpGuardService.check_tool_access(body.tool_name, role)
        if not McpGuardService.validate_tool_version(body.tool_name, "1.0.0"):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail=f"Tool '{body.tool_name}' version mismatch, expected {McpGuardService.TOOL_REGISTRY.get(body.tool_name, {}).get('version', 'unknown')}",
            )

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.repo.create(
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
        row = self.repo.get_by_tool_name(body.tool_name)
        return self._row(row)

    def list_tools(self, is_active: Optional[int] = None, page: int = 1, page_size: int = 20) -> dict:
        """list_tools 操作。

        Args:
            is_active: 描述
            page: 描述
            page_size: 描述

        Returns:
            描述
        """
        rows = self.repo.list_filtered(enabled=is_active)
        items = [self._row(r) for r in rows]
        offset = (page - 1) * page_size
        return {
            "items": items[offset : offset + page_size],
            "total": len(items),
            "page": page,
            "page_size": page_size,
        }

    def call_tool(self, tool_name: str, params: dict, user_id: int) -> dict:
        """call_tool 操作。

        Args:
            tool_name: 描述
            params: 描述
            user_id: 描述

        Returns:
            描述
        """
        row = self.repo.get_by_tool_name(tool_name)
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Tool '{tool_name}' not found")
        McpGuardService.check_tool_access(tool_name, "rep")
        return {"status": "ok", "tool_name": tool_name, "params": params, "user_id": user_id}

    def toggle_tool(self, tool_id: int) -> dict:
        """toggle_tool 操作。

        Args:
            tool_id: 描述

        Returns:
            描述
        """
        existing = self.repo.get_by_id(tool_id)
        if not existing:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Tool not found")
        self.repo.toggle_enabled(tool_id)
        updated = self.repo.get_by_id(tool_id)
        return self._row(updated)

    def delete_tool(self, tool_id: int) -> dict:
        """delete_tool 操作。

        Args:
            tool_id: 描述

        Returns:
            描述
        """
        existing = self.repo.get_by_id(tool_id)
        if not existing:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Tool not found")
        self.repo.delete(tool_id)
        return {"deleted": tool_id}
