class TestDashboard:
    def test_dashboard_endpoints(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}

        resp = client.get("/dashboard/overview", headers=headers)
        assert resp.status_code == 200
        overview = resp.json()["data"]
        assert "user_count" in overview
        assert "content_count" in overview
        assert "compliance_rate" in overview

        resp = client.get("/dashboard/users", headers=headers)
        assert resp.status_code == 200
        assert "by_role" in resp.json()["data"]

        resp = client.get("/dashboard/compliance", headers=headers)
        assert resp.status_code == 200
        assert "pass_rate" in resp.json()["data"]

        resp = client.get("/dashboard/contents", headers=headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "by_category" in data
        assert "by_status" in data


class TestAiGateway:
    def test_chat_requires_auth(self, client):
        resp = client.post("/ai/chat", json={"messages": [{"role": "user", "content": "hi"}]})
        assert resp.status_code == 401


class TestInteractionRouter:
    def test_get_interactions(self, client, auth_token):
        resp = client.get(
            "/interactions/",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200


class TestTaskRouter:
    def test_get_tasks(self, client, auth_token):
        resp = client.get(
            "/tasks/",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
