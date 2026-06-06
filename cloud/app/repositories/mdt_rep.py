"""MDT会话、参与者、意见、异步意见等数据访问层。"""

from cloud.shared.columns import (
    TABLE_ASYNC_MDT_OPINIONS_COLS,
    TABLE_MDT_OPINIONS_COLS,
    TABLE_MDT_PARTICIPANTS_COLS,
    TABLE_MDT_SESSIONS_COLS,
)
from cloud.shared.repository import BaseRepository


class MdtSessionsRepository(BaseRepository):
    """MDT会话表。"""

    def __init__(self, db):
        super().__init__(db, "mdt_sessions", TABLE_MDT_SESSIONS_COLS)

    def count_by_field(self, field: str) -> dict:
        rows = self.db.execute(f"SELECT {field}, COUNT(*) as cnt FROM {self.table_name} GROUP BY {field}").fetchall()
        return {r[field]: r["cnt"] for r in rows}

    def count_completed(self) -> int:
        return self.db.execute(f"SELECT COUNT(*) FROM {self.table_name} WHERE status='completed'").fetchone()[0]

    def avg_field(self, field: str) -> float:
        return self.db.execute(f"SELECT COALESCE(ROUND(AVG({field}),2),0) FROM {self.table_name}").fetchone()[0]

    def list_recent(self, limit: int = 5) -> list:
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


class MdtParticipantsRepository(BaseRepository):
    """MDT参与者表。"""

    def __init__(self, db):
        super().__init__(db, "mdt_participants", TABLE_MDT_PARTICIPANTS_COLS)

    def list_by_session(self, session_id: int) -> list:
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE session_id=? ORDER BY id ASC",
            (session_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def avg_per_session(self) -> float:
        return self.db.execute(f"SELECT COALESCE(ROUND(AVG(c),2),0) FROM (SELECT COUNT(*) c FROM {self.table_name} GROUP BY session_id)").fetchone()[
            0
        ]

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


class MdtOpinionsRepository(BaseRepository):
    """MDT意见表。"""

    def __init__(self, db):
        super().__init__(db, "mdt_opinions", TABLE_MDT_OPINIONS_COLS)

    def list_by_session(self, session_id: int, round_number=None) -> list:
        conditions = ["session_id=?"]
        params = [session_id]
        if round_number is not None:
            conditions.append("round_number=?")
            params.append(round_number)
        placeholders = ", ".join(self.cols)
        where = "WHERE " + " AND ".join(conditions)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name}{where} ORDER BY round_number ASC, id ASC",
            params,
        ).fetchall()
        return [dict(r) for r in rows]

    def list_by_session_with_participant(self, session_id: int) -> list:
        placeholders = ", ".join(f"o.{c}" for c in self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders}, p.role_name, p.stance FROM {self.table_name} o "
            f"JOIN mdt_participants p ON p.id=o.participant_id "
            f"WHERE o.session_id=? ORDER BY o.round_number ASC, o.id ASC",
            (session_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def avg_confidence(self) -> float:
        return self.db.execute(f"SELECT COALESCE(ROUND(AVG(confidence),2),0) FROM {self.table_name}").fetchone()[0]

    def build_round_summary(self, session_id: int, round_num: int) -> str:
        if round_num < 1:
            return ""
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders}, p.role_name FROM {self.table_name} o "
            f"JOIN mdt_participants p ON p.id=o.participant_id "
            f"WHERE o.session_id=? AND o.round_number=?",
            (session_id, round_num),
        ).fetchall()
        return "\n".join(f"- {r['role_name']}: {r['summary']}" for r in rows if r.get("summary"))

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


class AsyncMdtOpinionsRepository(BaseRepository):
    """异步MDT意见表。"""

    def __init__(self, db):
        super().__init__(db, "async_mdt_opinions", TABLE_ASYNC_MDT_OPINIONS_COLS)

    def list_by_decision(self, decision_id: int):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE decision_id=? ORDER BY created_at ASC",
            (decision_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def count_all(self):
        return self.db.execute(f"SELECT COUNT(*) FROM {self.table_name}").fetchone()[0]
