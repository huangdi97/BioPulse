from datetime import datetime, timezone
from typing import List, Optional

from assistant.app.repositories import KnowledgeBaseRepository
from assistant.app.services.base import BaseService


class KnowledgeService(BaseService):
    def create(self, body, user_id: int) -> dict:
        repo = KnowledgeBaseRepository(self.db)
        now = datetime.now(timezone.utc).isoformat()
        row_id = repo.create(
            {**body.model_dump(),
             "created_by": user_id, "created_at": now, "updated_at": now},
        )
        return {"id": row_id}

    def list(
        self,
        page: int,
        page_size: int,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
    ) -> tuple:
        repo = KnowledgeBaseRepository(self.db)
        conditions = ["is_active = 1"]
        params: list = []
        if category:
            conditions.append("category = ?")
            params.append(category)
        if difficulty:
            conditions.append("difficulty = ?")
            params.append(difficulty)

        return repo.paginate(page, page_size, conditions, params)

    def list_categories(self) -> list:
        repo = KnowledgeBaseRepository(self.db)
        rows = repo.list_all(
            conditions=["category IS NOT NULL", "is_active = 1"],
            order_by="category ASC",
        )
        categories = list({r["category"] for r in rows})
        return sorted(categories)

    def search(self, q: str, page: int, page_size: int) -> tuple:
        match_expr = q
        count_row = self.db.execute(
            "SELECT COUNT(*) FROM knowledge_fts WHERE knowledge_fts MATCH ?",
            (match_expr,),
        ).fetchone()
        total = count_row[0]
        total_pages = max(1, (total + page_size - 1) // page_size)
        offset = (page - 1) * page_size
        rows = self.db.execute(
            """SELECT k.* FROM knowledge_fts f JOIN knowledge_base k ON f.rowid = k.id
               WHERE knowledge_fts MATCH ? AND k.is_active = 1
               ORDER BY rank LIMIT ? OFFSET ?""",
            (match_expr, page_size, offset),
        ).fetchall()
        return total, total_pages, rows

    def get(self, knowledge_id: int) -> dict:
        repo = KnowledgeBaseRepository(self.db)
        return dict(repo.get_or_404(knowledge_id))

    def update(self, knowledge_id: int, body) -> dict:
        repo = KnowledgeBaseRepository(self.db)
        repo.get_or_404(knowledge_id)
        updates = body.model_dump(exclude_unset=True)
        if not updates:
            return dict(repo.get_by_id(knowledge_id))
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        repo.update(knowledge_id, updates)
        return dict(repo.get_by_id(knowledge_id))

    def delete(self, knowledge_id: int) -> None:
        repo = KnowledgeBaseRepository(self.db)
        repo.get_or_404(knowledge_id)
        repo.soft_delete(knowledge_id)
