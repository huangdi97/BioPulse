"""Agent Event Bridge — Event-Driven Agent Communication (EDAC).

Connects Event Bus events to Agent execution based on agent specs' event_subscriptions.
When an event is published, this bridge checks all registered agents and triggers
any that subscribe to the event type.

Agent chain: Compliance Monitor → (red_light) → Anomaly Analysis → (insights) → Sales Suggestion
"""

from __future__ import annotations

import logging
import threading

from cloud.app.agent_runtime.agent_specs import AGENT_SPECS
from cloud.app.agent_runtime.runtime_core import RuntimeCore
from cloud.app.database import DB_PATH

logger = logging.getLogger(__name__)


# In-memory subscription map built from agent specs
# { "event_type": [("agent_key", "goal_override"), ...] }
_SUBSCRIPTIONS: dict[str, list[tuple[str, str | None]]] = {}
_LOCK = threading.Lock()


def _build_subscriptions():
    """Build event→agent mapping from all agent specs."""
    global _SUBSCRIPTIONS
    subs: dict[str, list[tuple[str, str | None]]] = {}
    for agent_key, spec in AGENT_SPECS.items():
        subscriptions = spec.get("event_subscriptions", [])
        for event_type in subscriptions:
            if event_type not in subs:
                subs[event_type] = []
            subs[event_type].append((agent_key, None))
    with _LOCK:
        _SUBSCRIPTIONS = subs
    logger.info("Agent Event Bridge: built %d event→agent mappings from %d agents", len(subs), len(AGENT_SPECS))


def get_subscribers(event_type: str) -> list[tuple[str, str | None]]:
    """Get agent keys that subscribe to a given event type."""
    with _LOCK:
        return _SUBSCRIPTIONS.get(event_type, [])


def on_event_published(event_type: str, payload: dict | None = None):
    """Called when an event is published. Triggers subscribing agents."""
    subscribers = get_subscribers(event_type)
    if not subscribers:
        return

    logger.info("EDAC: event '%s' → triggering %d agents", event_type, len(subscribers))

    for agent_key, goal_override in subscribers:
        goal = goal_override or _get_default_goal(agent_key)
        _trigger_agent_async(agent_key, goal, payload)


def _get_default_goal(agent_key: str) -> str:
    spec = AGENT_SPECS.get(agent_key, {})
    return spec.get("role_desc", f"执行 {agent_key} 的默认任务")


def _trigger_agent_async(agent_key: str, goal: str, context: dict | None = None):
    """Trigger an agent execution in a background thread."""
    import sqlite3

    def _run():
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            runtime = RuntimeCore(conn, conn, "")
            result = runtime.execute(goal, agent_key, context or {})
            logger.info(
                "EDAC: agent '%s' completed with status=%s (iterations=%d, tools=%d)",
                agent_key,
                result.status,
                result.iterations,
                result.tool_calls,
            )
        except Exception:
            logger.exception("EDAC: agent '%s' execution failed", agent_key)
        finally:
            conn.close()

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()


# Initialize on import
_build_subscriptions()
