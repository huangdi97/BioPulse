"""培训模块服务模块，管理培训课程的增删改查。"""

from datetime import datetime, timezone
from typing import Optional

from sales_coach.app.repositories import ModuleRepository
from shared.base_service import BaseService


class ModuleService(BaseService):
    """培训模块服务，提供模块的创建、分页查询、更新与软删除。"""

    def create(self, body, user_id: int) -> dict:
        """创建培训模块。

        Args:
            body: 模块请求体。
            user_id: 创建者用户ID。

        Returns:
            包含新创建模块ID的字典。
        """
        repo = ModuleRepository(self.db)
        now = datetime.now(timezone.utc).isoformat()
        data = body.model_dump()
        extra = {"created_by": user_id, "created_at": now, "updated_at": now}
        lastrowid = repo.create(data, extra=extra)
        return {"id": lastrowid}

    def list(
        self,
        page: int,
        page_size: int,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
    ) -> tuple:
        """分页查询模块列表。

        Args:
            page: 页码。
            page_size: 每页条数。
            category: 按分类筛选。
            difficulty: 按难度筛选。

        Returns:
            (记录列表, 总条数) 元组。
        """
        repo = ModuleRepository(self.db)
        conditions = []
        params = []

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

    def get(self, module_id: int) -> dict:
        """获取单个模块详情。

        Args:
            module_id: 模块ID。

        Returns:
            模块详情字典，不存在或已删除则抛404。
        """
        repo = ModuleRepository(self.db)
        return dict(repo.get_active_or_404(module_id))

    def update(self, module_id: int, body) -> dict:
        """更新模块。

        Args:
            module_id: 模块ID。
            body: 更新数据。

        Returns:
            更新后的模块详情。
        """
        repo = ModuleRepository(self.db)
        repo.get_active_or_404(module_id)
        updates = body.model_dump(exclude_unset=True)
        if not updates:
            return dict(repo.get_by_id(module_id))
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        repo.update(module_id, updates)
        return dict(repo.get_by_id(module_id))

    def delete(self, module_id: int) -> None:
        """软删除模块。

        Args:
            module_id: 模块ID。
        """
        repo = ModuleRepository(self.db)
        repo.get_active_or_404(module_id)
        repo.soft_delete(module_id)
