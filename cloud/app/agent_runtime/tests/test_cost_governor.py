"""Tests for CostGovernor."""

from cloud.app.agent_runtime.safety.cost_governor import CostGovernor


def test_init_ok():
    """test init with default and custom max_cost."""
    cg = CostGovernor()
    assert cg._max_cost == 0.50
    assert cg._total_cost == 0.0
    assert cg._call_count == 0

    cg2 = CostGovernor(max_cost=1.00)
    assert cg2._max_cost == 1.00


def test_check_cost_within_budget():
    """test check returns True when total cost stays within budget."""
    cg = CostGovernor(max_cost=0.50)
    assert cg.check("deepseek-chat", 100, 50, "cloud_normal") is True
    cg.record("deepseek-chat", 100, 50, "cloud_normal")
    assert cg.check("deepseek-chat", 100, 50, "cloud_normal") is True


def test_check_cost_exceeds_budget():
    """test check returns False when adding cost would exceed budget."""
    cg = CostGovernor(max_cost=0.0001)
    assert cg.check("deepseek-chat", 1000, 500, "cloud_normal") is False
