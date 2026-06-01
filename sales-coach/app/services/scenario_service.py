from datetime import datetime, timezone
from typing import Optional

from sales_coach.app.repositories import ScenarioRepository
from sales_coach.app.services.base import BaseService


class ScenarioService(BaseService):
    def create(self, body, user_id: int) -> dict:
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
        repo = ScenarioRepository(self.db)
        return dict(repo.get_active_or_404(scenario_id))

    def update(self, scenario_id: int, body) -> dict:
        repo = ScenarioRepository(self.db)
        repo.get_active_or_404(scenario_id)
        updates = body.model_dump(exclude_unset=True)
        if not updates:
            return dict(repo.get_by_id(scenario_id))
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        repo.update(scenario_id, updates)
        return dict(repo.get_by_id(scenario_id))

    def delete(self, scenario_id: int) -> None:
        repo = ScenarioRepository(self.db)
        repo.get_active_or_404(scenario_id)
        repo.soft_delete(scenario_id)
