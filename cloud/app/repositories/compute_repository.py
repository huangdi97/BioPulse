"""隐私预算、隐私计算作业、传感器会话、效果指标等数据访问层。"""

from cloud.shared.columns import (
    TABLE_EFFECT_METRICS_COLS,
    TABLE_PRIVACY_BUDGETS_COLS,
    TABLE_PRIVACY_COMPUTE_JOBS_COLS,
    TABLE_SENSOR_SESSIONS_COLS,
)
from cloud.shared.repository import BaseRepository


class PrivacyBudgetsRepository(BaseRepository):
    """隐私预算表。"""

    def __init__(self, db):
        super().__init__(db, "privacy_budgets", TABLE_PRIVACY_BUDGETS_COLS)


class PrivacyComputeJobsRepository(BaseRepository):
    """隐私计算作业表。"""

    def __init__(self, db):
        super().__init__(db, "privacy_compute_jobs", TABLE_PRIVACY_COMPUTE_JOBS_COLS)


class SensorSessionsRepository(BaseRepository):
    """传感器会话表。"""

    def __init__(self, db):
        super().__init__(db, "sensor_sessions", TABLE_SENSOR_SESSIONS_COLS)

    def get_by_session_id(self, session_id: str):
        placeholders = ", ".join(self.cols)
        row = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE session_id=?",
            (session_id,),
        ).fetchone()
        return dict(row) if row else None


class EffectMetricsRepository(BaseRepository):
    """效果指标表。"""

    def __init__(self, db):
        super().__init__(db, "effect_metrics", TABLE_EFFECT_METRICS_COLS)

    def dashboard(self, agent_role=None) -> list:
        where = ""
        params = []
        if agent_role:
            where = "WHERE agent_role = ?"
            params.append(agent_role)
        ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT agent_role, metric_type, SUM(metric_value) AS total, AVG(metric_value) AS avg_value "
            f"FROM {self.table_name} {where} GROUP BY agent_role, metric_type ORDER BY agent_role, metric_type",
            params,
        ).fetchall()
        return [dict(r) for r in rows]

    def metrics_by_dimension(
        self,
        agent_role=None,
        metric_type=None,
        period_start=None,
        period_end=None,
    ) -> list:
        conditions, params = [], []
        if agent_role:
            conditions.append("agent_role = ?")
            params.append(agent_role)
        if metric_type:
            conditions.append("metric_type = ?")
            params.append(metric_type)
        if period_start:
            conditions.append("period_start >= ?")
            params.append(period_start)
        if period_end:
            conditions.append("period_end <= ?")
            params.append(period_end)
        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name}{where} ORDER BY created_at",
            params,
        ).fetchall()
        return [dict(r) for r in rows]

    def distinct_sources(
        self,
        agent_role,
        metric_type,
        period_start=None,
        period_end=None,
    ) -> int:
        conditions = ["agent_role = ?", "metric_type = ?"]
        params = [agent_role, metric_type]
        if period_start:
            conditions.append("period_start >= ?")
            params.append(period_start)
        if period_end:
            conditions.append("period_end <= ?")
            params.append(period_end)
        where = " WHERE " + " AND ".join(conditions)
        row = self.db.execute(
            f"SELECT COUNT(DISTINCT source_row_id) AS cnt FROM {self.table_name}{where}",
            params,
        ).fetchone()
        return int(row["cnt"]) if row else 0

    def all_dimension_groups(self, period_start=None, period_end=None) -> list:
        conditions, params = [], []
        if period_start:
            conditions.append("period_start >= ?")
            params.append(period_start)
        if period_end:
            conditions.append("period_end <= ?")
            params.append(period_end)
        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        rows = self.db.execute(
            f"SELECT DISTINCT agent_role, metric_type FROM {self.table_name}{where} ORDER BY agent_role, metric_type",
            params,
        ).fetchall()
        return [dict(r) for r in rows]

    def user_metrics(
        self,
        source_sub: str,
        agent_role=None,
        period_start=None,
        period_end=None,
    ) -> list:
        conditions = ["source_sub = ?"]
        params = [source_sub]
        if agent_role:
            conditions.append("agent_role = ?")
            params.append(agent_role)
        if period_start:
            conditions.append("period_start >= ?")
            params.append(period_start)
        if period_end:
            conditions.append("period_end <= ?")
            params.append(period_end)
        where = " WHERE " + " AND ".join(conditions)
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name}{where} ORDER BY period_start",
            params,
        ).fetchall()
        return [dict(r) for r in rows]
