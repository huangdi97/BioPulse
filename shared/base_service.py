"""服务层基类——供各子项目继承使用。"""

import importlib
import sqlite3

from fastapi import HTTPException
from starlette import status


class BaseService:
    """服务基类，支持三种数据库连接模式：

    - sqlite3 直连：通过 `_connect(db_path)` 打开并返回连接
    - PostgreSQL 连接：若 `DATABASE_URL` 为 PG 协议，自动切换 psycopg
    - FastAPI 依赖注入：通过 `__init__(db=...)` 注入连接后，`self.db` 可用
    """

    def __init__(self, db=None):
        """初始化服务实例，接收可选的数据库连接。

        参数:
            db: 可选的数据库连接对象，若为 None 则尝试自动连接
        """
        self.db = db
        if self.db is None:
            try:
                self.db = self._connection()
            except (NotImplementedError, ImportError, ModuleNotFoundError):
                pass

    def _connect(self, db_path: str):
        """根据路径创建连接。

        支持 SQLite 和 PostgreSQL 两种模式：
        - SQLite: `sqlite3.connect(db_path)`
        - PostgreSQL: `psycopg.connect(db_path)` + `PGCompatConnection` 包装

        参数:
            db_path: 数据库文件路径或 PG 连接串

        返回:
            sqlite3.Connection 或 PGCompatConnection 对象
        """
        if db_path.startswith("postgresql://") or db_path.startswith("postgres://"):
            import psycopg

            from shared.db import PGCompatConnection

            return PGCompatConnection(psycopg.connect(db_path))
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _connection(self):
        """获取数据库连接，优先使用已存在的连接，否则自动创建。"""
        if hasattr(self, "db") and self.db is not None:
            return self.db
        db_path = self._default_db_path()
        if db_path:
            self.db = self._connect(db_path)
            return self.db
        raise NotImplementedError("Override _connection() or pass db to __init__")

    def _default_db_path(self) -> str | None:
        """根据类的模块名推断默认数据库路径。

        PG 模式时返回 DATABASE_URL，SQLite 模式时返回 DB_PATH。

        返回:
            数据库路径字符串或 PG 连接串，若无法推断则返回 None
        """
        module_name = self.__class__.__module__
        marker = ".app.services"
        if marker not in module_name:
            return None
        app_root = module_name.split(marker, 1)[0]
        try:
            database_module = importlib.import_module(f"{app_root}.app.database")
        except (ImportError, ModuleNotFoundError):
            return None
        # PG 模式：优先使用 DATABASE_URL
        database_url = getattr(database_module, "DATABASE_URL", None)
        if database_url and (database_url.startswith("postgresql://") or database_url.startswith("postgres://")):
            return database_url
        return getattr(database_module, "DB_PATH", None)


class BaseCrudService(BaseService):
    """CRUD 基类，自动处理连接/404 检查。"""

    def __init__(self, repository_class=None, entity_name="entity", db=None):
        """初始化 CRUD 服务，绑定仓储类与实体名称。

        参数:
            repository_class: 对应的仓储类
            entity_name: 实体名称，用于错误信息
            db: 可选的数据库连接
        """
        super().__init__(db)
        self._repo_class = repository_class
        self._entity_name = entity_name

    def _close_connection(self, conn):
        """关闭数据库连接。

        参数:
            conn: 待关闭的数据库连接对象
        """
        conn.close()

    def create(self, body, user_id: int, **extra) -> dict:
        """创建实体记录。

        参数:
            body: 请求体（Pydantic 模型）
            user_id: 创建者用户 ID
            **extra: 额外的字段

        返回:
            包含新记录 ID 的字典
        """
        conn = self._connection()
        try:
            repo = self._repo_class(conn)
            row_id = repo.create(body.model_dump(), extra={"created_by": user_id, **extra})
            return {"id": row_id}
        finally:
            self._close_connection(conn)

    def get_by_id(self, entity_id: int) -> dict:
        """根据 ID 获取实体，不存在时返回 404。

        参数:
            entity_id: 实体 ID

        返回:
            实体字典

        抛出:
            HTTPException: 实体不存在时抛出 404
        """
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
        """更新实体记录，不存在时返回 404。

        参数:
            entity_id: 实体 ID
            body: 包含待更新字段的 Pydantic 模型

        返回:
            包含已更新 ID 的字典

        抛出:
            HTTPException: 实体不存在时抛出 404
        """
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
        """删除实体记录，不存在时返回 404。

        参数:
            entity_id: 待删除的实体 ID

        抛出:
            HTTPException: 实体不存在时抛出 404
        """
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
        """分页查询实体列表。

        参数:
            page: 页码，从 1 开始
            page_size: 每页条数
            **filters: 过滤条件

        返回:
            (实体字典列表, 总记录数) 的元组
        """
        conn = self._connection()
        try:
            repo = self._repo_class(conn)
            rows = repo.list(page=page, page_size=page_size, **filters)
            total = repo.count(**filters)
            return [dict(r) for r in rows], total
        finally:
            self._close_connection(conn)

    def paginate(self, page: int = 1, page_size: int = 20, **filters) -> dict:
        """分页查询并返回包含分页信息的字典。

        参数:
            page: 页码
            page_size: 每页条数
            **filters: 过滤条件

        返回:
            包含 items、total、page、page_size、total_pages 的字典
        """
        items, total = self.list(page=page, page_size=page_size, **filters)
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }
