import os
import uuid

import pytest
from starlette.testclient import TestClient

from shared.conftest_base import is_pg, get_pg_url, setup_test_db, clean_test_tables

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
TEST_DB = os.path.join(BASE_DIR, "data", "test_cloud.db")
TEST_RESEARCH_DB = os.path.join(BASE_DIR, "data", "test_research.db")
os.makedirs(os.path.dirname(TEST_DB), exist_ok=True)


@pytest.fixture(scope="session")
def app():
    import cloud.app.database as mod_db
    from cloud.app.schema import SCHEMA_SQL
    setup_test_db(mod_db, SCHEMA_SQL, TEST_DB)
    import cloud.app.research_database as mod_research
    mod_research.set_test_research_db_path(TEST_RESEARCH_DB)
    mod_research.init_research_db()

    if not is_pg():
        import sqlite3
        with sqlite3.connect(TEST_DB) as conn:
            conn.row_factory = sqlite3.Row
            try:
                conn.execute("ALTER TABLE users ADD COLUMN updated_at TEXT")
                conn.commit()
            except sqlite3.OperationalError:
                pass

    import cloud.app.main as mod_main
    mod_main.DB_PATH = TEST_DB

    from cloud.app.main import app as _app
    return _app


@pytest.fixture
def client(app):
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db_path():
    return TEST_DB


def _register_and_login(client, username, password):
    resp = client.post("/auth/register", json={"username": username, "password": password})
    assert resp.status_code == 201, resp.text
    resp = client.post("/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]["access_token"]


@pytest.fixture
def auth_token(client):
    username = f"testuser_{uuid.uuid4().hex[:8]}"
    return _register_and_login(client, username, "testpass123")


@pytest.fixture
def admin_token(client):
    from shared.auth import hash_password

    username = f"admin_{uuid.uuid4().hex[:8]}"
    password = "CHANGE_ME"
    hashed = hash_password(password)

    if is_pg():
        import psycopg2
        from psycopg2.extras import RealDictCursor
        pg_url = get_pg_url(TEST_DB)
        conn = psycopg2.connect(pg_url, cursor_factory=RealDictCursor)
        conn.autocommit = True
        conn.cursor().execute(
            "INSERT INTO users (username, hashed_password, role) VALUES (%s, %s, %s)",
            (username, hashed, "admin"),
        )
        conn.close()
    else:
        import sqlite3
        with sqlite3.connect(TEST_DB) as conn:
            conn.execute(
                "INSERT INTO users (username, hashed_password, role) VALUES (?, ?, ?)",
                (username, hashed, "admin"),
            )
            conn.commit()

    resp = client.post("/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]["access_token"]


TABLES = [
    "user_team", "teams", "notifications", "notification_templates",
    "audit_logs", "board_tasks", "task_boards", "contents",
    "compliance_rules", "users", "enforcement_log",
]


@pytest.fixture(autouse=True)
def _clean_tables():
    yield
    clean_test_tables(TABLES)


@pytest.fixture(autouse=True)
def _reset_rate_limiter(monkeypatch):
    from shared.rate_limiter import RateLimiterMiddleware

    async def passthrough(self, request, call_next):
        return await call_next(request)

    monkeypatch.setattr(RateLimiterMiddleware, "dispatch", passthrough)
    yield
