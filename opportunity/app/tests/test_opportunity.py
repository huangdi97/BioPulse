class TestOpportunityCRUD:
    def test_opportunity_crud_flow(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}

        resp = client.post(
            "/opportunities",
            json={
                "name": "New Drug Launch Support",
                "hcp_name": "Dr. Chen",
                "hospital": "Nanjing Hospital",
                "product": "DrugX",
                "estimated_value": 500000.0,
                "stage": "lead",
            },
            headers=headers,
        )
        assert resp.status_code == 201
        opp_id = resp.json()["data"]["id"]

        resp = client.get(f"/opportunities/{opp_id}", headers=headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["name"] == "New Drug Launch Support"
        assert data["stage"] == "lead"

        resp = client.patch(
            f"/opportunities/{opp_id}",
            json={"stage": "negotiation", "probability": 50},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["stage"] == "negotiation"
        assert resp.json()["data"]["probability"] == 50

        resp = client.get("/opportunities", headers=headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] >= 1


class TestContactCRUD:
    def test_contact_crud_flow(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}

        resp = client.post(
            "/opportunities",
            json={
                "name": "Contact Test Opportunity",
                "hcp_name": "Dr. Wu",
                "hospital": "Hangzhou Hospital",
            },
            headers=headers,
        )
        assert resp.status_code == 201
        opp_id = resp.json()["data"]["id"]

        resp = client.post(
            f"/opportunities/{opp_id}/contacts",
            json={
                "contact_type": "phone_call",
                "summary": "Discussed pricing options",
                "contact_date": "2024-06-15T10:00:00",
            },
            headers=headers,
        )
        assert resp.status_code == 201
        contact_id = resp.json()["data"]["id"]

        resp = client.get(f"/contacts/{contact_id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["data"]["summary"] == "Discussed pricing options"

        resp = client.get(
            f"/opportunities/{opp_id}/contacts",
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] >= 1


class TestBiddingCRUD:
    def test_bidding_crud_flow(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}

        resp = client.post(
            "/bidding",
            json={
                "title": "Hospital Equipment Tender",
                "hospital": "West China Hospital",
                "department": "Surgery",
                "product_category": "Surgical Instruments",
                "budget": 2000000.0,
                "deadline": "2024-12-31",
            },
            headers=headers,
        )
        assert resp.status_code == 201
        bidding_id = resp.json()["data"]["id"]

        resp = client.get(f"/bidding/{bidding_id}", headers=headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["title"] == "Hospital Equipment Tender"
        assert data["status"] == "new"

        resp = client.patch(
            f"/bidding/{bidding_id}",
            json={"status": "in_progress"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "in_progress"


class TestPubPeer:
    def test_pubpeer_list(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}

        resp = client.get("/pubpeer/alerts", headers=headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "items" in data
        assert "total" in data


class TestAuthChecks:
    def test_unauthorized_returns_401(self, client):
        resp = client.get("/opportunities")
        assert resp.status_code == 401

        resp = client.post("/opportunities", json={"name": "Test"})
        assert resp.status_code == 401

        resp = client.get("/bidding")
        assert resp.status_code == 401

        resp = client.get("/pubpeer/alerts")
        assert resp.status_code == 401

    def test_invalid_token_returns_401(self, client):
        headers = {"Authorization": "Bearer invalidtoken123"}
        resp = client.get("/opportunities", headers=headers)
        assert resp.status_code == 401

    def test_health_does_not_require_auth(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "db" in data
        assert "uptime" in data
