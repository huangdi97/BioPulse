import threading
import time
from datetime import datetime, timedelta

from cloud.app.agent_runtime.agent_specs import AGENT_SPECS
from cloud.app.agent_runtime.models import RuntimeResult
from cloud.app.agent_runtime.queue_manager import AgentQueueManager
from cloud.app.agent_runtime.runtime_core import AgentRuntime


class AgentScheduler:
    def __init__(self, db, runtime_factory=None):
        self._db = db
        self._runtime_factory = runtime_factory
        self._queue = AgentQueueManager(db)
        self._running = False
        self._thread = None

    def start(self):
        self._queue.recover()
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        for key, spec in AGENT_SPECS.items():
            if spec.get("trigger_cron"):
                self.schedule_agent(key, 3600, f"执行 {spec['role_desc']}")

    def stop(self):
        self._running = False

    def schedule_agent(self, agent_key: str, interval_seconds: int, goal: str):
        scheduled_at = (datetime.now() + timedelta(seconds=interval_seconds)).isoformat()
        self._queue.enqueue(agent_key, goal, scheduled_at)

    def trigger_now(self, agent_key: str, goal: str, auth_header: str) -> RuntimeResult:
        runtime = self._runtime_factory() if self._runtime_factory else AgentRuntime(self._db, auth_header)
        return runtime.execute(goal, agent_key)

    def _run_loop(self):
        while self._running:
            try:
                task = self._queue.dequeue()
                if task is not None:
                    auth_header = ""
                    runtime = self._runtime_factory() if self._runtime_factory else AgentRuntime(self._db, auth_header)
                    result = runtime.execute(task["goal"], task["agent_key"])
                    if result.status == "completed":
                        self._queue.complete(task["id"], result.result)
                    else:
                        self._queue.fail(task["id"], result.result)
            except Exception as e:
                if task:
                    self._queue.fail(task["id"], str(e))
            time.sleep(30)
