import os

import pytest
from starlette.testclient import TestClient

from shared.conftest_base import clean_test_tables, setup_test_db

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
TEST_DB = os.path.join(BASE_DIR, "data", "test_sales_assistant.db")
os.makedirs(os.path.dirname(TEST_DB), exist_ok=True)


@pytest.fixture(scope="session")
def app():
    import sales_assistant.app.database as mod_db

    setup_test_db(mod_db, mod_db.SCHEMA_SQL, TEST_DB)

    from sales_assistant.app.main import app as _app

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
    "hcp_product_relation",
    "product",
    "strategy_simulation",
    "content_library",
    "meeting_note",
    "schedule",
    "hcp",
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
