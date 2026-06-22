"""Agent Event Bridge — Event-Driven Agent Communication (EDAC)."""

import glob
import logging
import os
import threading

import yaml

from cloud.app.agent_runtime.core.agent_specs import AGENT_SPECS
from cloud.app.agent_runtime.core.runtime_core import RuntimeCore
from cloud.app.database import DB_PATH

_SUBSCRIPTIONS: dict[str, list[tuple[str, str | None]]] = {}
_LOCK = threading.Lock()
logger = logging.getLogger(__name__)


def _build_subscriptions():
    """从 agents/*/identity.yaml 中提取所有 event_subscriptions → agent mapping"""
    subs: dict[str, list[tuple[str, str | None]]] = {}
    agents_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "agents")
    for yaml_path in glob.glob(os.path.join(agents_dir, "*", "identity.yaml")):
        with open(yaml_path) as f:
            identity = yaml.safe_load(f)
        agent_key = identity.get("key") if identity else None
        if not agent_key:
            continue
        for event_type in identity.get("event_subscriptions", []):
            subs.setdefault(event_type, []).append((agent_key, None))
    with _LOCK:
        _SUBSCRIPTIONS.clear()
        _SUBSCRIPTIONS.update(subs)
    logger.info("EDAC built %d event mappings from agents/*/identity.yaml", len(subs))


def on_event_published(event_type: str, payload: dict | None = None):
    """事件发布时触发订阅了该事件的 Agent。"""
    with _LOCK:
        subscribers = list(_SUBSCRIPTIONS.get(event_type, []))
    if not subscribers:
        return
    logger.info("EDAC event=%s → %d agents", event_type, len(subscribers))
    for agent_key, _ in subscribers:
        spec = AGENT_SPECS.get(agent_key, {})
        goal = spec.get("role_desc", f"执行 {agent_key} 的默认任务")
        _trigger_async(agent_key, goal, payload)


def _trigger_async(agent_key: str, goal: str, context: dict | None = None):
    """后台线程异步触发 Agent 执行。"""

    def _run():
        import sqlite3

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            runtime = RuntimeCore(conn, conn, "", agent_key)
            result = runtime.execute(goal, agent_key, context or {})
            logger.info("EDAC agent=%s status=%s", agent_key, result.status)
        except Exception:  # noqa: BLE001  # agent 执行可能抛出任意异常
            logger.exception("EDAC agent=%s failed", agent_key)
        finally:
            conn.close()

    threading.Thread(target=_run, daemon=True).start()


_build_subscriptions()
