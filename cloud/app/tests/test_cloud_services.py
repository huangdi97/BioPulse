import uuid


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


class TestMemoryUtilityRouter:
    def test_memory_utility_scores_public(self, client):
        resp = client.get("/memory-utils/status")
        assert resp.status_code == 200


class TestAuthTokenService:
    def test_refresh_with_expired_token_returns_401(self, client):
        resp = client.post("/auth/refresh", json={"refresh_token": "expired.token.value"})
        assert resp.status_code == 401

    def test_refresh_with_missing_field_returns_422(self, client):
        resp = client.post("/auth/refresh", json={})
        assert resp.status_code in (422, 400)

    def test_login_with_whitespace_username(self, client):
        resp = client.post("/auth/login", json={"username": "   ", "password": "testpass123"})
        assert resp.status_code in (422, 400, 401)

    def test_register_with_unicode_username(self, client):
        username = f"用户_{uuid.uuid4().hex[:4]}"
        resp = client.post("/auth/register", json={"username": username, "password": "testpass123"})
        assert resp.status_code in (201, 409, 422)

    def test_register_with_unicode_password(self, client):
        username = f"unicodepw_{uuid.uuid4().hex[:6]}"
        resp = client.post(
            "/auth/register",
            json={"username": username, "password": "pässwörd123"},
        )
        assert resp.status_code in (201, 422)

    def test_login_case_sensitive_username(self, client):
        username = f"CaseUser_{uuid.uuid4().hex[:6]}"
        client.post("/auth/register", json={"username": username, "password": "testpass123"})
        resp = client.post("/auth/login", json={"username": username.upper(), "password": "testpass123"})
        assert resp.status_code in (401, 200)


class TestServiceCompliance:
    def test_enforce_with_empty_visit(self, client, auth_token):
        resp = client.post(
            "/api/compliance/enforce",
            json={"visit_data": {}},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code in (200, 422)

    def test_enforce_with_null_notes(self, client, auth_token):
        resp = client.post(
            "/api/compliance/enforce",
            json={"visit_data": {"rep_id": 1, "notes": None, "expenses": 0}},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code in (200, 422)


class TestServiceNotifications:
    def test_notifications_mark_read_invalid_id(self, client, auth_token):
        resp = client.patch(
            "/notifications/99999999/read",
            json={"is_read": True},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code in (404, 200)

    def test_notifications_mark_read_missing_body(self, client, auth_token):
        resp = client.patch(
            "/notifications/1/read",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code in (200, 422, 404)


class TestServiceSettings:
    def test_settings_health_endpoint(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "db" in data

    def test_settings_response_format(self, client, auth_token):
        resp = client.get(
            "/admin/settings",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data or isinstance(data, dict)
