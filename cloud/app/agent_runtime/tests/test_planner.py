from cloud.app.agent_runtime.planner import Plan, PlanGenerator, PlanStep


def test_validate_plan_valid():
    """test validate plan valid."""
    plan = Plan(goal="test", steps=[PlanStep(step_id="s1", description="step1", tool="tool", dependencies=[])], max_steps=5, plan_confidence=0.8)
    assert PlanGenerator().validate_plan(plan) is True
