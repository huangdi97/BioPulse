import os
import sqlite3
import sys
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from shared.conftest_base import clean_test_tables, is_pg, setup_test_db

_root = Path(__file__).resolve().parent.parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
TEST_DB = os.path.join(BASE_DIR, "data", "test_opportunity.db")
os.makedirs(os.path.dirname(TEST_DB), exist_ok=True)


@pytest.fixture(scope="session")
def app():
    import opportunity.app.database as mod_db

    setup_test_db(mod_db, mod_db.SCHEMA_SQL, TEST_DB)

    if not is_pg():
        conn = sqlite3.connect(TEST_DB)
        try:
            conn.execute("ALTER TABLE opportunity ADD COLUMN heat_score INTEGER DEFAULT 0")
            conn.commit()
        except sqlite3.OperationalError:
            pass
        conn.close()

    from opportunity.app.main import app as _app

    return _app


@pytest.fixture
def client(app):
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_token():
    from shared.auth import create_access_token

    return create_access_token(1, "user")


@pytest.fixture
def db_path():
    return TEST_DB


TABLES = [
    "bidding_agent_log",
    "bidding_agent_config",
    "trend_analysis",
    "paper_integrity",
    "user_bookmark",
    "research_trail",
    "bidding_info",
    "contact_record",
    "opportunity",
]


@pytest.fixture(autouse=True)
def _clean_tables():
    yield
    clean_test_tables(TABLES)


@pytest.fixture(autouse=True)
def _disable_rate_limiter(monkeypatch):
    from shared.rate_limiter import RateLimiterMiddleware

    async def passthrough(self, request, call_next):
        return await call_next(request)

    monkeypatch.setattr(RateLimiterMiddleware, "dispatch", passthrough)
    yield
