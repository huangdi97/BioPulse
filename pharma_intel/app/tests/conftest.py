import os

import pytest
from starlette.testclient import TestClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
TEST_DB = os.path.join(BASE_DIR, "data", "test_pharma_intel.db")
os.makedirs(os.path.dirname(TEST_DB), exist_ok=True)


@pytest.fixture(scope="session")
def app():
    import pharma_intel.app.database as mod_db

    mod_db.DB_PATH = TEST_DB

    from pharma_intel.app.main import app as _app

    return _app


@pytest.fixture
def client(app):
    with TestClient(app) as c:
        yield c
