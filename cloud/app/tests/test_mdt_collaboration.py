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


class TestTokenBudgetRouter:
    def test_get_token_budget(self, client, auth_token):
        resp = client.get(
            "/token-budget/status",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code in (200, 404)
