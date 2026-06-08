class TestBiddingRouter:
    def test_create_bidding(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = client.post(
            "/bidding",
            json={
                "title": "Test Tender",
                "hospital": "Test Hospital",
                "department": "Cardiology",
            },
            headers=headers,
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["id"] is not None

    def test_list_bidding(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = client.get("/bidding", headers=headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "items" in data

    def test_get_bidding_not_found(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = client.get("/bidding/99999", headers=headers)
        assert resp.status_code == 404
