import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


class BaseRepository:
    def __init__(self, db: sqlite3.Connection, table_name: str, cols: List[str]):
        self.db = db
        self.table_name = table_name
        self.cols = cols
        self._is_sqlite = isinstance(self.db, sqlite3.Connection)

    def execute(self, sql: str, params=None):
        if self._is_sqlite:
            sql = sql.replace("%s", "?")
        return self.db.execute(sql, params)

    def get_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        placeholders = ", ".join(self.cols)
        query = f"SELECT {placeholders} FROM {self.table_name} WHERE id = %s"
        cursor = self.execute(query, (record_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    def get_all(self) -> List[Dict[str, Any]]:
        placeholders = ", ".join(self.cols)
        query = f"SELECT {placeholders} FROM {self.table_name}"
        cursor = self.execute(query)
        return [dict(row) for row in cursor.fetchall()]

    def create(self, data: Dict[str, Any]) -> int:
        filtered = {k: v for k, v in data.items() if k in self.cols and k != "id"}
        if not filtered:
            return 0
        cols_str = ", ".join(filtered.keys())
        placeholders = ", ".join(["%s"] * len(filtered))
        values = list(filtered.values())
        query = f"INSERT INTO {self.table_name} ({cols_str}) VALUES ({placeholders})"
        if not self._is_sqlite:
            query += " RETURNING id"
        cursor = self.execute(query, values)
        self.db.commit()
        if self._is_sqlite:
            return cursor.lastrowid
        return cursor.fetchone()[0]

    def update(self, record_id: int, data: Dict[str, Any]) -> bool:
        filtered = {k: v for k, v in data.items() if k in self.cols and k != "id"}
        if not filtered:
            return False
        set_clause = ", ".join([f"{k} = %s" for k in filtered.keys()])
        values = list(filtered.values()) + [record_id]
        query = f"UPDATE {self.table_name} SET {set_clause} WHERE id = %s"
        cursor = self.execute(query, values)
        self.db.commit()
        return cursor.rowcount > 0

    def soft_delete(self, record_id: int) -> bool:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        query = f"UPDATE {self.table_name} SET is_active=0, updated_at=%s WHERE id=%s"
        cursor = self.execute(query, (now, record_id))
        self.db.commit()
        return cursor.rowcount > 0

    def delete(self, record_id: int) -> bool:
        query = f"DELETE FROM {self.table_name} WHERE id = %s"
        cursor = self.execute(query, (record_id,))
        self.db.commit()
        return cursor.rowcount > 0

    def list_all(
        self,
        conditions: Optional[List[str]] = None,
        params: Optional[List[Any]] = None,
        order_by: str = "id DESC",
    ) -> List[Dict[str, Any]]:
        placeholders = ", ".join(self.cols)
        where = ""
        if conditions:
            where = " WHERE " + " AND ".join(conditions)
        query = f"SELECT {placeholders} FROM {self.table_name}{where} ORDER BY {order_by}"
        cursor = self.execute(query, params or [])
        return [dict(row) for row in cursor.fetchall()]

    def paginate(
        self,
        page: int = 1,
        page_size: int = 20,
        conditions: Optional[List[str]] = None,
        params: Optional[List[Any]] = None,
        order_by: str = "id DESC",
    ) -> Tuple[int, int, List[Dict[str, Any]]]:
        placeholders = ", ".join(self.cols)
        where = ""
        if conditions:
            where = " WHERE " + " AND ".join(conditions)
        total = self.execute(
            f"SELECT COUNT(*) FROM {self.table_name}{where}", params or []
        ).fetchone()[0]
        total_pages = max(1, (total + page_size - 1) // page_size)
        offset = (page - 1) * page_size
        query = f"SELECT {placeholders} FROM {self.table_name}{where} ORDER BY {order_by} LIMIT %s OFFSET %s"
        cursor = self.execute(query, (params or []) + [page_size, offset])
        return total, total_pages, [dict(row) for row in cursor.fetchall()]

    def count(
        self,
        conditions: Optional[List[str]] = None,
        params: Optional[List[Any]] = None,
    ) -> int:
        where = ""
        if conditions:
            where = " WHERE " + " AND ".join(conditions)
        return self.execute(
            f"SELECT COUNT(*) FROM {self.table_name}{where}", params or []
        ).fetchone()[0]
