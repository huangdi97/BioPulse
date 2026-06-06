"""服务层基类模块。"""

import sqlite3

from sales_coach.app.database import DB_PATH


class BaseService:
    """服务基类，每个方法独立管理数据库连接。"""

    def _connection(self):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn
