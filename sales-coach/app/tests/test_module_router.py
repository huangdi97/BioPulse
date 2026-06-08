class TestModuleRouter:
    def test_create_module(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = client.post(
            "/modules",
            json={
                "title": "Test Module",
                "description": "Test description",
                "category": "test",
                "difficulty": "beginner",
            },
            headers=headers,
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["id"] is not None

    def test_list_modules(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = client.get("/modules", headers=headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "items" in data

    def test_get_module_not_found(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = client.get("/modules/99999", headers=headers)
        assert resp.status_code == 404
