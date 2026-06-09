import importlib

from fastapi.testclient import TestClient


class TestImports:
    def test_import_main_ok(self):
        mod = importlib.import_module("patient-engage.app.main")
        assert mod.app is not None

    def test_import_all_routers(self):
        er = importlib.import_module("patient-engage.app.education_router")
        rr = importlib.import_module("patient-engage.app.reminder_router")
        fr = importlib.import_module("patient-engage.app.followup_router")
        gr = importlib.import_module("patient-engage.app.routers.gamification_router")
        pwr = importlib.import_module("patient-engage.app.routers.patient_weapp_router")
        assert all(hasattr(m, "router") for m in (er, rr, fr, gr, pwr))


class TestHealthEndpoint:
    def test_health_returns_200(self):
        mod = importlib.import_module("patient-engage.app.main")
        client = TestClient(mod.app)
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "patient-engage"

    def test_health_uptime_is_int(self):
        mod = importlib.import_module("patient-engage.app.main")
        client = TestClient(mod.app)
        resp = client.get("/health")
        assert isinstance(resp.json()["uptime"], int)

    def test_root_router_endpoint_registered(self):
        mod = importlib.import_module("patient-engage.app.main")
        routes = [r.path for r in mod.app.routes]
        assert "/api/education/content" in routes
        assert "/api/reminder/status" in routes
