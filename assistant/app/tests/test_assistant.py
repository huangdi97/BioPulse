class TestHCPCRUD:
    def test_create_hcp(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = client.post(
            "/hcp",
            json={
                "name": "Dr. Zhang",
                "hospital": "Beijing Hospital",
                "department": "Cardiology",
                "title": "Chief Physician",
                "specialty": "Interventional Cardiology",
            },
            headers=headers,
        )
        assert resp.status_code == 201
        assert resp.json()["data"]["id"] is not None

    def test_hcp_crud_flow(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}

        resp = client.post(
            "/hcp",
            json={
                "name": "Dr. Li",
                "hospital": "Shanghai Hospital",
                "department": "Neurology",
                "specialty": "Stroke",
                "level": "B",
            },
            headers=headers,
        )
        assert resp.status_code == 201
        hcp_id = resp.json()["data"]["id"]

        resp = client.get(f"/hcp/{hcp_id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "Dr. Li"
        assert resp.json()["data"]["level"] == "B"

        resp = client.patch(
            f"/hcp/{hcp_id}",
            json={"department": "Neurosurgery", "level": "A"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["department"] == "Neurosurgery"
        assert resp.json()["data"]["level"] == "A"

        resp = client.get("/hcp", headers=headers)
        assert resp.status_code == 200
        items = resp.json()["data"]["items"]
        assert len(items) >= 1


class TestVisitScheduling:
    def test_visit_crud_flow(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}

        resp = client.post(
            "/hcp",
            json={
                "name": "Dr. Wang",
                "hospital": "Guangzhou Hospital",
                "department": "Oncology",
            },
            headers=headers,
        )
        assert resp.status_code == 201
        hcp_id = resp.json()["data"]["id"]

        resp = client.post(
            "/visits",
            json={
                "hcp_id": hcp_id,
                "visit_type": "academic",
                "summary": "Discussed new treatment options",
                "mood": "positive",
                "is_completed": 0,
            },
            headers=headers,
        )
        assert resp.status_code == 201
        visit_id = resp.json()["data"]["id"]

        resp = client.get(f"/visits/{visit_id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["data"]["summary"] == "Discussed new treatment options"

        resp = client.patch(
            f"/visits/{visit_id}",
            json={"is_completed": 1, "mood": "very_positive"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["is_completed"] == 1

        resp = client.get("/visits", headers=headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] >= 1


class TestKnowledgeBase:
    def test_knowledge_crud(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}

        resp = client.post(
            "/knowledge",
            json={
                "title": "Type 2 Diabetes Guidelines",
                "category": "endocrinology",
                "content": "Latest treatment guidelines for T2DM management.",
                "difficulty": "advanced",
            },
            headers=headers,
        )
        assert resp.status_code == 201
        knowledge_id = resp.json()["data"]["id"]

        resp = client.get(f"/knowledge/{knowledge_id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["data"]["title"] == "Type 2 Diabetes Guidelines"

        resp = client.patch(
            f"/knowledge/{knowledge_id}",
            json={"title": "Updated T2DM Guidelines", "difficulty": "intermediate"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["title"] == "Updated T2DM Guidelines"

    def test_knowledge_search(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}

        resp = client.post(
            "/knowledge",
            json={
                "title": "Hypertension Management",
                "category": "cardiology",
                "content": "Blood pressure control strategies for resistant hypertension.",
            },
            headers=headers,
        )
        assert resp.status_code == 201

        resp = client.get(
            "/knowledge/search",
            params={"q": "hypertension"},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] >= 1


class TestAuthChecks:
    def test_unauthorized_returns_401(self, client):
        resp = client.get("/hcp")
        assert resp.status_code == 401

        resp = client.post("/hcp", json={"name": "Test", "hospital": "H"})
        assert resp.status_code == 401

        resp = client.get("/visits")
        assert resp.status_code == 401

        resp = client.get("/knowledge")
        assert resp.status_code == 401

    def test_invalid_token_returns_401(self, client):
        headers = {"Authorization": "Bearer invalidtoken123"}
        resp = client.get("/hcp", headers=headers)
        assert resp.status_code == 401

    def test_health_does_not_require_auth(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "db" in data
        assert "uptime" in data
