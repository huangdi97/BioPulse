import uuid


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
        data["access_token"]
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


class TestAuthServiceEdgeCases:
    def test_register_username_too_short(self, client):
        resp = client.post("/auth/register", json={"username": "ab", "password": "testpass123"})
        assert resp.status_code in (409, 422)

    def test_register_password_too_short(self, client):
        resp = client.post("/auth/register", json={"username": "validuser123", "password": "12345"})
        assert resp.status_code in (409, 422)

    def test_register_duplicate_user(self, client):
        username = f"dup_{uuid.uuid4().hex[:8]}"
        client.post("/auth/register", json={"username": username, "password": "pass123456"})
        resp = client.post("/auth/register", json={"username": username, "password": "pass123456"})
        assert resp.status_code == 409

    def test_login_bad_password(self, client):
        username = f"badpw_{uuid.uuid4().hex[:8]}"
        client.post("/auth/register", json={"username": username, "password": "goodpass123"})
        resp = client.post("/auth/login", json={"username": username, "password": "wrongpass456"})
        assert resp.status_code == 401

    def test_login_disabled_account(self, client, admin_token):
        username = f"disabled_{uuid.uuid4().hex[:8]}"
        reg_resp = client.post("/auth/register", json={"username": username, "password": "CHANGE_ME"})
        user_id = reg_resp.json()["data"]["user_id"]
        client.patch(
            f"/users/{user_id}",
            json={"is_active": False},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        resp = client.post("/auth/login", json={"username": username, "password": "CHANGE_ME"})
        assert resp.status_code == 403

    def test_login_nonexistent_user(self, client):
        resp = client.post(
            "/auth/login",
            json={"username": "no__such__user__x", "password": "pass123456"},
        )
        assert resp.status_code == 401

    def test_refresh_invalid_token(self, client):
        resp = client.post("/auth/refresh", json={"refresh_token": "invalid-token-value"})
        assert resp.status_code == 401


class TestConfigRouter:
    def test_get_configs_unauthorized(self, client):
        resp = client.get("/admin/configs/")
        assert resp.status_code == 401

    def test_get_configs(self, client, auth_token):
        resp = client.get(
            "/admin/configs/",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code in (200, 422)


class TestHealthCheckEnhanced:
    def test_health_returns_db_uptime_version(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["db"] in ("connected", "ok")
        assert isinstance(data["uptime"], (int, float))
        assert isinstance(data["version"], str)


class TestDatabaseConnection:
    def test_health_db_connected(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["db"] == "connected"


class TestInvalidTokenFormat:
    def test_no_auth_header(self, client):
        resp = client.get("/admin/configs/")
        assert resp.status_code == 401

    def test_empty_bearer(self, client):
        resp = client.get(
            "/admin/configs/",
            headers={"Authorization": "Bearer "},
        )
        assert resp.status_code == 401

    def test_malformed_auth_header(self, client):
        resp = client.get(
            "/admin/configs/",
            headers={"Authorization": "NotBearer token"},
        )
        assert resp.status_code == 401
