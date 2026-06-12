"""Analysis L4 trigger — routes red-light events through agent_runtime.execute()."""

import logging
import time
import uuid

from cloud.app.agent_runtime.agent_specs import AGENT_SPECS
from cloud.app.agent_runtime.runtime_core import RuntimeCore

logger = logging.getLogger(__name__)


def analysis_monitor_trigger(runtime: RuntimeCore, red_light_event: dict) -> dict:
    agent_key = "anomaly_analysis"
    spec = AGENT_SPECS.get(agent_key)
    if not spec:
        return {"status": "error", "result": f"unknown agent: {agent_key}"}

    enriched_context = {
        **(red_light_event or {}),
        "_trigger_source": "analysis_monitor_trigger",
        "_trace_id": str(uuid.uuid4()),
    }

    start = time.time()
    result = runtime.execute("分析红灯事件", agent_key, enriched_context)
    elapsed = time.time() - start

    logger.info(
        "Analysis L4 trigger: agent=%s status=%s elapsed=%.2fs",
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
