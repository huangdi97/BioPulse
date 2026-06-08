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

    def test_full_visit_compliance_flow(self, client):
        token = _register_and_get_visit_token(client)

        hcp_resp = client.post(
            "/customers/",
            json={
                "name": "Dr. Liu Ming",
                "title": "Chief Physician",
                "hospital": "Beijing Union Hospital",
                "department": "Cardiology",
                "specialty": "Interventional Cardiology",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert hcp_resp.status_code == 201
        hcp = hcp_resp.json()["data"]
        hcp_id = hcp["id"]

        visit_resp = client.post(
            "/visit",
            json={
                "hcp_id": hcp_id,
                "hcp_name": "Dr. Liu Ming",
                "content": "学术合作讨论，介绍新药临床试验",
                "visit_type": "常规拜访",
                "location": "Beijing Union Hospital",
                "location_mode": "on_site",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert visit_resp.status_code == 200

        enforce_resp = client.post(
            "/api/compliance/enforce",
            json={
                "visit_data": {
                    "notes": "学术合作讨论，介绍新药临床试验",
                    "expenses": 0,
                    "rep_id": 1,
                    "rep_verified": True,
                    "location_type": "hospital",
                    "call_type": "常规拜访",
                }
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert enforce_resp.status_code == 200
        data = enforce_resp.json()
        assert data["passed"] is True
        assert len(data["violations"]) == 0

        dashboard_resp = client.get(
            "/api/compliance/dashboard/summary",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert dashboard_resp.status_code == 200

    def test_violation_flow(self, client):
        token = _register_and_get_visit_token(client)

        hcp_resp = client.post(
            "/customers/",
            json={
                "name": "Dr. Wang Fang",
                "title": "Deputy Director",
                "hospital": "Shanghai East Hospital",
                "department": "Oncology",
                "specialty": "Medical Oncology",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert hcp_resp.status_code == 201
        hcp = hcp_resp.json()["data"]
        hcp_id = hcp["id"]

        visit_resp = client.post(
            "/visit",
            json={
                "hcp_id": hcp_id,
                "hcp_name": "Dr. Wang Fang",
                "content": "医生提供了统方数据，包括本月处方量统计",
                "visit_type": "常规拜访",
                "location": "Shanghai East Hospital",
                "location_mode": "on_site",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert visit_resp.status_code == 200

        enforce_resp = client.post(
            "/api/compliance/enforce",
            json={
                "visit_data": {
                    "notes": "医生提供了统方数据，包括本月处方量统计",
                    "expenses": 0,
                    "rep_id": 2,
                    "rep_verified": True,
                    "location_type": "hospital",
                    "call_type": "常规拜访",
                }
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert enforce_resp.status_code == 200
        data = enforce_resp.json()
        assert data["passed"] is False
        assert len(data["violations"]) > 0
        rule_codes = [v["rule_code"] for v in data["violations"]]
        assert any(c.startswith("PHR-") for c in rule_codes)

        dashboard_resp = client.get(
            "/api/compliance/dashboard/summary",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert dashboard_resp.status_code == 200
        dashboard_data = dashboard_resp.json()
        assert dashboard_data["total_violations_today"] > 0
