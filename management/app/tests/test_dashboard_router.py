class TestDashboard:
    def test_dashboard_returns_ok(self, client):
        resp = client.get("/api/management/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert "data" in data

    def test_dashboard_users(self, client):
        resp = client.get("/api/management/dashboard/users")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0

    def test_dashboard_compliance(self, client):
        resp = client.get("/api/management/dashboard/compliance")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
