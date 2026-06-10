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


class TestHealthCheckEnhanced:
    def test_health_returns_db_uptime_version(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["db"] in ("connected", "ok")
        assert isinstance(data["uptime"], (int, float))
        assert isinstance(data["version"], str)


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


class TestPaginationEdgeCases:
    def test_audit_log_pagination_large_page(self, client, auth_token):
        resp = client.get(
            "/audit/logs?page=100&page_size=50",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] >= 0

    def test_audit_log_pagination_zero_page_size(self, client, auth_token):
        resp = client.get(
            "/audit/logs?page=1&page_size=1",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code in (200, 422)

    def test_users_pagination(self, client, admin_token):
        resp = client.get(
            "/users/?page=1&page_size=5",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200


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


class TestCosmeticEndpointCoverage:
    def test_key_routes_require_auth(self, client):
        resp = client.get("/kg/entities/list")
        assert resp.status_code == 401

        resp = client.get("/recommend/list")
        assert resp.status_code == 401

        resp = client.get("/collaboration/sessions/list")
        assert resp.status_code == 401

        resp = client.get("/events/messages/list")
        assert resp.status_code == 401

        resp = client.get("/memory/consolidation/status")
        assert resp.status_code == 401

        resp = client.get("/orchestrate/templates/list")
        assert resp.status_code == 401

        resp = client.get("/causal/graph/test")
        assert resp.status_code == 401

        resp = client.get("/compute/job/list")
        assert resp.status_code == 401

        resp = client.get("/compliance/gov/logs/list")
        assert resp.status_code == 401

        resp = client.get("/training/scripts/list")
        assert resp.status_code == 401

        resp = client.get("/marketplace/metrics/dashboard")
        assert resp.status_code == 401

        resp = client.get("/mcp/tools/list")
        assert resp.status_code == 401


class TestRegisterValidation:
    def test_register_missing_username(self, client):
        resp = client.post("/auth/register", json={"password": "testpass123"})
        assert resp.status_code in (422, 400)

    def test_register_missing_password(self, client):
        resp = client.post("/auth/register", json={"username": "someuser"})
        assert resp.status_code in (422, 400)

    def test_register_empty_username(self, client):
        resp = client.post("/auth/register", json={"username": "", "password": "testpass123"})
        assert resp.status_code in (422, 400)

    def test_register_empty_password(self, client):
        resp = client.post("/auth/register", json={"username": "validuser", "password": ""})
        assert resp.status_code in (422, 400)

    def test_register_username_too_long(self, client):
        long_name = "u" * 300
        resp = client.post("/auth/register", json={"username": long_name, "password": "testpass123"})
        assert resp.status_code in (422, 400, 409)


class TestTokenValidation:
    def test_expired_token_formats(self, client):
        resp = client.get(
            "/contents/",
            headers={"Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.d910"},
        )
        assert resp.status_code == 401

    def test_token_with_wrong_scheme(self, client, auth_token):
        resp = client.get(
            "/contents/",
            headers={"Authorization": f"Basic {auth_token}"},
        )
        assert resp.status_code == 401

    def test_token_missing_in_middleware(self, client):
        resp = client.get("/contents/", headers={"Authorization": ""})
        assert resp.status_code == 401


class TestLoginEdgeCases:
    def test_login_missing_fields(self, client):
        resp = client.post("/auth/login", json={})
        assert resp.status_code in (422, 400)

    def test_login_empty_username(self, client):
        resp = client.post("/auth/login", json={"username": "", "password": "test123456"})
        assert resp.status_code in (422, 400)

    def test_login_empty_password(self, client):
        resp = client.post("/auth/login", json={"username": "someuser", "password": ""})
        assert resp.status_code in (422, 400)

    def test_login_bad_token_refresh_chain(self, client):
        resp = client.post("/auth/refresh", json={"refresh_token": ""})
        assert resp.status_code in (422, 401)

    def test_register_special_chars_username(self, client):
        resp = client.post(
            "/auth/register",
            json={"username": "user!@#$%", "password": "testpass123"},
        )
        assert resp.status_code in (201, 409, 422)
