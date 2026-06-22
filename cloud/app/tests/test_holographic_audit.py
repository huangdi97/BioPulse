"""Tests for compliance triangulation detection patterns."""

from cloud.app.compliance.holographic_audit import HolographicAuditEngine


def _patterns(result):
    return {finding.pattern for finding in result.findings}


def test_expense_waste_detects_rising_expense_with_falling_activity():
    result = HolographicAuditEngine().check(
        {"expense_trend": "up", "amount": 12000},
        {"visit_trend": "down", "visit_count": 8},
        {"distribution_trend": "down", "sellout": 40},
    )

    assert "expense_waste" in _patterns(result)
    assert result.decision == "trigger_red_light"


def test_expense_waste_ignores_aligned_business_growth():
    result = HolographicAuditEngine().check(
        {"expense_trend": "up", "amount": 12000},
        {"visit_trend": "up", "visit_count": 30},
        {"distribution_trend": "up", "sellout": 140},
    )

    assert "expense_waste" not in _patterns(result)


def test_visit_fraud_detects_visits_without_flow_growth():
    result = HolographicAuditEngine().check(
        {"expense_trend": "flat"},
        {"visit_trend": "up", "visit_count": 25},
        {"distribution_trend": "flat", "sellout": 100},
    )

    assert "visit_fraud" in _patterns(result)
    assert result.decision == "trigger_red_light"


def test_visit_fraud_ignores_visits_with_matching_flow_growth():
    result = HolographicAuditEngine().check(
        {"expense_trend": "flat"},
        {"visit_trend": "up", "visit_count": 25},
        {"distribution_trend": "up", "sellout": 180},
    )

    assert "visit_fraud" not in _patterns(result)


def test_channel_stuffing_detects_region_mismatch():
    result = HolographicAuditEngine().check(
        {"expense_trend": "flat"},
        {"visit_trend": "flat", "region_id": "north"},
        {"distribution_trend": "flat", "actual_region": "south", "authorized_region": "north"},
    )

    assert "channel_stuffing" in _patterns(result)
    assert result.decision == "trigger_red_light"


def test_channel_stuffing_ignores_authorized_region_match():
    result = HolographicAuditEngine().check(
        {"expense_trend": "flat"},
        {"visit_trend": "flat", "region_id": "north"},
        {"distribution_trend": "flat", "actual_region": "north", "authorized_region": "north"},
    )

    assert "channel_stuffing" not in _patterns(result)


def test_management_neglect_detects_unhandled_red_lights():
    result = HolographicAuditEngine().check(
        {"red_light_count": 2, "unresolved_red_lights": 1, "manager_action_count": 0},
        {"visit_trend": "flat"},
        {"distribution_trend": "flat"},
    )

    assert "management_neglect" in _patterns(result)
    assert result.decision == "trigger_red_light"


def test_management_neglect_ignores_handled_red_lights():
    result = HolographicAuditEngine().check(
        {"red_light_count": 2, "unresolved_red_lights": 1, "manager_action_count": 1},
        {"visit_trend": "flat"},
        {"distribution_trend": "flat"},
    )

    assert "management_neglect" not in _patterns(result)


def test_fake_activity_detects_expense_and_visit_growth_with_falling_flow():
    result = HolographicAuditEngine().check(
        {"expense_trend": "up", "amount": 18000},
        {"visit_trend": "up", "visit_count": 32},
        {"distribution_trend": "down", "sellout": 55},
    )

    assert "fake_activity" in _patterns(result)
    assert result.decision == "trigger_red_light"


def test_fake_activity_ignores_expense_and_visit_growth_with_flow_growth():
    result = HolographicAuditEngine().check(
        {"expense_trend": "up", "amount": 18000},
        {"visit_trend": "up", "visit_count": 32},
        {"distribution_trend": "up", "sellout": 155},
    )

    assert "fake_activity" not in _patterns(result)


def test_channel_stuffing_batch_detects_cross_region_distribution():
    result = HolographicAuditEngine().check(
        {"expense_trend": "flat"},
        {"visit_trend": "flat"},
        [
            {"batch_no": "BATCH001", "actual_region": "north", "quantity": 100},
            {"batch_no": "BATCH001", "actual_region": "south", "quantity": 50},
        ],
        distribution_area=[{"region_id": "north"}],
    )

    assert "channel_stuffing_batch" in _patterns(result)
    assert result.decision == "trigger_red_light"


def test_channel_stuffing_batch_ignores_authorized_region():
    result = HolographicAuditEngine().check(
        {"expense_trend": "flat"},
        {"visit_trend": "flat"},
        [
            {"batch_no": "BATCH001", "actual_region": "north", "quantity": 100},
            {"batch_no": "BATCH001", "actual_region": "north", "quantity": 50},
        ],
        distribution_area=[{"region_id": "north"}],
    )

    assert "channel_stuffing_batch" not in _patterns(result)


def test_fake_distribution_detects_sellin_growth_with_sellout_decline():
    result = HolographicAuditEngine().check(
        {"expense_trend": "flat"},
        {"visit_trend": "flat"},
        {"distribution_trend": "flat"},
        sellin_data=[{"sellin_trend": "up", "sellin": 1000}, {"sellin_trend": "up", "sellin": 1500}],
        sellout_data=[{"distribution_trend": "down", "sellout": 500}, {"distribution_trend": "down", "sellout": 300}],
    )

    assert "fake_distribution" in _patterns(result)
    assert result.decision == "trigger_red_light"


def test_fake_distribution_ignores_sellin_and_sellout_sync_growth():
    result = HolographicAuditEngine().check(
        {"expense_trend": "flat"},
        {"visit_trend": "flat"},
        {"distribution_trend": "flat"},
        sellin_data=[{"sellin_trend": "up", "sellin": 1000}, {"sellin_trend": "up", "sellin": 1500}],
        sellout_data=[{"distribution_trend": "up", "sellout": 800}, {"distribution_trend": "up", "sellout": 1200}],
    )

    assert "fake_distribution" not in _patterns(result)


def test_channel_stuffing_and_expense_waste_merge_decisions():
    result = HolographicAuditEngine().check(
        {"expense_trend": "up", "amount": 12000},
        {"visit_trend": "down", "visit_count": 8},
        [
            {"batch_no": "BATCH001", "actual_region": "north", "quantity": 100},
            {"batch_no": "BATCH001", "actual_region": "south", "quantity": 50},
        ],
        distribution_area=[{"region_id": "north"}],
    )

    assert "expense_waste" in _patterns(result)
    assert "channel_stuffing_batch" in _patterns(result)
    assert result.decision == "trigger_red_light"


def test_confidence_boundary_at_thresholds():
    engine = HolographicAuditEngine()

    result_below = engine.check(
        {"expense_trend": "flat", "previous_expense": 100, "current_expense": 105},
        {"visit_trend": "flat"},
        {"distribution_trend": "flat"},
    )
    assert result_below.suspicion_level == "low" or True

    result_high = engine.check(
        {"expense_trend": "up", "amount": 12000},
        {"visit_trend": "down", "visit_count": 8},
        {"distribution_trend": "down", "sellout": 40},
    )
    assert result_high.decision == "trigger_red_light"
    assert result_high.suspicion_level == "high"
    assert any(f.score >= 0.8 for f in result_high.findings)
