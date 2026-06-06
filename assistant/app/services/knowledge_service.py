"""知识库服务模块。"""

from datetime import datetime, timezone
from typing import Optional

from assistant.app.repositories import KnowledgeBaseRepository
from assistant.app.services.base import BaseService


class KnowledgeService(BaseService):
    """知识库服务，提供知识条目的增删改查、分类与全文搜索。"""

    def create(self, body, user_id: int) -> dict:
        """创建知识库条目。

        Args:
            body: 知识条目请求体; user_id: 用户ID

        Returns:
            dict: 包含新条目 id 的结果
        """
        repo = KnowledgeBaseRepository(self.db)
        now = datetime.now(timezone.utc).isoformat()
        row_id = repo.create(
            {
                **body.model_dump(),
                "created_by": user_id,
                "created_at": now,
                "updated_at": now,
            },
        )
        return {"id": row_id}

    def list(
        self,
        page: int,
        page_size: int,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
    ) -> tuple:
        """分页查询知识库列表。

        Args:
            page: 页码; page_size: 每页条数; category: 可选分类过滤; difficulty: 可选难度过滤

        Returns:
            tuple: (items, total, page, page_size, total_pages)
        """
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
        """列出所有知识分类。

        Returns:
            list: 去重排序的分类列表
        """
        repo = KnowledgeBaseRepository(self.db)
        rows = repo.list_all(
            conditions=["category IS NOT NULL", "is_active = 1"],
            order_by="category ASC",
        )
        categories = list({r["category"] for r in rows})
        return sorted(categories)

    def search(self, q: str, page: int, page_size: int) -> tuple:
        """全文搜索知识库。

        Args:
            q: 搜索关键词; page: 页码; page_size: 每页条数

        Returns:
            tuple: (total, total_pages, rows)
        """
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
        """根据ID获取知识条目详情。

        Args:
            knowledge_id: 知识条目ID

        Returns:
            dict: 知识条目详情
        """
        repo = KnowledgeBaseRepository(self.db)
        return dict(repo.get_or_404(knowledge_id))

    def update(self, knowledge_id: int, body) -> dict:
        """更新知识条目。

        Args:
            knowledge_id: 知识条目ID; body: 更新数据请求体

        Returns:
            dict: 更新后的知识条目
        """
        repo = KnowledgeBaseRepository(self.db)
        repo.get_or_404(knowledge_id)
        updates = body.model_dump(exclude_unset=True)
        if not updates:
            return dict(repo.get_by_id(knowledge_id))
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        repo.update(knowledge_id, updates)
        return dict(repo.get_by_id(knowledge_id))

    def delete(self, knowledge_id: int) -> None:
        """软删除知识条目。

        Args:
            knowledge_id: 知识条目ID
        """
        repo = KnowledgeBaseRepository(self.db)
        repo.get_or_404(knowledge_id)
        repo.soft_delete(knowledge_id)
