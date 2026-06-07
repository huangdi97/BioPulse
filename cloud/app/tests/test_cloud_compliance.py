class TestComplianceCheck:
    def test_prohibited_content_fails_compliance(self, client, auth_token):
        resp = client.post(
            "/contents/",
            json={
                "title": "Bad Content",
                "body": "This product can 根治 all diseases with absolutely safe formulation 无副作用.",
                "category": "pharma",
                "tags": [],
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["compliance_score"] < 1.0
        assert data["status"] == "pending_review"

    def test_clean_content_passes_compliance(self, client, auth_token):
        resp = client.post(
            "/contents/",
            json={
                "title": "Clean Content",
                "body": "This product should be used as directed by a physician.",
                "category": "pharma",
                "tags": [],
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["compliance_score"] >= 0.8


class TestAuditLogs:
    def test_audit_log_crud_and_stats(self, client, auth_token):
        resp = client.post(
            "/audit/logs",
            json={
                "user_id": 1,
                "action": "test_create",
                "entity_type": "tests",
                "entity_id": 1,
                "detail": "Test audit entry",
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200

        resp = client.post(
            "/audit/logs",
            json={
                "user_id": 1,
                "action": "test_update",
                "entity_type": "tests",
                "entity_id": 2,
                "detail": "Another test audit entry",
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200

        resp = client.get(
            "/audit/logs",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] >= 2
        assert len(data["items"]) >= 2

        resp = client.get(
            "/audit/logs/stats",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        stats = resp.json()["data"]
        assert "by_action" in stats
        assert "daily_trend" in stats


class TestComplianceRulesCRUD:
    def test_compliance_rule_crud(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}

        resp = client.post(
            "/compliance/rules",
            json={
                "name": "Test Rule",
                "category": "pharma",
                "keyword": "test_prohibited",
                "max_value": 0.5,
            },
            headers=headers,
        )
        assert resp.status_code in (200, 201)
        data = resp.json()["data"]
        rule_id = data.get("id") or data.get("rule_id")
        assert rule_id is not None

        resp = client.get("/compliance/rules", headers=headers)
        assert resp.status_code == 200
        rules = resp.json()["data"]
        if isinstance(rules, dict) and "items" in rules:
            assert rules["total"] >= 1
        elif isinstance(rules, list):
            assert len(rules) >= 1

        resp = client.delete(
            f"/compliance/rules/{rule_id}",
            headers=headers,
        )
        assert resp.status_code in (200, 204)


class TestAuditLogPagination:
    def test_audit_pagination(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}

        for i in range(3):
            resp = client.post(
                "/audit/logs",
                json={
                    "user_id": 1,
                    "action": f"page_test_{i}",
                    "entity_type": "test",
                    "entity_id": i,
                    "detail": f"Pagination test entry {i}",
                },
                headers=headers,
            )
            assert resp.status_code == 200

        resp = client.get(
            "/audit/logs?page=1&page_size=2",
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] >= 3
        assert len(data["items"]) <= 2


class TestComplianceDashboardRouter:
    def test_dashboard_summary(self, client, auth_token):
        resp = client.get(
            "/api/compliance/dashboard/summary",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "total_violations_today" in data

    def test_rep_violations(self, client, auth_token):
        resp = client.get(
            "/api/compliance/dashboard/reps/1",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "rep_id" in data
        assert "violations" in data

    def test_dashboard_auth_required(self, client):
        resp = client.get("/api/compliance/dashboard/summary")
        assert resp.status_code == 401

        resp = client.get("/api/compliance/dashboard/reps/1")
        assert resp.status_code == 401


class TestEnforcerRouter:
    def test_enforce_visit(self, client, auth_token):
        resp = client.post(
            "/api/compliance/enforce",
            json={
                "visit_data": {
                    "rep_id": 1,
                    "notes": "Regular checkup visit with no issues.",
                    "expenses": 100,
                }
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "violations" in data
        assert "passed" in data

    def test_list_rules(self, client, auth_token):
        resp = client.get(
            "/api/compliance/enforce/rules",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "rules" in data

    def test_enforce_auth_required(self, client):
        resp = client.post("/api/compliance/enforce", json={"visit_data": {}})
        assert resp.status_code == 401

        resp = client.get("/api/compliance/enforce/rules")
        assert resp.status_code == 401
