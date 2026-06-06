"""商机服务，负责商机数据的业务逻辑处理。"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from starlette import status

from opportunity.app.repositories import OpportunityRepository
from opportunity.app.services.base import BaseService

"""商机线索管理服务，负责商机的创建、列表、详情、更新与删除。"""


class OpportunityService(BaseService):
    """商机线索管理：创建、分页列表（支持阶段/产品/HCP筛选）、详情、更新、软删除。"""

    def create_opportunity(self, body, user_id: int) -> int:
        """创建商机线索。

        Args:
            body: 商机请求体; user_id: 用户ID

        Returns:
            int: 新商机记录ID
        """
        repo = OpportunityRepository(self.db)
        now = datetime.now(timezone.utc).isoformat()
        extra = {"created_by": user_id, "created_at": now, "updated_at": now}
        return repo.create(body.model_dump(), extra=extra)

    def list_opportunities(
        self,
        page: int,
        page_size: int,
        stage: Optional[str] = None,
        product: Optional[str] = None,
        hcp_name: Optional[str] = None,
    ) -> tuple:
        """分页查询商机列表。

        Args:
            page: 页码; page_size: 每页条数; stage: 可选阶段过滤; product: 可选产品模糊查询; hcp_name: 可选HCP姓名模糊查询

        Returns:
            tuple: (items, total, page, page_size, total_pages)
        """
        repo = OpportunityRepository(self.db)
        conditions = ["is_active = 1"]
        params: list = []

        if stage:
            conditions.append("stage = ?")
            params.append(stage)
        if product:
            conditions.append("product LIKE ?")
            params.append(f"%{product}%")
        if hcp_name:
            conditions.append("hcp_name LIKE ?")
            params.append(f"%{hcp_name}%")

        return repo.paginate(
            page=page,
            page_size=page_size,
            conditions=conditions,
            params=params,
        )

    def get_opportunity(self, opportunity_id: int) -> dict:
        """根据ID获取商机详情。

        Args:
            opportunity_id: 商机ID

        Returns:
            dict: 商机记录详情
        """
        repo = OpportunityRepository(self.db)
        row = repo.get_by_id(opportunity_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found")
        return dict(row)

    def update_opportunity(self, opportunity_id: int, body) -> dict:
        """更新商机记录。

        Args:
            opportunity_id: 商机ID; body: 更新数据请求体

        Returns:
            dict: 更新后的商机记录
        """
        repo = OpportunityRepository(self.db)
        row = repo.get_by_id(opportunity_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found")

        updates = body.model_dump(exclude_unset=True)
        if not updates:
            return dict(row)

        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        repo.update(opportunity_id, updates)
        return dict(repo.get_by_id(opportunity_id))

    def delete_opportunity(self, opportunity_id: int) -> None:
        """软删除商机记录。

        Args:
            opportunity_id: 商机ID
        """
        repo = OpportunityRepository(self.db)
        row = repo.get_by_id(opportunity_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found")
        repo.soft_delete(opportunity_id)

    def list_all_active(self) -> list:
        """列出所有活跃商机。

        Returns:
            list: 活跃商机列表
        """
        repo = OpportunityRepository(self.db)
        return repo.list_all(conditions=["is_active = 1"])
