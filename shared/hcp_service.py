"""Shared HCP CRUD helpers for assistant and sales-assistant services."""

from datetime import datetime, timezone
from typing import Any, Optional

from shared.base_service import BaseService


class BaseHcpService(BaseService):
    """Shared base for HCP management across assistant and sales-assistant."""

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _build_list_conditions(
        self,
        name: Optional[str] = None,
        hospital: Optional[str] = None,
        department: Optional[str] = None,
        level: Optional[str] = None,
    ) -> tuple[list[str], list]:
        conditions = ["is_active = 1"]
        params: list = []
        if name:
            conditions.append("name LIKE ?")
            params.append(f"%{name}%")
        if hospital:
            conditions.append("hospital LIKE ?")
            params.append(f"%{hospital}%")
        if department:
            conditions.append("department LIKE ?")
            params.append(f"%{department}%")
        if level:
            conditions.append("level = ?")
            params.append(level)
        return conditions, params
