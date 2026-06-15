class TestMonitoringPlan:
    def test_health_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
