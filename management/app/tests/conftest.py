import os
import sys
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from shared.conftest_base import clean_test_tables, setup_test_db

_root = Path(__file__).resolve().parent.parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
TEST_DB = os.path.join(BASE_DIR, "data", "test_management.db")
os.makedirs(os.path.dirname(TEST_DB), exist_ok=True)


@pytest.fixture(scope="session")
def app():
    import management.app.database as mod_db

    setup_test_db(mod_db, mod_db.SCHEMA, TEST_DB)

    from management.app.main import app as _app

    return _app


@pytest.fixture
def client(app):
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_token():
    from shared.auth import create_access_token

    return create_access_token(1, "user")


@pytest.fixture(autouse=True)
def _mock_dashboard_fetch(monkeypatch):
    """Mock external _fetch calls so tests don't hit real cloud API."""

    async def mock_fetch(path: str) -> dict:
        return {"mock": True, "path": path}

    monkeypatch.setattr("management.app.management_dashboard_router._fetch", mock_fetch)


TABLES = ["role_cache", "view_preferences", "management_config"]


@pytest.fixture(autouse=True)
def _clean_tables():
    yield
    clean_test_tables(TABLES)
