"""服务层基类——供各子项目继承使用。"""

import importlib
import sqlite3

from fastapi import HTTPException
from starlette import status


class BaseService:
    """服务基类，支持两种数据库连接模式：

    - sqlite3 直连：通过 `_connection(db_path)` 打开并返回连接
    - FastAPI 依赖注入：通过 `__init__(db=...)` 注入连接后，`self.db` 可用
    """

    def __init__(self, db=None):
        self.db = db


    def _connect(self, db_path: str):
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _connection(self):
        if hasattr(self, "db") and self.db is not None:
            return self.db
        db_path = self._default_db_path()
        if db_path:
            return self._connect(db_path)
        raise NotImplementedError("Override _connection() or pass db to __init__")

    def _default_db_path(self) -> str | None:
        module_name = self.__class__.__module__
        marker = ".app.services."
        if marker not in module_name:
            return None
        app_root = module_name.split(marker, 1)[0]
        try:
            database_module = importlib.import_module(f"{app_root}.app.database")
        except ImportError:
            return None
        return getattr(database_module, "DB_PATH", None)


class BaseCrudService(BaseService):
    """CRUD 基类，自动处理连接/404 检查。"""

    def __init__(self, repository_class=None, entity_name="entity", db=None):
        super().__init__(db)
        self._repo_class = repository_class
        self._entity_name = entity_name

    def _close_connection(self, conn):
        conn.close()

    def create(self, body, user_id: int, **extra) -> dict:
        conn = self._connection()
        try:
            repo = self._repo_class(conn)
            row_id = repo.create(body.model_dump(), extra={"created_by": user_id, **extra})
            return {"id": row_id}
        finally:
            self._close_connection(conn)

    def get_by_id(self, entity_id: int) -> dict:
        conn = self._connection()
        try:
            repo = self._repo_class(conn)
            row = repo.get_by_id(entity_id)
            if not row:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{self._entity_name} not found")
            return dict(row)
        finally:
            self._close_connection(conn)

    def update(self, entity_id: int, body) -> dict:
        conn = self._connection()
        try:
            repo = self._repo_class(conn)
            existing = repo.get_by_id(entity_id)
            if not existing:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{self._entity_name} not found")
            repo.update(entity_id, body.model_dump(exclude_unset=True))
            return {"updated": entity_id}
        finally:
            self._close_connection(conn)

    def delete(self, entity_id: int) -> None:
        conn = self._connection()
        try:
            repo = self._repo_class(conn)
            existing = repo.get_by_id(entity_id)
            if not existing:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{self._entity_name} not found")
            repo.delete(entity_id)
        finally:
            self._close_connection(conn)

    def list(self, page: int = 1, page_size: int = 20, **filters) -> tuple:
        conn = self._connection()
        try:
            repo = self._repo_class(conn)
            rows = repo.list(page=page, page_size=page_size, **filters)
            total = repo.count(**filters)
            return [dict(r) for r in rows], total
        finally:
            self._close_connection(conn)

    def paginate(self, page: int = 1, page_size: int = 20, **filters) -> dict:
        items, total = self.list(page=page, page_size=page_size, **filters)
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }
