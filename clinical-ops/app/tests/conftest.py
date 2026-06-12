import os
import sys
from pathlib import Path

import pytest
from starlette.testclient import TestClient

_root = Path(__file__).resolve().parent.parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
TEST_DB = os.path.join(BASE_DIR, "data", "test_clinical_ops.db")
os.makedirs(os.path.dirname(TEST_DB), exist_ok=True)


@pytest.fixture(scope="session")
def app():
    import importlib

    importlib.import_module("clinical-ops.app.database").init_cache_db()

    return importlib.import_module("clinical-ops.app.main").app


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
