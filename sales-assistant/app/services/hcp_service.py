"""HCP管理服务：HCP、产品、关联关系的CRUD与图谱查询。"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from starlette import status

from sales_assistant.app.repositories import HcpRepository
from sales_assistant.app.services.base import BaseCrudService
from sales_assistant.app.services.hcp_search import HcpSearchMixin
from sales_assistant.app.services.hcp_stats import HcpStatsMixin


class HcpService(HcpSearchMixin, HcpStatsMixin, BaseCrudService):
    """HCP管理服务：管理医生信息、产品及HCP-产品关联关系图谱。"""

    _repo_class = HcpRepository
    _entity_name = "HCP"

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def create_hcp(self, body, user_id: int) -> int:
        """创建HCP档案。

        Args:
            body: HCP创建请求体。
            user_id: 创建人用户ID。

        Returns:
            新HCP记录ID。

        Raises:
            sqlite3.Error: 当HCP写入失败时由仓储层抛出。
        """
        repo = HcpRepository(self.db)
        now = self._now()
        return repo.create(body.model_dump(), extra={"created_by": user_id, "created_at": now, "updated_at": now})

    def list_hcps(
        self, page: int, page_size: int, name: Optional[str] = None, hospital: Optional[str] = None, department: Optional[str] = None
    ) -> tuple:
        """分页查询活跃HCP档案。

        Args:
            page: 当前页码。
            page_size: 每页数量。
            name: 可选的姓名模糊搜索关键词。
            hospital: 可选的医院模糊搜索关键词。
            department: 可选的科室模糊搜索关键词。

        Returns:
            仓储层分页元组。

        Raises:
            sqlite3.Error: 当HCP查询失败时由仓储层抛出。
        """
        repo = HcpRepository(self.db)
        conditions, params = ["is_active = 1"], []
        if name:
            conditions.append("name LIKE ?")
            params.append(f"%{name}%")
        if hospital:
            conditions.append("hospital LIKE ?")
            params.append(f"%{hospital}%")
        if department:
            conditions.append("department LIKE ?")
            params.append(f"%{department}%")
        return repo.paginate(page, page_size, conditions, params)

    def get_hcp(self, hcp_id: int) -> dict:
        """读取单个HCP档案。

        Args:
            hcp_id: HCP记录ID。

        Returns:
            HCP记录字典。

        Raises:
            HTTPException: 当HCP不存在或已停用时抛出404。
        """
        repo = HcpRepository(self.db)
        row = repo.get_by_id(hcp_id)
        if not row or not row["is_active"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="HCP not found")
        return dict(row)

    def update_hcp(self, hcp_id: int, body) -> dict:
        """更新HCP档案字段。

        Args:
            hcp_id: HCP记录ID。
            body: HCP更新请求体。

        Returns:
            更新后的HCP记录字典；无更新字段时返回原记录。

        Raises:
            HTTPException: 当HCP不存在或已停用时抛出404。
        """
        repo = HcpRepository(self.db)
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
        """软删除HCP档案。

        Args:
            hcp_id: HCP记录ID。

        Returns:
            None。

        Raises:
            HTTPException: 当HCP不存在或已停用时抛出404。
        """
        repo = HcpRepository(self.db)
        row = repo.get_by_id(hcp_id)
        if not row or not row["is_active"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="HCP not found")
        repo.soft_delete(hcp_id)
