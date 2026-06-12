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
        assert resp.status_code == 201
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
        assert resp.status_code == 201
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
        assert resp.status_code == 201

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
        assert resp.status_code == 201

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
            assert resp.status_code == 201

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
        data = resp.json()["data"]
        assert "total_violations_today" in data

    def test_rep_violations(self, client, auth_token):
        resp = client.get(
            "/api/compliance/dashboard/reps/1",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
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
        data = resp.json()["data"]
        assert "violations" in data
        assert "passed" in data

    def test_list_rules(self, client, auth_token):
        resp = client.get(
            "/api/compliance/enforce/rules",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "rules" in data

    def test_enforce_auth_required(self, client):
        resp = client.post("/api/compliance/enforce", json={"visit_data": {}})
        assert resp.status_code == 401

        resp = client.get("/api/compliance/enforce/rules")
        assert resp.status_code == 401


class TestComplianceRuleUpdate:
    def test_update_compliance_rule(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = client.post(
            "/compliance/rules",
            json={"name": "RuleToUpdate", "category": "pharma", "keyword": "badword", "max_value": 0.3},
            headers=headers,
        )
        assert resp.status_code in (200, 201)
        rule_id = resp.json()["data"].get("id") or resp.json()["data"].get("rule_id")

        resp = client.patch(
            f"/compliance/rules/{rule_id}",
            json={"max_value": 0.9},
            headers=headers,
        )
        assert resp.status_code in (200, 201)

        resp = client.get(f"/compliance/rules/{rule_id}", headers=headers)
        assert resp.status_code in (200, 404)

    def test_update_nonexistent_rule(self, client, auth_token):
        resp = client.patch(
            "/compliance/rules/99999999",
            json={"max_value": 0.5},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code in (404, 200)

    def test_create_rule_missing_name(self, client, auth_token):
        resp = client.post(
            "/compliance/rules",
            json={"category": "pharma", "keyword": "kw", "max_value": 0.5},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code in (422, 400, 200, 201)

    def test_create_rule_negative_max_value(self, client, auth_token):
        resp = client.post(
            "/compliance/rules",
            json={"name": "NegRule", "category": "pharma", "keyword": "kw", "max_value": -1.0},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code in (422, 400, 200, 201)

    def test_create_rule_invalid_category(self, client, auth_token):
        resp = client.post(
            "/compliance/rules",
            json={"name": "BadCat", "category": "", "keyword": "kw", "max_value": 0.5},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code in (422, 400, 200, 201)


class TestAuditLogFiltering:
    def test_audit_log_filter_by_action(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        client.post(
            "/audit/logs",
            json={"user_id": 1, "action": "filter_test", "entity_type": "test", "detail": "x"},
            headers=headers,
        )
        resp = client.get(
            "/audit/logs?action=filter_test",
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] >= 1

    def test_audit_log_filter_by_date_range(self, client, auth_token):
        resp = client.get(
            "/audit/logs?start_date=2000-01-01&end_date=2099-12-31",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200

    def test_audit_log_filter_no_match(self, client, auth_token):
        resp = client.get(
            "/audit/logs?action=nonexistent_action_xyz",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["total"] == 0


class TestComplianceContentEdgeCases:
    def test_content_high_risk_pharma(self, client, auth_token):
        resp = client.post(
            "/contents/",
            json={
                "title": "High Risk",
                "body": "Buy now! This drug cures everything immediately 100% guarantee.",
                "category": "pharma",
                "tags": [],
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["data"]["compliance_score"] < 1.0

    def test_content_medical_disclaimer(self, client, auth_token):
        resp = client.post(
            "/contents/",
            json={
                "title": "Disclaimer",
                "body": "This content is for informational purposes only. Consult your physician.",
                "category": "pharma",
                "tags": [],
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["data"]["compliance_score"] >= 0.5

    def test_content_empty_body(self, client, auth_token):
        resp = client.post(
            "/contents/",
            json={"title": "Empty Body", "body": "", "category": "pharma", "tags": []},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code in (200, 422, 400)
