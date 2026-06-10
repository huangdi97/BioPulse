"""End-to-end compliance flow using in-memory mock data."""

from cloud.app.analysis import HypothesisVerifier, Narrator
from cloud.app.compliance.red_light import RedLightManager
from cloud.app.compliance.triangulation import TriangulationEngine


def test_expense_submission_to_red_light_and_root_cause_analysis():
    expense_submission = {
        "agent_id": "rep-e2e-001",
        "expense_trend": "up",
        "amount": 24000,
        "expense_visit_mismatch": True,
        "invoice_mismatch": True,
    }
    visit_snapshot = {"agent_id": "rep-e2e-001", "visit_trend": "down", "visit_count": 6}
    flow_snapshot = {"agent_id": "rep-e2e-001", "distribution_trend": "down", "sellout": 35}

    triangulation = TriangulationEngine().check(expense_submission, visit_snapshot, flow_snapshot)

    assert triangulation.decision == "trigger_red_light"
    assert any(finding.pattern == "expense_waste" for finding in triangulation.findings)

    red_light = RedLightManager().trigger(
        expense_submission["agent_id"],
        "L2",
        {
            "findings": [finding.to_dict() for finding in triangulation.findings],
            "expense_visit_mismatch": True,
            "invoice_mismatch": True,
            "expense": "费用金额与拜访、流向无法互相印证",
        },
        notify_levels=["L1", "L2", "L3"],
    )

    analysis = HypothesisVerifier().verify_anomaly(red_light.to_dict())
    narrative = Narrator().generate_narrative(analysis)

    assert red_light.status == "active"
    assert red_light.incentives_paused is True
    assert len(red_light.notifications) == 3
    assert analysis.root_cause_category == "expense_visit_mismatch"
    assert analysis.confidence >= 0.8
    assert narrative.cause.startswith("原因：")
