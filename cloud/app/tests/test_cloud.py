import uuid
import pytest


class TestAuthFlow:
    def test_register_login_refresh_me(self, client):
        username = f"authuser_{uuid.uuid4().hex[:8]}"
        password = "CHANGE_ME"

        resp = client.post("/auth/register", json={"username": username, "password": password})
        assert resp.status_code == 201
        assert resp.json()["data"]["username"] == username

        resp = client.post("/auth/login", json={"username": username, "password": password})
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        access_token = data["access_token"]
        refresh_token = data["refresh_token"]

        resp = client.post("/auth/refresh", json={"refresh_token": refresh_token})
        assert resp.status_code == 200
        new_data = resp.json()["data"]
        assert "access_token" in new_data
        assert new_data["token_type"] == "bearer"
        new_access_token = new_data["access_token"]

        resp = client.get(
            "/notifications/unread-count",
            headers={"Authorization": f"Bearer {new_access_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["count"] == 0


class TestUserCRUD:
    def test_user_crud_flow(self, client, admin_token):
        username = f"cruduser_{uuid.uuid4().hex[:8]}"

        resp = client.post("/auth/register", json={"username": username, "password": "crudpass123"})
        assert resp.status_code == 201
        user_id = resp.json()["data"]["user_id"]

        resp = client.get(
            f"/users/{user_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["username"] == username

        resp = client.patch(
            f"/users/{user_id}",
            json={"is_active": False},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200

        resp = client.get(
            "/users/",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        users = resp.json()["data"]
        assert len(users) >= 1

        another = f"deleteuser_{uuid.uuid4().hex[:8]}"
        resp = client.post("/auth/register", json={"username": another, "password": "delpass123"})
        assert resp.status_code == 201
        del_id = resp.json()["data"]["user_id"]

        resp = client.delete(
            f"/users/{del_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200

        resp = client.get(
            f"/users/{del_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["is_active"] is False


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


class TestAuthRequired:
    def test_unauthorized_returns_401(self, client):
        resp = client.get("/contents/")
        assert resp.status_code == 401

        resp = client.get("/users/")
        assert resp.status_code == 401

        resp = client.post("/audit/logs", json={"user_id": 1, "action": "x", "entity_type": "x"})
        assert resp.status_code == 401

    def test_non_admin_returns_403(self, client, auth_token):
        resp = client.get(
            "/users/",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 403

        resp = client.get(
            "/users/1",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 403

    def test_invalid_token_returns_401(self, client):
        resp = client.get(
            "/contents/",
            headers={"Authorization": "Bearer invalidtoken123"},
        )
        assert resp.status_code == 401

    def test_health_does_not_require_auth(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "db" in data
        assert "uptime" in data
        assert "version" in data


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


class TestHealthCheckEnhanced:
    def test_health_returns_db_uptime_version(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["db"] in ("connected", "ok")
        assert isinstance(data["uptime"], (int, float))
        assert isinstance(data["version"], str)
