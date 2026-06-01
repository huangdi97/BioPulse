from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import AgentRolesRepository
from cloud.app.services.base import BaseService


def rd(row) -> dict:
    return {"id": row["id"], "name": row["name"], "role_type": row["role_type"],
            "description": row["description"], "system_prompt": row["system_prompt"],
            "input_schema": row["input_schema"], "output_schema": row["output_schema"],
            "temperature": row["temperature"], "max_tokens": row["max_tokens"],
            "allowed_tools": row["allowed_tools"], "is_active": row["is_active"],
            "created_by": row["created_by"], "created_at": row["created_at"],
            "updated_at": row["updated_at"]}


class AgentRoleService(BaseService):
    def _get_role_or_404(self, role_id: int) -> dict:
        repo = AgentRolesRepository(self.db)
        row = repo.get_by_id(role_id)
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Role not found")
        return row

    def create_role(self, name: str, role_type: str, description: str,
                    system_prompt: str, input_schema: str, output_schema: str,
                    temperature: float, max_tokens: int, allowed_tools: str,
                    user_id: int) -> dict:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        repo = AgentRolesRepository(self.db)
        rid = repo.create({
            "name": name, "role_type": role_type,
            "description": description, "system_prompt": system_prompt,
            "input_schema": input_schema, "output_schema": output_schema,
            "temperature": temperature, "max_tokens": max_tokens,
            "allowed_tools": allowed_tools, "created_by": user_id,
            "created_at": now, "updated_at": now,
        })
        row = repo.get_by_id(rid)
        return rd(row)

    def list_roles(self, role_type: Optional[str] = None,
                   is_active: Optional[int] = None) -> list:
        repo = AgentRolesRepository(self.db)
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
        return [rd(r) for r in rows]

    def get_role(self, role_id: int) -> dict:
        row = self._get_role_or_404(role_id)
        return rd(row)

    def update_role(self, role_id: int, name: Optional[str] = None,
                    role_type: Optional[str] = None,
                    description: Optional[str] = None,
                    system_prompt: Optional[str] = None,
                    input_schema: Optional[str] = None,
                    output_schema: Optional[str] = None,
                    temperature: Optional[float] = None,
                    max_tokens: Optional[int] = None,
                    allowed_tools: Optional[str] = None,
                    is_active: Optional[int] = None) -> dict:
        repo = AgentRolesRepository(self.db)
        self._get_role_or_404(role_id)
        updates = {}
        for f in ["name", "role_type", "description", "system_prompt", "input_schema",
                  "output_schema"]:
            v = locals().get(f)
            if v is not None:
                updates[f] = v
        if temperature is not None:
            updates["temperature"] = temperature
        if max_tokens is not None:
            updates["max_tokens"] = max_tokens
        if allowed_tools is not None:
            updates["allowed_tools"] = allowed_tools
        if is_active is not None:
            updates["is_active"] = is_active
        if updates:
            updates["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            repo.update(role_id, updates)
        row = repo.get_by_id(role_id)
        return rd(row)

    def delete_role(self, role_id: int) -> None:
        repo = AgentRolesRepository(self.db)
        self._get_role_or_404(role_id)
        repo.soft_delete(role_id)
