"""运行时热加载 Agent prompt 变更。"""

import json
import logging
import threading
import time

from cloud.app.agent_runtime.agent_specs import AGENT_SPECS

logger = logging.getLogger(__name__)


class PromptHotReloader:
    """运行时热加载 Agent prompt 变更。"""

    def __init__(self, db, watch_interval: int = 30):
        self._db = db
        self._watch_interval = watch_interval
        self._cache: dict[str, dict] = dict(AGENT_SPECS)
        self._last_check: dict[str, str] = {}
        self._watcher_thread = None
        self._running = False

    def get_spec(self, agent_name: str) -> dict:
        cached = self._cache.get(agent_name)
        if cached:
            return cached
        spec = dict(AGENT_SPECS.get(agent_name, {}))
        self._cache[agent_name] = spec
        return spec

    def _load_from_db(self, agent_name: str) -> dict | None:
        try:
            row = self._db.execute(
                "SELECT content FROM prompt_versions WHERE agent_name=? AND status='approved' ORDER BY version_id DESC LIMIT 1",
                (agent_name,),
            ).fetchone()
            if row:
                content = json.loads(row["content"]) if isinstance(row["content"], str) else row["content"]
                if isinstance(content, dict):
                    return content
            return None
        except Exception:
            logger.exception("Failed to load prompt version from DB for %s", agent_name)
            return None

    def reload(self, agent_name: str = None):
        if agent_name:
            db_spec = self._load_from_db(agent_name)
            if db_spec:
                self._cache[agent_name] = {**AGENT_SPECS.get(agent_name, {}), **db_spec}
                logger.info("Hot-reloaded prompt for agent: %s", agent_name)
            else:
                self._cache[agent_name] = dict(AGENT_SPECS.get(agent_name, {}))
        else:
            for name in AGENT_SPECS:
                self.reload(name)

    def start_watching(self):
        if self._running:
            return
        self._running = True
        self._watcher_thread = threading.Thread(target=self._watch_loop, daemon=True)
        self._watcher_thread.start()
        logger.info("Prompt hot-reload watcher started (interval=%ds)", self._watch_interval)

    def stop_watching(self):
        self._running = False

    def _watch_loop(self):
        while self._running:
            try:
                for agent_name in AGENT_SPECS:
                    row = self._db.execute(
                        "SELECT MAX(version_id) as latest FROM prompt_versions WHERE agent_name=? AND status='approved'",
                        (agent_name,),
                    ).fetchone()
                    if row:
                        latest_id = str(row["latest"])
                        if self._last_check.get(agent_name) != latest_id:
                            self.reload(agent_name)
                            self._last_check[agent_name] = latest_id
            except Exception:
                logger.exception("Error in prompt hot-reload watcher")
            time.sleep(self._watch_interval)
