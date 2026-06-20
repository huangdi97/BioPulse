"""Dynamic replanning handler — re-generates plan when agent deviates too much."""

import logging

logger = logging.getLogger(__name__)


class ReplanHandler:
    """Handles dynamic replanning when the agent deviates too far from the current plan."""

    def __init__(self, host):
        self._host = host

    def trigger(self, c) -> dict:
        """Regenerate the execution plan for the given context and update deviation counters."""
        tools_list = [t["name"] for t in self._host._tool_registry.list_tools() if t.get("name")]
        new_plan = self._host._planner.generate_plan(c["goal"], tools_list, c.get("context"))
        if new_plan and new_plan.steps:
            c["_plan"] = new_plan
            c["_plan_step_index"] = 0
            c["_plan_deviation_count"] = 0
            c["_replan_count"] = c.get("_replan_count", 0) + 1
            c["messages"].append({"role": "user", "content": "🔄 计划已更新"})
            logger.info("Replan triggered for %s (count: %d)", c["agent_key"], c["_replan_count"])
        else:
            c["_plan_deviation_count"] = 0
            logger.warning("Replan generation returned empty plan for %s", c["agent_key"])
        return c
