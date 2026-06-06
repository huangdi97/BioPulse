import uuid

from shared.auth import create_access_token


def _register_and_get_visit_token(client):
    username = f"pharma_{uuid.uuid4().hex[:8]}"
    resp = client.post("/auth/register", json={"username": username, "password": "testpass123"})
    assert resp.status_code == 201
    user_id = resp.json()["data"]["user_id"]
    token = create_access_token(user_id, "rep", "visit")
    return token


class TestPharmaE2E:
    def test_pharma_compliant_flow(self, client):
        token = _register_and_get_visit_token(client)
        visit_data = {
            "notes": "正常拜访，讨论学术合作",
            "expenses": 0,
            "rep_id": 1,
            "rep_verified": True,
            "location_type": "hospital",
            "call_type": "常规拜访",
        }
        resp = client.post(
            "/api/compliance/enforce",
            json={"visit_data": visit_data},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["passed"] is True
        assert len(data["violations"]) == 0

    def test_pharma_violation_flow(self, client):
        token = _register_and_get_visit_token(client)
        visit_data = {
            "notes": "医生透露了本月处方量数据",
            "expenses": 0,
            "rep_id": 2,
            "rep_verified": True,
            "location_type": "hospital",
            "call_type": "常规拜访",
        }
        resp = client.post(
            "/api/compliance/enforce",
            json={"visit_data": visit_data},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["passed"] is False
        assert len(data["violations"]) > 0

    def test_boundary_empty_visit(self, client):
        token = _register_and_get_visit_token(client)
        resp = client.post(
            "/api/compliance/enforce",
            json={"visit_data": {}},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["passed"] is True
        assert len(data["violations"]) == 0

    def test_boundary_negative_expense(self, client):
        token = _register_and_get_visit_token(client)
        visit_data = {
            "notes": "正常拜访",
            "expenses": -500,
            "rep_id": 1,
            "rep_verified": True,
            "location_type": "hospital",
            "call_type": "普通",
        }
        resp = client.post(
            "/api/compliance/enforce",
            json={"visit_data": visit_data},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["passed"] is True
        assert len(data["violations"]) == 0

    def test_boundary_long_notes(self, client):
        token = _register_and_get_visit_token(client)
        long_notes = "学术交流" * 5000
        visit_data = {
            "notes": long_notes,
            "expenses": 0,
            "rep_id": 1,
            "rep_verified": True,
            "location_type": "hospital",
            "call_type": "常规拜访",
        }
        resp = client.post(
            "/api/compliance/enforce",
            json={"visit_data": visit_data},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["passed"] is True

    def test_compliance_dashboard(self, client):
        token = _register_and_get_visit_token(client)
        visit_data = {
            "notes": "医生透露了本月开方数信息",
            "expenses": 0,
            "rep_id": 3,
            "rep_verified": True,
            "location_type": "hospital",
            "call_type": "常规拜访",
        }
        client.post(
            "/api/compliance/enforce",
            json={"visit_data": visit_data},
            headers={"Authorization": f"Bearer {token}"},
        )
        resp = client.get(
            "/api/compliance/dashboard/summary",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_violations_today"] > 0
