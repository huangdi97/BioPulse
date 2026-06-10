"""Validate registered agent specs."""

import pytest

from cloud.app.agent_runtime.agent_specs import AGENT_SPECS

REGISTERED_AGENTS = {
    "Compliance Agent": "compliance_monitor",
    "Suggestion Agent": "sales_suggestion",
    "Analysis Agent": "anomaly_analysis",
    "Opportunity Scanner": "opportunity_scanner",
    "Knowledge Worker": "knowledge_worker",
}


@pytest.mark.parametrize("agent_name,spec_key", REGISTERED_AGENTS.items())
def test_registered_agent_config_is_complete(agent_name, spec_key):
    spec = AGENT_SPECS[spec_key]
    role = spec.get("role") or spec.get("role_desc")
    goal = spec.get("goal") or spec.get("role_desc")
    tools = spec.get("tools") or spec.get("allowed_tools")
    execution_config = spec.get("execution_config") or {
        "max_iterations": spec.get("max_iterations"),
        "max_retries": spec.get("max_retries", 0),
        "default_temperature": spec.get("default_temperature"),
        "max_permission": spec.get("max_permission"),
    }
    max_iterations = execution_config.get("max_iterations") or execution_config.get("max_steps")

    assert role, f"{agent_name} role is required"
    assert goal, f"{agent_name} goal is required"
    assert tools, f"{agent_name} tools are required"
    assert max_iterations > 0
    assert spec.get("default_temperature") is not None or execution_config.get("default_temperature") is not None or "max_steps" in execution_config
    assert spec.get("allowed_tools") or spec.get("tools")
