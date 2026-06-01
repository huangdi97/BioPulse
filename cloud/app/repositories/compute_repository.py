from cloud.shared.repository import BaseRepository
from cloud.shared.columns import (
    TABLE_PRIVACY_BUDGETS_COLS,
    TABLE_PRIVACY_COMPUTE_JOBS_COLS,
    TABLE_SENSOR_SESSIONS_COLS,
    TABLE_EFFECT_METRICS_COLS,
)


class PrivacyBudgetsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "privacy_budgets", TABLE_PRIVACY_BUDGETS_COLS)


class PrivacyComputeJobsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "privacy_compute_jobs", TABLE_PRIVACY_COMPUTE_JOBS_COLS)


class SensorSessionsRepository(BaseRepository):
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
    def __init__(self, db):
        super().__init__(db, "effect_metrics", TABLE_EFFECT_METRICS_COLS)

    def dashboard(self, agent_role=None) -> list:
        where = ""
        params = []
        if agent_role:
            where = "WHERE agent_role = ?"
            params.append(agent_role)
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT agent_role, metric_type, SUM(metric_value) AS total, AVG(metric_value) AS avg_value "
            f"FROM {self.table_name} {where} GROUP BY agent_role, metric_type ORDER BY agent_role, metric_type",
            params,
        ).fetchall()
        return [dict(r) for r in rows]
