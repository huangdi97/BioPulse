"""Agent 角色服务，管理 Agent 角色的增删改查（含系统提示词与参数配置）。"""

from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import AgentRolesRepository
from shared.base_service import BaseService


class AgentRoleService(BaseService):
    """AgentRole 服务类。"""

    def _rd(self, row) -> dict:
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

    def _404(self, repo, rid):
        row = repo.get_by_id(rid)
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Role not found")
        return row

    def create_role(self, body, uid) -> dict:
        """create_role 操作。

        Args:
            uid: 描述

        Returns:
            描述
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        repo = AgentRolesRepository(self._connection())
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
        return self._rd(row)

    def list_roles(self, role_type: Optional[str] = None, is_active: Optional[int] = None) -> list:
        """list_roles 操作。

        Args:
            role_type: 描述
            is_active: 描述

        Returns:
            描述
        """
        repo = AgentRolesRepository(self._connection())
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
        return [self._rd(r) for r in rows]

    def get_role(self, role_id: int) -> dict:
        """get_role 操作。

        Args:
            role_id: 描述

        Returns:
            描述
        """
        repo = AgentRolesRepository(self._connection())
        row = self._404(repo, role_id)
        return self._rd(row)

    def update_role(self, role_id: int, body) -> dict:
        """update_role 操作。

        Args:
            role_id: 描述

        Returns:
            描述
        """
        repo = AgentRolesRepository(self._connection())
        self._404(repo, role_id)
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
        return self._rd(row)

    def delete_role(self, role_id: int) -> None:
        """delete_role 操作。

        Args:
            role_id: 描述

        Returns:
            描述
        """
        repo = AgentRolesRepository(self._connection())
        self._404(repo, role_id)
        repo.soft_delete(role_id)
