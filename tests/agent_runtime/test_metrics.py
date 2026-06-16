from cloud.app.agent_runtime.metrics import agent_active_count, agent_requests_total, get_metrics


def test_metrics_label_names():
    assert "agent_name" in agent_requests_total._labelnames
    assert "status" in agent_requests_total._labelnames
    assert "agent_name" in agent_active_count._labelnames


def test_get_metrics_returns_string():
    result = get_metrics()
    assert isinstance(result, str)
    assert "agent_requests_total" in result
