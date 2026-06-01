from cloud.shared.repository import BaseRepository
from cloud.shared.columns import (
    TABLE_ROUTE_RULES_COLS,
    TABLE_ROUTE_LOGS_COLS,
    TABLE_ROUTE_STATS_COLS,
)


class RouteRulesRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "route_rules", TABLE_ROUTE_RULES_COLS)

    def list_active_ordered(self):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE is_active=1 ORDER BY priority ASC"
        ).fetchall()
        return [dict(r) for r in rows]

    def list_all_ordered(self):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} ORDER BY priority ASC"
        ).fetchall()
        return [dict(r) for r in rows]


class RouteLogsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "route_logs", TABLE_ROUTE_LOGS_COLS)

    def list_filtered(
        self,
        role_id=None,
        source=None,
        date_from=None,
        date_to=None,
        page=1,
        page_size=20,
    ):
        conditions, params = [], []
        if role_id is not None:
            conditions.append("assigned_role_id=?")
            params.append(role_id)
        if source is not None:
            conditions.append("source=?")
            params.append(source)
        if date_from:
            conditions.append("created_at>=?")
            params.append(date_from)
        if date_to:
            conditions.append("created_at<=?")
            params.append(date_to)
        return self.paginate(
            page=page,
            page_size=page_size,
            conditions=conditions or None,
            params=params or None,
            order_by="created_at DESC",
        )

    def role_distribution(self):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT assigned_role_id, assigned_role_name, COUNT(*) as cnt "
            f"FROM {self.table_name} GROUP BY assigned_role_id, assigned_role_name ORDER BY cnt DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def avg_latency(self):
        return self.db.execute(
            f"SELECT COALESCE(AVG(latency_ms), 0) FROM {self.table_name}"
        ).fetchone()[0]

    def list_recent(self, limit: int = 10):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


class RouteStatsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "route_stats", TABLE_ROUTE_STATS_COLS)

    def upsert(self, role_id: int, latency_ms: int, tokens: int, confidence: float):
        from datetime import datetime

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row = self.db.execute(
            f"SELECT * FROM {self.table_name} WHERE role_id=?", (role_id,)
        ).fetchone()
        if row:
            total = row["total_routed"] + 1
            n = float(total)
            avg_confidence = round(
                (row["avg_confidence"] * (n - 1) + confidence) / n, 4
            )
            avg_tokens = round((row["avg_tokens"] * (n - 1) + tokens) / n, 2)
            avg_latency = round((row["avg_latency_ms"] * (n - 1) + latency_ms) / n, 2)
            self.db.execute(
                f"UPDATE {self.table_name} SET total_routed=?, avg_confidence=?, "
                "avg_tokens=?, avg_latency_ms=?, last_routed_at=?, updated_at=? WHERE role_id=?",
                (total, avg_confidence, avg_tokens, avg_latency, now, now, role_id),
            )
        else:
            self.db.execute(
                f"INSERT INTO {self.table_name} (role_id, total_routed, avg_confidence, "
                "avg_tokens, avg_latency_ms, last_routed_at, updated_at) VALUES (?,1,?,?,?,?,?)",
                (
                    role_id,
                    round(confidence, 4),
                    round(float(tokens), 2),
                    round(float(latency_ms), 2),
                    now,
                    now,
                ),
            )
        self.db.commit()

    def list_with_role_name(self):
        placeholders = ", ".join(f"rs.{c}" for c in self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders}, ar.name as role_name FROM {self.table_name} rs "
            "LEFT JOIN agent_roles ar ON rs.role_id=ar.id ORDER BY rs.total_routed DESC"
        ).fetchall()
        return [dict(r) for r in rows]
