import uuid
from datetime import datetime, timedelta, timezone

from jose import jwt

from shared.auth import ALGORITHM, SECRET_KEY, create_access_token


def _get_token(client, scope):
    username = f"scope_{scope}_{uuid.uuid4().hex[:8]}"
    resp = client.post("/auth/register", json={"username": username, "password": "testpass123"})
    assert resp.status_code == 201
    user_id = resp.json()["data"]["user_id"]
    return create_access_token(user_id, "rep", scope)


class TestScopeIsolation:
    def test_visit_token_blocked_from_research(self, client):
        token = _get_token(client, "visit")
        resp = client.get(
            "/api/research/pi/search?q=test",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    def test_research_token_allowed_on_research(self, client):
        token = _get_token(client, "research")
        resp = client.get(
            "/api/research/pi/search?q=test",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200

    def test_boundary_missing_scope_token(self, client):
        old_token = jwt.encode(
            {
                "sub": "1",
                "role": "rep",
                "type": "access",
                "exp": datetime.now(timezone.utc) + timedelta(hours=1),
                "iat": datetime.now(timezone.utc),
            },
            SECRET_KEY,
            algorithm=ALGORITHM,
        )
        resp = client.get(
            "/api/research/pi/search?q=test",
            headers={"Authorization": f"Bearer {old_token}"},
        )
        assert resp.status_code == 403

    def test_research_compliance_uses_separate_db(self, client):
        token = _get_token(client, "research")
        resp = client.post(
            "/api/research/compliance/enforce",
            json={"visit_data": {"notes": "学术交流", "expenses": 0}},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert not data["passed"]
        rule_codes = [v["rule_code"] for v in data["violations"]]
        for code in rule_codes:
            assert code.startswith("RSR-"), f"Expected research rules (RSR-), got {code}"
