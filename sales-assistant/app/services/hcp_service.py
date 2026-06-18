"""HCP管理服务：HCP、产品、关联关系的CRUD与图谱查询。"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from starlette import status

from sales_assistant.app.repositories import HcpRepository
from sales_assistant.app.services.hcp_search import HcpSearchMixin
from sales_assistant.app.services.hcp_stats import HcpStatsMixin
from shared.base_service import BaseCrudService
from shared.hcp_service import BaseHcpService


class HcpService(HcpSearchMixin, HcpStatsMixin, BaseHcpService, BaseCrudService):
    """HCP管理服务：管理医生信息、产品及HCP-产品关联关系图谱。"""

    def __init__(self, db=None):
        super().__init__(repository_class=HcpRepository, entity_name="HCP", db=db)

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def create_hcp(self, body, user_id: int) -> int:
        repo = HcpRepository(self._connection())
        now = self._now()
        return repo.create(body.model_dump(), extra={"created_by": user_id, "created_at": now, "updated_at": now})

    def list_hcps(
        self, page: int, page_size: int, name: Optional[str] = None, hospital: Optional[str] = None, department: Optional[str] = None
    ) -> tuple:
        repo = HcpRepository(self._connection())
        conditions, params = self._build_list_conditions(name, hospital, department)
        return repo.paginate(page, page_size, conditions, params)

    def get_hcp(self, hcp_id: int) -> dict:
        repo = HcpRepository(self._connection())
        row = repo.get_by_id(hcp_id)
        if not row or not row["is_active"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="HCP not found")
        return dict(row)

    def update_hcp(self, hcp_id: int, body) -> dict:
        repo = HcpRepository(self._connection())
        row = repo.get_by_id(hcp_id)
        if not row or not row["is_active"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="HCP not found")
        updates = body.model_dump(exclude_unset=True)
        if not updates:
            return dict(row)
        updates["updated_at"] = self._now()
        repo.update(hcp_id, updates)
        return dict(repo.get_by_id(hcp_id))

    def delete_hcp(self, hcp_id: int) -> None:
        repo = HcpRepository(self._connection())
        row = repo.get_by_id(hcp_id)
        if not row or not row["is_active"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="HCP not found")
        repo.soft_delete(hcp_id)
