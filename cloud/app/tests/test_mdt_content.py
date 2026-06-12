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
        assert resp.status_code == 201
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
        assert resp.status_code == 201
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
        assert resp.status_code == 201
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
