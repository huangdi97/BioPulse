from datetime import datetime

from cloud.shared.repository import BaseRepository
from cloud.shared.columns import (
    TABLE_MDT_SESSIONS_COLS,
    TABLE_MDT_PARTICIPANTS_COLS,
    TABLE_MDT_OPINIONS_COLS,
    TABLE_ASYNC_MDT_OPINIONS_COLS,
    TABLE_SOAP_DECISIONS_COLS,
    TABLE_SOAP_TEMPLATES_COLS,
    TABLE_DECISION_CASES_COLS,
    TABLE_CAUSAL_ANALYSES_COLS,
    TABLE_CAUSAL_GRAPHS_COLS,
    TABLE_COUNTERFACTUAL_SCENARIOS_COLS,
    TABLE_CROSS_CASE_INSIGHTS_COLS,
    TABLE_COLLABORATION_SESSIONS_COLS,
    TABLE_COLLABORATION_STEPS_COLS,
)


class MdtSessionsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "mdt_sessions", TABLE_MDT_SESSIONS_COLS)

    def count_by_field(self, field: str) -> dict:
        rows = self.db.execute(
            f"SELECT {field}, COUNT(*) as cnt FROM {self.table_name} GROUP BY {field}"
        ).fetchall()
        return {r[field]: r["cnt"] for r in rows}

    def count_completed(self) -> int:
        return self.db.execute(
            f"SELECT COUNT(*) FROM {self.table_name} WHERE status='completed'"
        ).fetchone()[0]

    def avg_field(self, field: str) -> float:
        return self.db.execute(
            f"SELECT COALESCE(ROUND(AVG({field}),2),0) FROM {self.table_name}"
        ).fetchone()[0]

    def list_recent(self, limit: int = 5) -> list:
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


class MdtParticipantsRepository(BaseRepository):
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
        return self.db.execute(
            "SELECT COALESCE(ROUND(AVG(c),2),0) FROM "
            f"(SELECT COUNT(*) c FROM {self.table_name} GROUP BY session_id)"
        ).fetchone()[0]

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
        return self.db.execute(
            f"SELECT COALESCE(ROUND(AVG(confidence),2),0) FROM {self.table_name}"
        ).fetchone()[0]

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
        return "\n".join(
            f"- {r['role_name']}: {r['summary']}" for r in rows if r.get("summary")
        )

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


class SoapDecisionsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "soap_decisions", TABLE_SOAP_DECISIONS_COLS)

    def list_active_filtered(
        self, status=None, priority=None, tag=None, page=1, page_size=20
    ):
        conditions = ["is_active=1"]
        params = []
        if status:
            conditions.append("status=?")
            params.append(status)
        if priority:
            conditions.append("priority=?")
            params.append(priority)
        if tag:
            conditions.append("tags LIKE ?")
            params.append(f"%{tag}%")
        return self.paginate(
            page=page,
            page_size=page_size,
            conditions=conditions,
            params=params or None,
            order_by="created_at DESC",
        )

    def count_active(self):
        return self.db.execute(
            f"SELECT COUNT(*) FROM {self.table_name} WHERE is_active=1"
        ).fetchone()[0]

    def count_by_status(self):
        rows = self.db.execute(
            f"SELECT status, COUNT(*) cnt FROM {self.table_name} WHERE is_active=1 GROUP BY status"
        ).fetchall()
        return {r["status"]: r["cnt"] for r in rows}

    def count_by_priority(self):
        rows = self.db.execute(
            f"SELECT priority, COUNT(*) cnt FROM {self.table_name} WHERE is_active=1 GROUP BY priority"
        ).fetchall()
        return {r["priority"]: r["cnt"] for r in rows}

    def list_active_recent(self, limit: int = 5):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE is_active=1 "
            "ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


class SoapTemplatesRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "soap_templates", TABLE_SOAP_TEMPLATES_COLS)

    def list_active(self, category=None):
        conditions = ["is_active=1"]
        params = []
        if category:
            conditions.append("category=?")
            params.append(category)
        return self.list_all(
            conditions=conditions, params=params or None, order_by="id ASC"
        )


class DecisionCasesRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "decision_cases", TABLE_DECISION_CASES_COLS)

    def get_active_by_id(self, case_id: int):
        placeholders = ", ".join(self.cols)
        row = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE id=? AND is_active=1",
            (case_id,),
        ).fetchone()
        return dict(row) if row else None

    def list_filtered(
        self,
        outcome_score_min=None,
        outcome_score_max=None,
        tag=None,
        search=None,
        page=1,
        page_size=20,
    ):
        conditions = ["is_active=1"]
        params = []
        if outcome_score_min is not None:
            conditions.append("outcome_score >= ?")
            params.append(outcome_score_min)
        if outcome_score_max is not None:
            conditions.append("outcome_score <= ?")
            params.append(outcome_score_max)
        if tag:
            conditions.append("tags LIKE ?")
            params.append(f"%{tag}%")
        if search:
            conditions.append("(name LIKE ? OR description LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%"])
        return self.paginate(
            page=page,
            page_size=page_size,
            conditions=conditions,
            params=params or None,
            order_by="created_at DESC",
        )

    def soft_delete_with_causal(self, case_id: int):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.db.execute(
            f"UPDATE {self.table_name} SET is_active=0, updated_at=? WHERE id=?",
            (now, case_id),
        )
        self.db.execute(
            "UPDATE causal_analyses SET case_id=-case_id WHERE case_id=?", (case_id,)
        )
        self.db.commit()

    def list_success_cases(self, limit=5, filter_tags=None):
        conditions = ["is_active=1", "outcome_score >= 0.5"]
        params = []
        if filter_tags:
            tc = " OR ".join(["tags LIKE ?"] * len(filter_tags))
            conditions.append(f"({tc})")
            params = [f"%{t}%" for t in filter_tags]
        placeholders = ", ".join(self.cols)
        where = " WHERE " + " AND ".join(conditions)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name}{where} ORDER BY outcome_score DESC LIMIT ?",
            params + [limit],
        ).fetchall()
        return [dict(r) for r in rows]

    def list_fail_cases(self, limit=5, filter_tags=None):
        conditions = ["is_active=1", "outcome_score <= -0.5"]
        params = []
        if filter_tags:
            tc = " OR ".join(["tags LIKE ?"] * len(filter_tags))
            conditions.append(f"({tc})")
            params = [f"%{t}%" for t in filter_tags]
        placeholders = ", ".join(self.cols)
        where = " WHERE " + " AND ".join(conditions)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name}{where} ORDER BY outcome_score ASC LIMIT ?",
            params + [limit],
        ).fetchall()
        return [dict(r) for r in rows]

    def count_active(self):
        return self.db.execute(
            f"SELECT COUNT(*) FROM {self.table_name} WHERE is_active=1"
        ).fetchone()[0]

    def score_distribution(self):
        rows = self.db.execute(
            "SELECT CASE WHEN outcome_score <= -0.5 THEN 'fail(<=-0.5)' "
            "WHEN outcome_score < 0 THEN 'negative(-0.5~0)' WHEN outcome_score = 0 THEN 'neutral(0)' "
            "WHEN outcome_score < 0.5 THEN 'positive(0~0.5)' ELSE 'success(>=0.5)' END AS bucket, "
            "COUNT(*) AS cnt FROM decision_cases WHERE is_active=1 GROUP BY bucket ORDER BY bucket"
        ).fetchall()
        return [{"bucket": r["bucket"], "count": r["cnt"]} for r in rows]


class CausalAnalysesRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "causal_analyses", TABLE_CAUSAL_ANALYSES_COLS)

    def list_by_case_id(self, case_id: int):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE case_id=? ORDER BY created_at DESC",
            (case_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def count_distinct_case_ids(self):
        return self.db.execute(
            "SELECT COUNT(DISTINCT case_id) FROM causal_analyses ca "
            "JOIN decision_cases dc ON ca.case_id=dc.id WHERE dc.is_active=1"
        ).fetchone()[0]


class CausalGraphsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "causal_graphs", TABLE_CAUSAL_GRAPHS_COLS)


class CounterfactualScenariosRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(
            db, "counterfactual_scenarios", TABLE_COUNTERFACTUAL_SCENARIOS_COLS
        )


class CrossCaseInsightsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "cross_case_insights", TABLE_CROSS_CASE_INSIGHTS_COLS)

    def list_filtered(
        self, insight_type=None, confidence_min=None, page=1, page_size=20
    ):
        conditions = ["is_active=1"]
        params = []
        if insight_type:
            conditions.append("insight_type=?")
            params.append(insight_type)
        if confidence_min is not None:
            conditions.append("confidence >= ?")
            params.append(confidence_min)
        return self.paginate(
            page=page,
            page_size=page_size,
            conditions=conditions,
            params=params or None,
            order_by="confidence DESC",
        )

    def get_active_by_id(self, insight_id: int):
        placeholders = ", ".join(self.cols)
        row = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE id=? AND is_active=1",
            (insight_id,),
        ).fetchone()
        return dict(row) if row else None

    def count_by_type(self):
        rows = self.db.execute(
            f"SELECT insight_type, COUNT(*) AS cnt FROM {self.table_name} WHERE is_active=1 "
            "GROUP BY insight_type"
        ).fetchall()
        return [{"type": r["insight_type"], "count": r["cnt"]} for r in rows]

    def top_by_confidence(self, limit=5):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE is_active=1 ORDER BY confidence DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


class CollaborationSessionsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(
            db, "collaboration_sessions", TABLE_COLLABORATION_SESSIONS_COLS
        )


class CollaborationStepsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "collaboration_steps", TABLE_COLLABORATION_STEPS_COLS)
