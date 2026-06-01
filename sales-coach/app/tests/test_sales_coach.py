class TestModuleCRUD:
    def test_module_crud_flow(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}

        resp = client.post(
            "/modules",
            json={
                "title": "Advanced Negotiation Skills",
                "description": "Learn advanced negotiation techniques.",
                "category": "soft_skills",
                "difficulty": "advanced",
            },
            headers=headers,
        )
        assert resp.status_code == 201
        module_id = resp.json()["data"]["id"]

        resp = client.get(f"/modules/{module_id}", headers=headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["title"] == "Advanced Negotiation Skills"
        assert data["difficulty"] == "advanced"

        resp = client.get("/modules", headers=headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] >= 1


class TestScenarioManagement:
    def test_scenario_crud_flow(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}

        resp = client.post(
            "/scenarios",
            json={
                "title": "Handling Objections",
                "role_setting": "Sales rep meets procurement manager",
                "goal": "Overcome price objections",
                "difficulty": "hard",
                "category": "objection_handling",
            },
            headers=headers,
        )
        assert resp.status_code == 201
        scenario_id = resp.json()["data"]["id"]

        resp = client.get(f"/scenarios/{scenario_id}", headers=headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["title"] == "Handling Objections"
        assert data["difficulty"] == "hard"


class TestSessionManagement:
    def test_session_crud_flow(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}

        resp = client.post(
            "/modules",
            json={
                "title": "Session Test Module",
                "description": "Module for session testing.",
            },
            headers=headers,
        )
        assert resp.status_code == 201
        module_id = resp.json()["data"]["id"]

        resp = client.post(
            f"/modules/{module_id}/sessions",
            json={
                "trainee_name": "Zhang Wei",
                "score": 85,
                "feedback": "Good performance on objection handling.",
            },
            headers=headers,
        )
        assert resp.status_code == 201
        session_id = resp.json()["data"]["id"]

        resp = client.get(f"/sessions/{session_id}", headers=headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["trainee_name"] == "Zhang Wei"
        assert data["score"] == 85

        resp = client.patch(
            f"/sessions/{session_id}",
            json={"score": 90, "feedback": "Improved significantly."},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["score"] == 90


class TestAssessmentCRUD:
    def test_assessment_crud_flow(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}

        resp = client.post(
            "/assessments",
            json={
                "title": "Q4 Performance Review",
                "trainee_name": "Li Ming",
                "current_level": "beginner",
                "target_level": "intermediate",
                "strengths": "Communication skills",
                "weaknesses": "Product knowledge",
            },
            headers=headers,
        )
        assert resp.status_code == 201
        assessment_id = resp.json()["data"]["id"]

        resp = client.get(f"/assessments/{assessment_id}", headers=headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["trainee_name"] == "Li Ming"
        assert data["current_level"] == "beginner"


class TestAuthChecks:
    def test_unauthorized_returns_401(self, client):
        resp = client.get("/modules")
        assert resp.status_code == 401

        resp = client.post("/modules", json={"title": "Test"})
        assert resp.status_code == 401

        resp = client.get("/scenarios")
        assert resp.status_code == 401

        resp = client.get("/assessments")
        assert resp.status_code == 401

    def test_invalid_token_returns_401(self, client):
        headers = {"Authorization": "Bearer invalidtoken123"}
        resp = client.get("/modules", headers=headers)
        assert resp.status_code == 401

    def test_health_does_not_require_auth(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "db" in data
        assert "uptime" in data
