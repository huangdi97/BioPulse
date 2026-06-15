"""Sales Suggestion L4 trigger — routes visit completion events through agent_runtime.execute()."""

import logging
import time
import uuid

from cloud.app.agent_runtime.agent_specs import AGENT_SPECS
from cloud.app.agent_runtime.runtime_core import RuntimeCore

logger = logging.getLogger(__name__)


def suggestion_monitor_trigger(runtime: RuntimeCore, visit_event: dict) -> dict:
    agent_key = "sales_suggestion"
    spec = AGENT_SPECS.get(agent_key)
    if not spec:
        return {"status": "error", "result": f"unknown agent: {agent_key}"}

    enriched_context = {
        **(visit_event or {}),
        "_trigger_source": "suggestion_monitor_trigger",
        "_trace_id": str(uuid.uuid4()),
    }

    start = time.time()
    result = runtime.execute("生成拜访后销售策略建议", agent_key, enriched_context)
    elapsed = time.time() - start

    logger.info(
        "Suggestion L4 trigger: agent=%s status=%s elapsed=%.2fs",
        agent_key,
        result.status,
        elapsed,
    )

    return {
        "status": result.status,
        "result": result.result,
        "iterations": result.iterations,
        "tool_calls": result.tool_calls,
        "logs": result.logs,
        "elapsed_seconds": round(elapsed, 3),
        "metadata": result.metadata,
    }
