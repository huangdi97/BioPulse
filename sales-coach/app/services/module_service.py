from datetime import datetime, timezone
from typing import Optional

from sales_coach.app.repositories import ModuleRepository
from sales_coach.app.services.base import BaseService


class ModuleService(BaseService):
    def create(self, body, user_id: int) -> dict:
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
            page=page, page_size=page_size,
            conditions=conditions, params=params, order_by="id DESC",
        )

    def get(self, module_id: int) -> dict:
        repo = ModuleRepository(self.db)
        return dict(repo.get_active_or_404(module_id))

    def update(self, module_id: int, body) -> dict:
        repo = ModuleRepository(self.db)
        repo.get_active_or_404(module_id)
        updates = body.model_dump(exclude_unset=True)
        if not updates:
            return dict(repo.get_by_id(module_id))
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        repo.update(module_id, updates)
        return dict(repo.get_by_id(module_id))

    def delete(self, module_id: int) -> None:
        repo = ModuleRepository(self.db)
        repo.get_active_or_404(module_id)
        repo.soft_delete(module_id)
