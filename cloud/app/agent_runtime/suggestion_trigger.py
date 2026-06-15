"""Sales Suggestion L4 trigger — thin wrapper around the generic trigger."""

import logging

from cloud.app.agent_runtime.runtime_core import RuntimeCore
from cloud.app.agent_runtime.trigger import run_agent_trigger

logger = logging.getLogger(__name__)

AGENT_KEY = "sales_suggestion"
GOAL = "生成拜访后销售策略建议"


def suggestion_monitor_trigger(runtime: RuntimeCore, visit_event: dict) -> dict:
    return run_agent_trigger(runtime, AGENT_KEY, GOAL, visit_event)
