import os

import pytest
from starlette.testclient import TestClient

from shared.conftest_base import clean_test_tables, setup_test_db

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


TABLES = ["role_cache", "view_preferences", "management_config"]


@pytest.fixture(autouse=True)
def _clean_tables():
    yield
    clean_test_tables(TABLES)
