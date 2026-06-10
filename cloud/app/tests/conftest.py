import os
import sqlite3 as _sql
import uuid

import pytest
from starlette.testclient import TestClient

from shared.conftest_base import clean_test_tables, get_pg_url, is_pg, setup_test_db

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
TEST_DB = os.path.join(BASE_DIR, "data", "test_cloud.db")
TEST_RESEARCH_DB = os.path.join(BASE_DIR, "data", "test_research.db")
os.makedirs(os.path.dirname(TEST_DB), exist_ok=True)


@pytest.fixture(scope="session")
def app():
    import cloud.app.database as mod_db
    from cloud.app.schemas.ddl import SCHEMA_SQL

    setup_test_db(mod_db, SCHEMA_SQL, TEST_DB)
    with _sql.connect(TEST_DB) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS enforcement_log ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "rule_code TEXT, rule_name TEXT, severity TEXT, "
            "action TEXT, visit_data_json TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS research_enforcement_log ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "rule_code TEXT, rule_name TEXT, severity TEXT, "
            "action TEXT, visit_data_json TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS agent_execution_tasks ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "task_id TEXT UNIQUE, "
            "source TEXT DEFAULT 'internal', "
            "session_id TEXT DEFAULT '', "
            "agent_role TEXT DEFAULT '', "
            "action_type TEXT DEFAULT 'process', "
            "input_data TEXT DEFAULT '{}', "
            "output_data TEXT DEFAULT '{}', "
            "status TEXT DEFAULT 'pending', "
            "retry_count INTEGER DEFAULT 0, "
            "max_retries INTEGER DEFAULT 3, "
            "result_verified INTEGER DEFAULT 0, "
            "verification_detail TEXT DEFAULT '', "
            "requires_human_approval INTEGER DEFAULT 0, "
            "assigned_to TEXT DEFAULT '', "
            "created_at TEXT DEFAULT CURRENT_TIMESTAMP, "
            "completed_at TEXT, "
            "duration_ms INTEGER DEFAULT 0"
            ")"
        )
        conn.commit()
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
                pass  # 兼容操作：列已存在时跳过

    os.environ["RATE_LIMIT_DISABLE"] = "1"

    import cloud.app.services.agent_execution_service as aes

    aes.DB_PATH = TEST_DB

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
        import psycopg

        pg_url = get_pg_url(TEST_DB)
        conn = psycopg.connect(pg_url)
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
    "user_team",
    "teams",
    "notifications",
    "notification_templates",
    "audit_logs",
    "board_tasks",
    "task_boards",
    "contents",
    "compliance_rules",
    "users",
    "enforcement_log",
]


@pytest.fixture(autouse=True)
def _clean_tables():
    yield
    clean_test_tables(TABLES)
