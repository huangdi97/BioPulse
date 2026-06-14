import importlib

from fastapi.testclient import TestClient


class TestImports:
    def test_import_main_ok(self):
        mod = importlib.import_module("clinical-ops.app.main")
        assert mod.app is not None

    def test_import_all_routers(self):
        sr = importlib.import_module("clinical-ops.app.site_router")
        rr = importlib.import_module("clinical-ops.app.recruitment_router")
        mr = importlib.import_module("clinical-ops.app.monitoring_router")
        mtr = importlib.import_module("clinical-ops.app.routers.milestone_tracker_router")
        mtr2 = importlib.import_module("clinical-ops.app.routers.monitor_task_router")
        assert all(hasattr(m, "router") for m in (sr, rr, mr, mtr, mtr2))


class TestHealthEndpoint:
    def test_health_returns_200(self):
        mod = importlib.import_module("clinical-ops.app.main")
        client = TestClient(mod.app)
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"

    def test_health_uptime_is_int(self):
        mod = importlib.import_module("clinical-ops.app.main")
        client = TestClient(mod.app)
        resp = client.get("/health")
        assert isinstance(resp.json()["uptime"], int)

    def test_root_router_endpoint_registered(self):
        mod = importlib.import_module("clinical-ops.app.main")
        routes = [r.path for r in mod.app.routes]
        assert "/api/sites/search" in routes
        assert "/api/recruitment/status" in routes
