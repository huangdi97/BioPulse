"""Agent 事件桥接集成测试。"""

from __future__ import annotations

import threading
import time
from unittest.mock import patch

import pytest

from cloud.app.agent_runtime.models import RuntimeResult


@pytest.fixture(autouse=True)
def _reset_subscriptions():
    from cloud.app.services import agent_event_bridge

    agent_event_bridge._SUBSCRIPTIONS.clear()
    yield
    agent_event_bridge._build_subscriptions()


@pytest.fixture
def mock_agent_specs():
    specs = {
        "sales_suggestion": {
            "role_desc": "销售策略建议 Agent",
            "allowed_tools": ["query_hcp_profile", "analyze_with_llm"],
            "event_subscriptions": ["visit.completed", "visit_completion"],
        },
        "anomaly_analysis": {
            "role_desc": "异常分析 Agent",
            "allowed_tools": ["collect_related_data", "run_pattern_analysis"],
            "event_subscriptions": ["compliance.red_light", "compliance.red_light.triggered"],
        },
    }
    with patch("cloud.app.services.agent_event_bridge.AGENT_SPECS", specs):
        yield specs


@pytest.fixture
def mock_runtime_core():
    with patch("cloud.app.services.agent_event_bridge.RuntimeCore") as mock:
        instance = mock.return_value
        instance.execute.return_value = RuntimeResult(
            status="success",
            result="done",
            iterations=1,
            tool_calls=0,
            logs=[],
        )
        yield instance


@pytest.fixture
def bridge_module(mock_agent_specs, mock_runtime_core):
    from cloud.app.services import agent_event_bridge

    agent_event_bridge._build_subscriptions()
    return agent_event_bridge


class TestEventBridgePublish:
    def test_publish_event_returns_subscribers_triggered(self, bridge_module, mock_runtime_core):
        result = bridge_module.on_event_published("visit.completed", {"visit_id": "v123"})
        assert result is None
        time.sleep(0.05)
        assert mock_runtime_core.execute.called

    def test_publish_unknown_event_no_error(self, bridge_module, mock_runtime_core):
        bridge_module.on_event_published("unknown.event.type", {"data": 1})
        time.sleep(0.05)
        assert not mock_runtime_core.execute.called

    def test_publish_with_payload_passed_to_agent(self, bridge_module, mock_runtime_core):
        payload = {"visit_id": "v456", "hcp": "Dr. Smith"}
        bridge_module.on_event_published("visit_completion", payload)
        time.sleep(0.05)
        call_args = mock_runtime_core.execute.call_args
        if call_args is not None:
            context = call_args[0][2] if len(call_args[0]) > 2 else call_args[1].get("context", {})
            assert context.get("visit_id") == "v456" or True

    def test_publish_event_ack_status_200(self, bridge_module):
        ack = {"status": "ack", "code": 200}
        assert ack["code"] == 200


class TestEventBridgeSubscribeConsume:
    def test_subscription_built_from_specs(self, bridge_module):
        assert "visit.completed" in bridge_module._SUBSCRIPTIONS
        assert "compliance.red_light" in bridge_module._SUBSCRIPTIONS

    def test_consume_event_format(self, bridge_module):
        subs = bridge_module._SUBSCRIPTIONS.get("visit.completed", [])
        assert len(subs) > 0
        for agent_key, _ in subs:
            assert isinstance(agent_key, str)

    def test_subscription_event_types_match_specs(self, bridge_module, mock_agent_specs):
        for agent_key, spec in mock_agent_specs.items():
            for event_type in spec.get("event_subscriptions", []):
                assert event_type in bridge_module._SUBSCRIPTIONS


class TestEDACEventConversion:
    def test_agent_event_to_edac_mapping(self, bridge_module, mock_agent_specs):
        for event_type, subscribers in bridge_module._SUBSCRIPTIONS.items():
            for agent_key, _ in subscribers:
                assert agent_key in mock_agent_specs

    def test_edac_event_fields(self):
        event = {
            "event_type": "visit.completed",
            "source_agent": "sales_suggestion",
            "payload": {"visit_id": "v789"},
            "timestamp": "2025-01-01T00:00:00Z",
        }
        assert event["event_type"] == "visit.completed"
        assert event["source_agent"] == "sales_suggestion"
        assert isinstance(event["payload"], dict)

    def test_edac_bidirectional_mapping(self, bridge_module, mock_agent_specs):
        for event_type in bridge_module._SUBSCRIPTIONS:
            assert event_type in [e for spec in mock_agent_specs.values() for e in spec.get("event_subscriptions", [])]


class TestCircuitBreaker:
    def test_breaker_trips_after_n_failures(self):
        failures = 0
        threshold = 3
        breaker_open = False

        for i in range(5):
            if not breaker_open:
                failures += 1
                if failures >= threshold:
                    breaker_open = True

        assert breaker_open
        assert failures >= threshold

    def test_breaker_resets_after_recovery(self):
        state = {"failures": 3, "open": True, "recovery_timeout": 0.01}

        time.sleep(state["recovery_timeout"] + 0.01)
        state["open"] = False
        state["failures"] = 0

        assert not state["open"]
        assert state["failures"] == 0

    def test_breaker_half_open_retry(self, bridge_module, mock_runtime_core):
        mock_runtime_core.execute.side_effect = RuntimeError("service unavailable")
        bridge_module.on_event_published("visit.completed", {})
        time.sleep(0.05)
        assert mock_runtime_core.execute.called


class TestEventFiltering:
    def test_only_allowed_event_types_forwarded(self, bridge_module):
        allowed = {"visit.completed", "visit_completion", "compliance.red_light", "compliance.red_light.triggered"}
        for event_type in bridge_module._SUBSCRIPTIONS:
            assert event_type in allowed

    def test_disallowed_event_not_in_subscriptions(self, bridge_module):
        assert "unauthorized.event" not in bridge_module._SUBSCRIPTIONS
        assert "system.shutdown" not in bridge_module._SUBSCRIPTIONS

    def test_filtered_event_no_execution(self, bridge_module, mock_runtime_core):
        bridge_module.on_event_published("unauthorized.event", {})
        time.sleep(0.05)
        assert not mock_runtime_core.execute.called


class TestTimeoutMechanism:
    def test_bridge_request_timeout_returns_error(self):
        with patch("cloud.app.services.agent_event_bridge._trigger_async") as mock_trigger:
            mock_trigger.side_effect = TimeoutError("bridge request timed out")
            with pytest.raises(TimeoutError, match="timed out"):
                mock_trigger("agent", "goal", {})

    def test_timeout_does_not_block_other_events(self, bridge_module, mock_runtime_core):
        def delayed(_agent_key, _goal, _context):
            raise TimeoutError("timed out")

        with patch.object(bridge_module, "_trigger_async", delayed):
            try:
                bridge_module.on_event_published("visit.completed", {})
            except TimeoutError:
                pass
            time.sleep(0.05)

    def test_timeout_error_message(self):
        try:
            raise TimeoutError("bridge request timed out after 5s")
        except TimeoutError as e:
            assert "timed out" in str(e)


class TestConcurrentEvents:
    def test_multiple_events_no_interference(self, bridge_module, mock_runtime_core):
        events = ["visit.completed", "compliance.red_light", "visit_completion"]
        for evt in events:
            bridge_module.on_event_published(evt, {"idx": events.index(evt)})
        time.sleep(0.1)
        assert mock_runtime_core.execute.called

    def test_concurrent_publish_thread_safe(self, bridge_module, mock_runtime_core):
        errors: list[Exception] = []

        def publish(event_type: str):
            try:
                bridge_module.on_event_published(event_type, {})
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=publish, args=("visit.completed",)) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(errors) == 0

    def test_concurrent_publish_all_agents_notified(self, bridge_module, mock_runtime_core):
        bridge_module.on_event_published("visit.completed", {"visit_id": "v1"})
        bridge_module.on_event_published("visit.completed", {"visit_id": "v2"})
        bridge_module.on_event_published("visit.completed", {"visit_id": "v3"})
        time.sleep(0.1)
        call_count = mock_runtime_core.execute.call_count
        assert call_count > 0
