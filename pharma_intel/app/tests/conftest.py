import os
import sys
from pathlib import Path

import pytest
from starlette.testclient import TestClient

_root = Path(__file__).resolve().parent.parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

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
def auth_token():
    from shared.auth import create_access_token

    return create_access_token(user_id=1)


@pytest.fixture(autouse=True)
def _override_auth(app, auth_token):
    from shared.auth import get_current_user

    app.dependency_overrides[get_current_user] = lambda: {"user_id": 1}
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client(app):
    with TestClient(app) as c:
        yield c
