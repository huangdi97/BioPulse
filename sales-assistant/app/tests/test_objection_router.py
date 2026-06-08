class TestObjectionRouter:
    def test_handle_objection_fallback(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = client.post(
            "/objection",
            json={"objection": "药品价格太贵了", "customer_type": "主任医生", "context": "科室年度采购会"},
            headers=headers,
        )
        assert resp.status_code in (200, 503)
        if resp.status_code == 200:
            data = resp.json()["data"]
            assert "objection" in data
            assert "analysis" in data
            assert "response_suggestion" in data
            assert isinstance(data.get("key_points"), list)
            assert isinstance(data.get("do_not_say"), list)

    def test_list_objections(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = client.get("/objections", headers=headers)
        assert resp.status_code == 200
        assert isinstance(resp.json()["data"], list)

    def test_handle_objection_missing_objection(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = client.post(
            "/objection",
            json={},
            headers=headers,
        )
        assert resp.status_code == 422
