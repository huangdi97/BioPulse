import json
from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import McpToolsRepository
from cloud.app.services.base import BaseService


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


class McpService(BaseService):
    def register_tool(self, tool_name: str, description: str, endpoint_url: str,
                      input_schema: dict, output_schema: dict, user_id: int) -> dict:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        repo = McpToolsRepository(self.db)
        repo.create({
            "tool_name": tool_name,
            "description": description,
            "endpoint_url": endpoint_url,
            "input_schema": json.dumps(input_schema, ensure_ascii=False),
            "output_schema": json.dumps(output_schema, ensure_ascii=False),
            "created_by": user_id,
            "created_at": now,
            "updated_at": now,
        })
        row = repo.get_by_tool_name(tool_name)
        return _row(row)

    def list_tools(self, enabled: Optional[int] = None) -> list:
        repo = McpToolsRepository(self.db)
        rows = repo.list_filtered(enabled=enabled)
        return [_row(r) for r in rows]

    def toggle_tool(self, tool_id: int) -> dict:
        repo = McpToolsRepository(self.db)
        existing = repo.get_by_id(tool_id)
        if not existing:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Tool not found")
        repo.toggle_enabled(tool_id)
        updated = repo.get_by_id(tool_id)
        return _row(updated)

    def delete_tool(self, tool_id: int) -> int:
        repo = McpToolsRepository(self.db)
        existing = repo.get_by_id(tool_id)
        if not existing:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Tool not found")
        repo.delete(tool_id)
        return tool_id
