"""Analysis L4 trigger — thin wrapper around the generic trigger."""

import logging

from cloud.app.agent_runtime.runtime_core import RuntimeCore
from cloud.app.agent_runtime.trigger import run_agent_trigger

logger = logging.getLogger(__name__)

AGENT_KEY = "anomaly_analysis"
GOAL = "分析红灯事件"


def analysis_monitor_trigger(runtime: RuntimeCore, red_light_event: dict) -> dict:
    return run_agent_trigger(runtime, AGENT_KEY, GOAL, red_light_event)
