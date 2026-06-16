"""Generic L4 agent trigger — parameterized by agent_key and goal."""

import logging
import time
import uuid

from cloud.app.agent_runtime.agent_specs import AGENT_SPECS
from cloud.app.agent_runtime.runtime_core import RuntimeCore

logger = logging.getLogger(__name__)


def run_agent_trigger(
    runtime: RuntimeCore,
    agent_key: str,
    goal: str,
    event: dict | None = None,
    context_extras: dict | None = None,
) -> dict:
    """run agent trigger."""
    """通用 agent trigger：按 agent_key 查找 spec，用 goal 作为 execute 的 task，返回执行结果。

    Args:
        runtime: RuntimeCore 实例
        agent_key: agent 的 key，用于从 AGENT_SPECS 查找
        goal: 执行的 task 描述
        event: 触发事件数据
        context_extras: 额外的 context 字段（如 _plan）
    """
    spec = AGENT_SPECS.get(agent_key)
    if not spec:
        return {"status": "error", "result": f"unknown agent: {agent_key}"}

    enriched_context = {
        **(event or {}),
        **(context_extras or {}),
        "_trigger_source": f"{agent_key}_trigger",
        "_trace_id": str(uuid.uuid4()),
    }

    start = time.time()
    result = runtime.execute(goal, agent_key, enriched_context)
    elapsed = time.time() - start

    logger.info(
        "L4 trigger: agent=%s status=%s elapsed=%.2fs",
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
