"""服务层基类——供各子项目继承使用。"""

import sqlite3


class BaseService:
    """服务基类，支持两种数据库连接模式：

    - sqlite3 直连：通过 `_connection(db_path)` 打开并返回连接
    - FastAPI 依赖注入：通过 `__init__(db=...)` 注入连接后，`self.db` 可用
    """

    def __init__(self, db=None):
        if db is not None:
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
        raise NotImplementedError("Override _connection() or pass db to __init__")
