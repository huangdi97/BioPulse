from datetime import datetime, timezone
from threading import Lock
from typing import Literal

AgentStatus = Literal["healthy", "degraded", "stale"]


class AgentHealthRecord:
    last_run_at: str = ""
    last_success_at: str = ""
    total_runs: int = 0
    success_count: int = 0
    fail_count: int = 0
    last_error: str = ""
    status: AgentStatus = "healthy"


class HealthTracker:
    def __init__(self):
        self._records: dict[str, AgentHealthRecord] = {}
        self._lock = Lock()

    def _get_or_create(self, agent_name: str) -> AgentHealthRecord:
        if agent_name not in self._records:
            self._records[agent_name] = AgentHealthRecord()
        return self._records[agent_name]

    def record_run(self, agent_name: str, success: bool, error: str = ""):
        with self._lock:
            record = self._get_or_create(agent_name)
            now = datetime.now(timezone.utc).isoformat()
            record.last_run_at = now
            record.total_runs += 1
            if success:
                record.last_success_at = now
                record.success_count += 1
            else:
                record.fail_count += 1
                if error:
                    record.last_error = error
            self._update_status(record)

    @staticmethod
    def _update_status(record: AgentHealthRecord):
        if record.total_runs == 0:
            record.status = "healthy"
            return
        fail_rate = record.fail_count / record.total_runs
        if fail_rate > 0.5 and record.total_runs >= 5:
            record.status = "degraded"
        elif fail_rate > 0.8:
            record.status = "degraded"
        else:
            record.status = "healthy"

    def mark_stale(self, agent_name: str):
        with self._lock:
            record = self._get_or_create(agent_name)
            record.status = "stale"

    def get_health(self, agent_name: str) -> dict:
        with self._lock:
            record = self._get_or_create(agent_name)
            return {
                "agent_name": agent_name,
                "status": record.status,
                "last_run_at": record.last_run_at,
                "last_success_at": record.last_success_at,
                "total_runs": record.total_runs,
                "success_count": record.success_count,
                "fail_count": record.fail_count,
                "last_error": record.last_error,
            }

    def get_all_health(self) -> list[dict]:
        with self._lock:
            return [self.get_health(name) for name in self._records]

    def get_summary(self) -> dict:
        with self._lock:
            total = len(self._records)
            healthy = sum(1 for r in self._records.values() if r.status == "healthy")
            degraded = sum(1 for r in self._records.values() if r.status == "degraded")
            stale = sum(1 for r in self._records.values() if r.status == "stale")
            return {
                "total_agents": total,
                "healthy": healthy,
                "degraded": degraded,
                "stale": stale,
            }


_health_tracker: HealthTracker | None = None
_tracker_lock = Lock()


def get_health_tracker() -> HealthTracker:
    global _health_tracker
    if _health_tracker is None:
        with _tracker_lock:
            if _health_tracker is None:
                _health_tracker = HealthTracker()
    return _health_tracker
