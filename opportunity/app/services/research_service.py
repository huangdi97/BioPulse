"""科研信息服务，用于查询和管理科研相关数据。"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from starlette import status

from opportunity.app.repositories import ResearchTrailRepository
from opportunity.app.services.base import BaseService

"""科研轨迹服务，管理HCP科研动态轨迹的增删改查。"""


class ResearchService(BaseService):
    """科研轨迹管理：创建、分页列表（支持HCP/主题/期刊/相关性筛选）、详情、更新、软删除。"""

    def create_research_trail(self, body, user_id: int) -> int:
        """创建科研轨迹记录。

        Args:
            body: 科研轨迹请求体; user_id: 用户ID

        Returns:
            int: 新科研轨迹记录ID
        """
        repo = ResearchTrailRepository(self.db)
        now = datetime.now(timezone.utc).isoformat()
        return repo.create(
            body.model_dump(),
            extra={
                "created_by": user_id,
                "created_at": now,
                "updated_at": now,
            },
        )

    def list_research_trails(
        self,
        page: int,
        page_size: int,
        hcp_name: Optional[str] = None,
        topic: Optional[str] = None,
        journal: Optional[str] = None,
        relevance_min: Optional[int] = None,
    ) -> tuple:
        """分页查询科研轨迹列表。

        Args:
            page: 页码; page_size: 每页条数; hcp_name: 可选HCP姓名模糊查询; topic: 可选主题模糊查询; journal: 可选期刊模糊查询; relevance_min: 可选最小相关性过滤

        Returns:
            tuple: (items, total, page, page_size, total_pages)
        """
        repo = ResearchTrailRepository(self.db)
        conditions = ["is_active = 1"]
        params: list = []

        if hcp_name:
            conditions.append("hcp_name LIKE ?")
            params.append(f"%{hcp_name}%")
        if topic:
            conditions.append("topic LIKE ?")
            params.append(f"%{topic}%")
        if journal:
            conditions.append("journal LIKE ?")
            params.append(f"%{journal}%")
        if relevance_min is not None:
            conditions.append("relevance >= ?")
            params.append(relevance_min)

        return repo.paginate(
            page=page,
            page_size=page_size,
            conditions=conditions,
            params=params,
        )

    def get_research_trail(self, trail_id: int) -> dict:
        """根据ID获取科研轨迹详情。

        Args:
            trail_id: 科研轨迹ID

        Returns:
            dict: 科研轨迹记录详情
        """
        row = self.db.execute(
            "SELECT * FROM research_trail WHERE id = ? AND is_active = 1",
            (trail_id,),
        ).fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Research trail not found",
            )
        return dict(row)

    def update_research_trail(self, trail_id: int, body) -> dict:
        """更新科研轨迹记录。

        Args:
            trail_id: 科研轨迹ID; body: 更新数据请求体

        Returns:
            dict: 更新后的科研轨迹记录
        """
        repo = ResearchTrailRepository(self.db)
        row = repo.get_by_id(trail_id)
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Research trail not found",
            )

        updates = body.model_dump(exclude_unset=True)
        if not updates:
            return dict(row)

        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        repo.update(trail_id, updates)
        return dict(repo.get_by_id(trail_id))

    def delete_research_trail(self, trail_id: int) -> None:
        """软删除科研轨迹记录。

        Args:
            trail_id: 科研轨迹ID
        """
        repo = ResearchTrailRepository(self.db)
        row = repo.get_by_id(trail_id)
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Research trail not found",
            )
        repo.soft_delete(trail_id)
