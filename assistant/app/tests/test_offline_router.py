class TestOffline:
    def test_get_offline_status(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = client.get("/offline/status", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0

    def test_enable_offline_mode(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = client.post("/offline/enable", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0

    def test_disable_offline_mode(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = client.post("/offline/disable", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
