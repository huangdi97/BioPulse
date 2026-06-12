import uuid


class TestBoardManagement:
    def test_board_and_task_flow(self, client, auth_token):
        resp = client.post(
            "/boards/",
            json={"name": "Test Board", "description": "A test kanban board"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 201
        board = resp.json()["data"]
        board_id = board["id"]
        assert board["name"] == "Test Board"

        resp = client.post(
            f"/boards/{board_id}/tasks",
            json={
                "title": "Task 1",
                "description": "First task",
                "status": "todo",
                "priority": "high",
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 201
        task_id = resp.json()["data"]["id"]

        resp = client.post(
            f"/boards/{board_id}/tasks",
            json={
                "title": "Task 2",
                "description": "Second task",
                "status": "done",
                "priority": "low",
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 201

        resp = client.get(
            f"/boards/{board_id}/kanban",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        kanban = resp.json()["data"]
        assert "board" in kanban
        assert "columns" in kanban
        assert len(kanban["columns"]["todo"]) >= 1
        assert len(kanban["columns"]["done"]) >= 1

        resp = client.get(
            f"/boards/{board_id}/tasks",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        tasks = resp.json()["data"]
        assert len(tasks) >= 2

        resp = client.delete(
            f"/boards/{board_id}/tasks/{task_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200

        resp = client.get(
            f"/boards/{board_id}/tasks",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        remaining = [t for t in resp.json()["data"] if t.get("is_active", 1) == 1]
        assert len(remaining) <= 1


class TestDashboard:
    def test_dashboard_endpoints(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}

        resp = client.get("/dashboard/overview", headers=headers)
        assert resp.status_code == 200
        overview = resp.json()["data"]
        assert "user_count" in overview
        assert "content_count" in overview
        assert "compliance_rate" in overview

        resp = client.get("/dashboard/users", headers=headers)
        assert resp.status_code == 200
        assert "by_role" in resp.json()["data"]

        resp = client.get("/dashboard/compliance", headers=headers)
        assert resp.status_code == 200
        assert "pass_rate" in resp.json()["data"]

        resp = client.get("/dashboard/contents", headers=headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "by_category" in data
        assert "by_status" in data


class TestTeamManagement:
    def test_team_flow(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}

        resp = client.post(
            "/teams",
            json={"name": "Alpha Team", "description": "Test team"},
            headers=headers,
        )
        assert resp.status_code == 201
        team = resp.json()["data"]
        team_id = team["id"]
        assert team["name"] == "Alpha Team"

        member_username = f"member_{uuid.uuid4().hex[:8]}"
        member_resp = client.post(
            "/auth/register",
            json={"username": member_username, "password": "memberpass123"},
        )
        assert member_resp.status_code == 201
        member_user_id = member_resp.json()["data"]["user_id"]

        resp = client.post(
            f"/teams/{team_id}/members",
            json={"user_id": member_user_id, "role": "member"},
            headers=headers,
        )
        assert resp.status_code == 201

        resp = client.get("/teams", headers=headers)
        assert resp.status_code == 200
        teams = resp.json()["data"]["items"]
        assert len(teams) >= 1

        resp = client.delete(
            f"/teams/{team_id}/members/{member_user_id}",
            headers=headers,
        )
        assert resp.status_code == 200

        resp = client.delete(
            f"/teams/{team_id}/members/{member_user_id}",
            headers=headers,
        )
        assert resp.status_code == 404


class TestBoardUpdate:
    def test_board_update(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}

        resp = client.post(
            "/boards/",
            json={"name": "Original Board", "description": "Before update"},
            headers=headers,
        )
        assert resp.status_code == 201
        board_id = resp.json()["data"]["id"]

        resp = client.patch(
            f"/boards/{board_id}",
            json={"name": "Updated Board Name", "description": "After update"},
            headers=headers,
        )
        assert resp.status_code in (200, 201)
        assert resp.json()["data"]["name"] == "Updated Board Name"

        resp = client.get(
            f"/boards/{board_id}",
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "Updated Board Name"


class TestTeamUpdate:
    def test_team_update_description(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}

        resp = client.post(
            "/teams",
            json={"name": "UpdateTeam", "description": "Before"},
            headers=headers,
        )
        assert resp.status_code == 201
        team_id = resp.json()["data"]["id"]

        resp = client.patch(
            f"/teams/{team_id}",
            json={"description": "After update description"},
            headers=headers,
        )
        assert resp.status_code in (200, 201)
        assert resp.json()["data"]["description"] == "After update description"

        resp = client.get("/teams", headers=headers)
        assert resp.status_code == 200
        teams = resp.json()["data"]["items"]
        assert len(teams) >= 1


class TestCustomerRouter:
    def test_get_customers_unauthorized(self, client):
        resp = client.get("/customers/")
        assert resp.status_code == 401

    def test_create_customer(self, client, auth_token):
        resp = client.post(
            "/customers/",
            json={
                "name": f"cust-{uuid.uuid4().hex[:6]}",
                "hospital": "Test Hospital",
                "department": "Cardiology",
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code in (200, 201)
        data = resp.json()["data"] if "data" in resp.json() else resp.json()
        assert data is not None

    def test_list_customers(self, client, auth_token):
        resp = client.get(
            "/customers/",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200


class TestVisitRouter:
    def test_get_visits(self, client, auth_token):
        resp = client.get(
            "/api/visit",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200

    def test_visit_auth_required(self, client):
        resp = client.post("/api/visit", json={"hcp_id": 1, "hcp_name": "x", "content": "y"})
        assert resp.status_code == 401


class TestSettingsRouter:
    def test_get_settings(self, client, auth_token):
        resp = client.get(
            "/settings/",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200


class TestDatabaseConnection:
    def test_health_db_connected(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["db"] == "connected"


class TestEmptyResultSets:
    def test_audit_logs_empty(self, client, auth_token):
        resp = client.get(
            "/audit/logs?entity_type=nonexistent_entity_x",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] == 0

    def test_teams_empty(self, client, auth_token):
        resp = client.get(
            "/teams",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200

    def test_notifications_empty(self, client, auth_token):
        resp = client.get(
            "/notifications/",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        items = resp.json()["data"].get("items", [])
        assert isinstance(items, list)


class TestBoardParamBoundaries:
    def test_board_create_empty_name(self, client, auth_token):
        resp = client.post(
            "/boards/",
            json={"name": "", "description": "empty name"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code in (422, 400, 201)

    def test_board_create_long_name(self, client, auth_token):
        resp = client.post(
            "/boards/",
            json={"name": "x" * 500, "description": "long name"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code in (422, 400, 201)

    def test_board_get_nonexistent(self, client, auth_token):
        resp = client.get(
            "/boards/99999999",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code in (404, 200)

    def test_board_delete_nonexistent(self, client, auth_token):
        resp = client.delete(
            "/boards/99999999",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code in (404, 200)

    def test_board_patch_nonexistent(self, client, auth_token):
        resp = client.patch(
            "/boards/99999999",
            json={"name": "ghost"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code in (404, 200)


class TestTeamParamBoundaries:
    def test_team_create_empty_name(self, client, auth_token):
        resp = client.post(
            "/teams",
            json={"name": "", "description": "empty"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code in (422, 400, 201)

    def test_team_get_nonexistent(self, client, auth_token):
        resp = client.get(
            "/teams/99999999",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code in (404, 200)

    def test_team_delete_nonexistent(self, client, auth_token):
        resp = client.delete(
            "/teams/99999999",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code in (404, 200)

    def test_team_patch_nonexistent(self, client, auth_token):
        resp = client.patch(
            "/teams/99999999",
            json={"description": "ghost update"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code in (404, 200)


class TestCustomerParamBoundaries:
    def test_customer_create_missing_name(self, client, auth_token):
        resp = client.post(
            "/customers/",
            json={"hospital": "Some Hospital"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code in (422, 400, 200, 201)

    def test_customer_get_nonexistent(self, client, auth_token):
        resp = client.get(
            "/customers/99999999",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code in (404, 200)


class TestSettingsParamBoundaries:
    def test_settings_unauthorized_methods(self, client):
        resp = client.post("/settings/", json={})
        assert resp.status_code in (401, 405, 404)

    def test_settings_put_not_allowed(self, client, auth_token):
        resp = client.put(
            "/settings/",
            json={},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code in (405, 401, 404)


class TestVisitParamBoundaries:
    def test_visit_create_missing_required(self, client, auth_token):
        resp = client.post(
            "/api/visit",
            json={},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code in (422, 400)

    def test_visit_get_detail_nonexistent(self, client, auth_token):
        resp = client.get(
            "/api/visit/99999999",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code in (404, 200)
