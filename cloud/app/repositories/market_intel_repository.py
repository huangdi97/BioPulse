from cloud.shared.columns import (
    TABLE_MARKET_INTEL_ITEMS_COLS,
    TABLE_MARKET_INTEL_SOURCES_COLS,
    TABLE_MCP_TOOLS_COLS,
)
from cloud.shared.repository import BaseRepository


class MarketIntelItemsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "market_intel_items", TABLE_MARKET_INTEL_ITEMS_COLS)

    def count_by_field(self, field: str) -> dict:
        if field not in self.cols:
            return {}
        ", ".join(self.cols)
        rows = self.db.execute(f"SELECT {field}, COUNT(*) as cnt FROM {self.table_name} GROUP BY {field}").fetchall()
        return {r[field]: r["cnt"] for r in rows}

    def count_recent_critical(self, limit: int = 10) -> list:
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE impact_level='critical' ORDER BY collected_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    def count_by_date_range(self, days: int = 7) -> list:
        from datetime import datetime, timedelta

        result = []
        ", ".join(self.cols)
        for i in range(days, -1, -1):
            day = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            cnt = self.db.execute(
                f"SELECT COUNT(*) FROM {self.table_name} WHERE date(collected_at)=?",
                (day,),
            ).fetchone()[0]
            result.append({"date": day, "count": cnt})
        return result

    def list_with_source(
        self,
        conditions=None,
        params=None,
        order_by="mi.collected_at DESC",
        page=1,
        page_size=20,
    ):
        placeholders = ", ".join(f"mi.{c}" for c in self.cols)
        where = ""
        if conditions:
            where = " WHERE " + " AND ".join(conditions)
        total = self.db.execute(f"SELECT COUNT(*) FROM {self.table_name} mi{where}", params or []).fetchone()[0]
        offset = (page - 1) * page_size
        rows = self.db.execute(
            f"SELECT {placeholders}, ms.name as source_name FROM {self.table_name} mi "
            f"LEFT JOIN market_intel_sources ms ON mi.source_id=ms.id"
            f"{where} ORDER BY {order_by} LIMIT ? OFFSET ?",
            (params or []) + [page_size, offset],
        ).fetchall()
        return total, [dict(r) for r in rows]

    def create_raw(self, data: dict) -> int:
        filtered = {k: v for k, v in data.items() if k in self.cols}
        if not filtered:
            return 0
        cols_str = ", ".join(filtered.keys())
        placeholders = ", ".join(["?"] * len(filtered))
        values = list(filtered.values())
        cursor = self.db.execute(
            f"INSERT INTO {self.table_name} ({cols_str}) VALUES ({placeholders})",
            values,
        )
        return cursor.lastrowid

    def delete_by_source(self, source_id: int):
        self.db.execute(f"DELETE FROM {self.table_name} WHERE source_id=?", (source_id,))

    def update_fields(self, record_id: int, data: dict) -> bool:
        filtered = {k: v for k, v in data.items() if k in self.cols and k != "id"}
        if not filtered:
            return False
        set_clause = ", ".join(f"{k}=?" for k in filtered.keys())
        values = list(filtered.values()) + [record_id]
        cursor = self.db.execute(f"UPDATE {self.table_name} SET {set_clause} WHERE id=?", values)
        return cursor.rowcount > 0


class MarketIntelSourcesRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "market_intel_sources", TABLE_MARKET_INTEL_SOURCES_COLS)

    def update_fields(self, record_id: int, data: dict) -> bool:
        filtered = {k: v for k, v in data.items() if k in self.cols and k != "id"}
        if not filtered:
            return False
        set_clause = ", ".join(f"{k}=?" for k in filtered.keys())
        values = list(filtered.values()) + [record_id]
        cursor = self.db.execute(f"UPDATE {self.table_name} SET {set_clause} WHERE id=?", values)
        self.db.commit()
        return cursor.rowcount > 0

    def list_active(self) -> list:
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(f"SELECT {placeholders} FROM {self.table_name} WHERE is_active=1").fetchall()
        return [dict(r) for r in rows]

    def count_active(self) -> int:
        return self.db.execute(f"SELECT COUNT(*) FROM {self.table_name} WHERE is_active=1").fetchone()[0]


class McpToolsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "mcp_tools", TABLE_MCP_TOOLS_COLS)

    def list_filtered(self, enabled=None) -> list:
        placeholders = ", ".join(self.cols)
        conditions, params = [], []
        if enabled is not None:
            conditions.append("enabled=?")
            params.append(enabled)
        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name}{where} ORDER BY created_at DESC",
            params,
        ).fetchall()
        return [dict(r) for r in rows]

    def toggle_enabled(self, record_id: int) -> bool:
        from datetime import datetime

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor = self.db.execute(
            f"UPDATE {self.table_name} SET enabled = NOT enabled, updated_at=? WHERE id=?",
            (now, record_id),
        )
        self.db.commit()
        return cursor.rowcount > 0

    def get_by_tool_name(self, tool_name: str):
        placeholders = ", ".join(self.cols)
        row = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE tool_name=?",
            (tool_name,),
        ).fetchone()
        return dict(row) if row else None
