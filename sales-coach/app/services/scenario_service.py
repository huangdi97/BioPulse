"""场景服务模块，管理教练场景的增删改查。"""

from datetime import datetime, timezone
from typing import Optional

from sales_coach.app.repositories import ScenarioRepository
from sales_coach.app.services.base import BaseService


class ScenarioService(BaseService):
    """教练场景服务，提供场景的创建、分页查询、更新与软删除。"""

    def create(self, body, user_id: int) -> dict:
        """创建教练场景。

        Args:
            body: 场景请求体。
            user_id: 创建者用户ID。

        Returns:
            包含新创建场景ID的字典。
        """
        repo = ScenarioRepository(self.db)
        now = datetime.now(timezone.utc).isoformat()
        scenario_id = repo.create(
            data={
                "title": body.title,
                "role_setting": body.role_setting,
                "goal": body.goal,
                "difficulty": body.difficulty,
                "category": body.category,
                "content": body.content,
                "tips": body.tips,
            },
            extra={
                "created_by": user_id,
                "created_at": now,
                "updated_at": now,
            },
        )
        return {"id": scenario_id}

    def list(
        self,
        page: int,
        page_size: int,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
    ) -> tuple:
        """分页查询场景列表。

        Args:
            page: 页码。
            page_size: 每页条数。
            category: 按分类筛选。
            difficulty: 按难度筛选。

        Returns:
            (记录列表, 总条数) 元组。
        """
        repo = ScenarioRepository(self.db)
        conditions = []
        params: list = []

        if category:
            conditions.append("category = ?")
            params.append(category)
        if difficulty:
            conditions.append("difficulty = ?")
            params.append(difficulty)

        return repo.paginate_active(
            page=page,
            page_size=page_size,
            conditions=conditions,
            params=params,
            order_by="id DESC",
        )

    def get(self, scenario_id: int) -> dict:
        """获取单个场景详情。

        Args:
            scenario_id: 场景ID。

        Returns:
            场景详情字典，不存在或已删除则抛404。
        """
        repo = ScenarioRepository(self.db)
        return dict(repo.get_active_or_404(scenario_id))

    def update(self, scenario_id: int, body) -> dict:
        """更新场景。

        Args:
            scenario_id: 场景ID。
            body: 更新数据。

        Returns:
            更新后的场景详情。
        """
        repo = ScenarioRepository(self.db)
        repo.get_active_or_404(scenario_id)
        updates = body.model_dump(exclude_unset=True)
        if not updates:
            return dict(repo.get_by_id(scenario_id))
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        repo.update(scenario_id, updates)
        return dict(repo.get_by_id(scenario_id))

    def delete(self, scenario_id: int) -> None:
        """软删除场景。

        Args:
            scenario_id: 场景ID。
        """
        repo = ScenarioRepository(self.db)
        repo.get_active_or_404(scenario_id)
        repo.soft_delete(scenario_id)
