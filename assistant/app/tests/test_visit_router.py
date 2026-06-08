class TestVisitCRUD:
    def test_create_hcp_and_visit(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = client.post(
            "/hcp",
            json={"name": "Dr. Test", "hospital": "Test Hospital", "department": "Test Dept"},
            headers=headers,
        )
        assert resp.status_code == 201
        hcp_id = resp.json()["data"]["id"]

        resp = client.post(
            "/visits",
            json={
                "hcp_id": hcp_id,
                "visit_type": "academic",
                "summary": "Test visit summary",
                "mood": "positive",
            },
            headers=headers,
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["id"] is not None
        assert data["hcp_id"] == hcp_id

    def test_list_visits_returns_paginated(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = client.get("/visits", headers=headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "items" in data
        assert "total" in data

    def test_get_visit_not_found(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = client.get("/visits/99999", headers=headers)
        assert resp.status_code == 404

    def test_update_visit_not_found(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = client.patch("/visits/99999", json={"summary": "updated"}, headers=headers)
        assert resp.status_code == 404

    def test_delete_visit_not_found(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = client.delete("/visits/99999", headers=headers)
        assert resp.status_code == 404
