import uuid


class TestContentCRUD:
    def test_content_crud(self, client, auth_token):
        resp = client.post(
            "/contents/",
            json={
                "title": "Test Content",
                "body": "This is a normal medical content without any prohibited words.",
                "category": "medical",
                "tags": ["tag1", "tag2"],
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        content_id = data["id"]
        assert data["title"] == "Test Content"
        assert data["category"] == "medical"

        resp = client.get(
            f"/contents/{content_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["id"] == content_id

        resp = client.get(
            "/contents/",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        items = resp.json()["data"]["items"]
        assert len(items) >= 1


class TestContentUpdateDelete:
    def test_content_update(self, client, auth_token):
        resp = client.post(
            "/contents/",
            json={
                "title": "Original Title",
                "body": "Original body content for testing.",
                "category": "medical",
                "tags": ["test"],
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        content_id = resp.json()["data"]["id"]

        resp = client.patch(
            f"/contents/{content_id}",
            json={"title": "Updated Title", "body": "Updated body content."},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["title"] == "Updated Title"

        resp = client.get(
            f"/contents/{content_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["title"] == "Updated Title"
        assert resp.json()["data"]["body"] == "Updated body content."

    def test_content_soft_delete(self, client, auth_token):
        resp = client.post(
            "/contents/",
            json={
                "title": "To Delete",
                "body": "Will be soft deleted.",
                "category": "pharma",
                "tags": [],
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        content_id = resp.json()["data"]["id"]

        resp = client.delete(
            f"/contents/{content_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code in (200, 204)

        resp = client.get(
            f"/contents/{content_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, dict) and "data" in data:
                item = data["data"]
                if item and isinstance(item, dict) and "is_active" in item:
                    assert item["is_active"] in (0, False, None)


class TestNotificationSystem:
    def test_notification_flow(self, client, auth_token):
        recipient_username = f"notifuser_{uuid.uuid4().hex[:8]}"
        recipient_password = "CHANGE_ME"
        resp = client.post(
            "/auth/register",
            json={"username": recipient_username, "password": recipient_password},
        )
        assert resp.status_code == 201
        recipient_id = resp.json()["data"]["user_id"]

        resp = client.post(
            "/auth/login",
            json={"username": recipient_username, "password": recipient_password},
        )
        assert resp.status_code == 200
        recipient_token = resp.json()["data"]["access_token"]

        resp = client.post(
            "/notifications/templates",
            json={
                "name": "test_template",
                "title_template": "Hello {name}",
                "body_template": "You have {count} new messages.",
                "category": "system",
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 201
        template = resp.json()["data"]
        assert template["name"] == "test_template"

        resp = client.post(
            "/notifications/send",
            json={
                "user_id": recipient_id,
                "template_name": "test_template",
                "context": {"name": "World", "count": "5"},
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 201
        notif = resp.json()["data"]
        assert notif["title"] == "Hello World"
        assert notif["body"] == "You have 5 new messages."
        notif_id = notif["id"]

        resp = client.get(
            "/notifications/",
            headers={"Authorization": f"Bearer {recipient_token}"},
        )
        assert resp.status_code == 200
        items = resp.json()["data"]["items"]
        assert len(items) >= 1

        resp = client.patch(
            f"/notifications/{notif_id}/read",
            headers={"Authorization": f"Bearer {recipient_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["is_read"] == 1

        resp = client.get(
            "/notifications/unread-count",
            headers={"Authorization": f"Bearer {recipient_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["count"] == 0


class TestNotificationTemplateCRUD:
    def test_template_update(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}

        resp = client.post(
            "/notifications/templates",
            json={
                "name": f"tpl_{uuid.uuid4().hex[:8]}",
                "title_template": "Meeting with {doctor}",
                "body_template": "Schedule: {time}",
                "category": "reminder",
            },
            headers=headers,
        )
        assert resp.status_code == 201
        template = resp.json()["data"]
        template_id = template["id"]

        resp = client.patch(
            f"/notifications/templates/{template_id}",
            json={"title_template": "Updated: {doctor} call"},
            headers=headers,
        )
        assert resp.status_code in (200, 201)

        resp = client.get(
            "/notifications/templates",
            headers=headers,
        )
        assert resp.status_code == 200
        templates = resp.json()["data"]
        if isinstance(templates, dict) and "items" in templates:
            assert templates["total"] >= 1


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
            "/visit/",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200

    def test_visit_auth_required(self, client):
        resp = client.post("/visit", json={"hcp_id": 1, "hcp_name": "x", "content": "y"})
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
