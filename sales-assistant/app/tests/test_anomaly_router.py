class TestAnomalyRouter:
    def test_create_rule(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = client.post(
            "/anomaly/rules",
            json={
                "rule_name": "test_rule",
                "metric": "visit_count",
                "operator": "lt",
                "threshold": 5.0,
                "severity": "medium",
            },
            headers=headers,
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["id"] is not None

    def test_list_rules(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = client.get("/anomaly/rules", headers=headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "items" in data

    def test_check_anomalies(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = client.post("/anomaly/check", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
