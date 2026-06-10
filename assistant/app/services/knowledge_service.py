"""知识库服务模块。"""

from datetime import datetime, timezone
from typing import Optional

from assistant.app.repositories import KnowledgeBaseRepository
from shared.base_service import BaseCrudService


class KnowledgeService(BaseCrudService):
    """知识库服务，提供知识条目的增删改查、分类与全文搜索。"""

    def __init__(self, db=None):
        super().__init__(repository_class=KnowledgeBaseRepository, entity_name="Knowledge", db=db)

    def create(self, body, user_id: int) -> dict:
        """创建知识库条目。

        Args:
            body: 知识条目请求体; user_id: 用户ID

        Returns:
            dict: 包含新条目 id 的结果
        """
        conn = self._connection()
        try:
            repo = KnowledgeBaseRepository(conn)
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
        finally:
            self._close_connection(conn)

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
        conn = self._connection()
        try:
            repo = KnowledgeBaseRepository(conn)
            conditions = ["is_active = 1"]
            params: list = []
            if category:
                conditions.append("category = ?")
                params.append(category)
            if difficulty:
                conditions.append("difficulty = ?")
                params.append(difficulty)

            return repo.paginate(page, page_size, conditions, params)
        finally:
            self._close_connection(conn)

    def list_categories(self) -> list:
        """列出所有知识分类。

        Returns:
            list: 去重排序的分类列表
        """
        conn = self._connection()
        try:
            repo = KnowledgeBaseRepository(conn)
            rows = repo.list_all(
                conditions=["category IS NOT NULL", "is_active = 1"],
                order_by="category ASC",
            )
            categories = list({r["category"] for r in rows})
            return sorted(categories)
        finally:
            self._close_connection(conn)

    def search(self, q: str, page: int, page_size: int) -> tuple:
        """全文搜索知识库。

        Args:
            q: 搜索关键词; page: 页码; page_size: 每页条数

        Returns:
            tuple: (total, total_pages, rows)
        """
        conn = self._connection()
        try:
            match_expr = q
            count_row = conn.execute(
                "SELECT COUNT(*) FROM knowledge_fts WHERE knowledge_fts MATCH ?",
                (match_expr,),
            ).fetchone()
            total = count_row[0]
            total_pages = max(1, (total + page_size - 1) // page_size)
            offset = (page - 1) * page_size
            rows = conn.execute(
                """SELECT k.* FROM knowledge_fts f JOIN knowledge_base k ON f.rowid = k.id
                   WHERE knowledge_fts MATCH ? AND k.is_active = 1
                   ORDER BY rank LIMIT ? OFFSET ?""",
                (match_expr, page_size, offset),
            ).fetchall()
            return total, total_pages, rows
        finally:
            self._close_connection(conn)

    def get(self, knowledge_id: int) -> dict:
        """根据ID获取知识条目详情。

        Args:
            knowledge_id: 知识条目ID

        Returns:
            dict: 知识条目详情
        """
        conn = self._connection()
        try:
            repo = KnowledgeBaseRepository(conn)
            return dict(repo.get_or_404(knowledge_id))
        finally:
            self._close_connection(conn)

    def update(self, knowledge_id: int, body) -> dict:
        """更新知识条目。

        Args:
            knowledge_id: 知识条目ID; body: 更新数据请求体

        Returns:
            dict: 更新后的知识条目
        """
        conn = self._connection()
        try:
            repo = KnowledgeBaseRepository(conn)
            repo.get_or_404(knowledge_id)
            updates = body.model_dump(exclude_unset=True)
            if not updates:
                return dict(repo.get_by_id(knowledge_id))
            updates["updated_at"] = datetime.now(timezone.utc).isoformat()
            repo.update(knowledge_id, updates)
            return dict(repo.get_by_id(knowledge_id))
        finally:
            self._close_connection(conn)

    def delete(self, knowledge_id: int) -> None:
        """软删除知识条目。

        Args:
            knowledge_id: 知识条目ID
        """
        conn = self._connection()
        try:
            repo = KnowledgeBaseRepository(conn)
            repo.get_or_404(knowledge_id)
            repo.soft_delete(knowledge_id)
        finally:
            self._close_connection(conn)
