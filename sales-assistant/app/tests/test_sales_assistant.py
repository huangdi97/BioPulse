class TestScheduleManagement:
    def test_schedule_crud_flow(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}

        resp = client.post(
            "/schedule",
            json={
                "title": "Client Meeting",
                "description": "Discuss quarterly results",
                "event_type": "meeting",
                "start_time": "2024-06-15T09:00:00",
                "end_time": "2024-06-15T10:00:00",
                "location": "Beijing Office",
            },
            headers=headers,
        )
        assert resp.status_code == 201
        schedule_id = resp.json()["data"]["id"]

        resp = client.get(f"/schedule/{schedule_id}", headers=headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["title"] == "Client Meeting"
        assert data["event_type"] == "meeting"
        assert data["is_completed"] == 0

        resp = client.get("/schedule", headers=headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] >= 1

        resp = client.patch(
            f"/schedule/{schedule_id}",
            json={"is_completed": 1, "description": "Completed quarterly review"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["is_completed"] == 1


class TestHCPManagement:
    def test_hcp_crud_flow(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}

        resp = client.post(
            "/hcp",
            json={
                "name": "Dr. Zhao",
                "hospital": "Tongji Hospital",
                "department": "Respiratory",
                "specialty": "Asthma",
                "tier": "A",
                "city": "Wuhan",
            },
            headers=headers,
        )
        assert resp.status_code == 201
        hcp_id = resp.json()["data"]["id"]

        resp = client.get(f"/hcp/{hcp_id}", headers=headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["name"] == "Dr. Zhao"
        assert data["tier"] == "A"


class TestContentCRUD:
    def test_content_crud_flow(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}

        resp = client.post(
            "/contents",
            json={
                "title": "Product Brochure Q3",
                "content_type": "product_material",
                "category": "Cardiology",
                "content": "Detailed product specifications and clinical data.",
                "summary": "Q3 product brochure for DrugX",
            },
            headers=headers,
        )
        assert resp.status_code == 201
        content_id = resp.json()["data"]["id"]

        resp = client.get(f"/contents/{content_id}", headers=headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["title"] == "Product Brochure Q3"
        assert data["content_type"] == "product_material"


class TestStrategyManagement:
    def test_strategy_crud_flow(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}

        resp = client.post(
            "/strategies",
            json={
                "hcp_name": "Dr. Sun",
                "goal": "Increase DrugX adoption by 20%",
                "approach": "Data-driven clinical evidence presentation",
                "talking_points": "Efficacy data from recent trial",
                "expected_outcome": "Positive engagement and follow-up meeting",
            },
            headers=headers,
        )
        assert resp.status_code == 201
        strategy_id = resp.json()["data"]["id"]

        resp = client.get(f"/strategies/{strategy_id}", headers=headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["hcp_name"] == "Dr. Sun"
        assert data["status"] == ("planned" if data.get("status") else None)


class TestAuthChecks:
    def test_unauthorized_returns_401(self, client):
        resp = client.get("/schedule")
        assert resp.status_code == 401

        resp = client.post(
            "/schedule", json={"title": "Test", "start_time": "2024-01-01T00:00:00"}
        )
        assert resp.status_code == 401

        resp = client.get("/hcp")
        assert resp.status_code == 401

        resp = client.get("/contents")
        assert resp.status_code == 401

        resp = client.get("/strategies")
        assert resp.status_code == 401

    def test_invalid_token_returns_401(self, client):
        headers = {"Authorization": "Bearer invalidtoken123"}
        resp = client.get("/schedule", headers=headers)
        assert resp.status_code == 401

    def test_health_does_not_require_auth(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "db" in data
        assert "uptime" in data
