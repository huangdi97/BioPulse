"""Tests for one-vote red-light handling."""

from cloud.app.compliance.red_light import RedLightManager


def test_red_light_trigger_sends_three_level_notifications():
    manager = RedLightManager()

    event = manager.trigger(
        "rep-001",
        "L2",
        {"rule": "expense_visit_mismatch"},
        notify_levels=["L1", "L2", "L3"],
    )

    assert event.status == "active"
    assert event.incentives_paused is True
    assert [item.role for item in event.notifications] == [
        "compliance_officer",
        "regional_manager",
        "president",
    ]
    assert manager.get_active("rep-001") == event


def test_retrospective_review_upgrades_active_red_light():
    manager = RedLightManager()
    event = manager.trigger("rep-002", "L1", {"score": 0.6}, notify_levels=["L1"])

    upgraded = manager.retrospect("rep-002", {"confidence_score": 0.95, "rule_hit": "fake_activity"})

    assert upgraded is event
    assert upgraded.level == "L3"
    assert upgraded.history[-1]["action"] == "upgrade"
    assert any(notification.role == "president" for notification in upgraded.notifications)


def test_retrospective_review_revokes_active_red_light():
    manager = RedLightManager()
    manager.trigger("rep-003", "L2", {"score": 0.82})

    revoked = manager.retrospect("rep-003", {"exonerating": True, "source": "audit_review"})

    assert revoked.status == "revoked"
    assert revoked.incentives_paused is False
    assert manager.get_active("rep-003") is None
    assert manager.is_incentive_paused("rep-003") is False


def test_red_light_forces_incentive_pause():
    manager = RedLightManager()

    manager.trigger("rep-004", "L1", {"rule": "visit_fraud"})

    assert manager.is_incentive_paused("rep-004") is True
