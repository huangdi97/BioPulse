class TestDashboard:
    def test_dashboard_returns_ok(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = client.get("/api/management/dashboard", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert "data" in data

    def test_dashboard_users(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = client.get("/api/management/dashboard/users", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0

    def test_dashboard_compliance(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = client.get("/api/management/dashboard/compliance", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
