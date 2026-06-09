import importlib

from fastapi.testclient import TestClient


class TestImports:
    def test_import_main_ok(self):
        mod = importlib.import_module("market-access.app.main")
        assert mod.app is not None

    def test_import_all_routers(self):
        br = importlib.import_module("market-access.app.bidding_router")
        fr = importlib.import_module("market-access.app.formulary_router")
        sr = importlib.import_module("market-access.app.strategy_router")
        par = importlib.import_module("market-access.app.routers.price_alert_router")
        pmr = importlib.import_module("market-access.app.routers.price_monitor_router")
        assert all(hasattr(m, "router") for m in (br, fr, sr, par, pmr))


class TestHealthEndpoint:
    def test_health_returns_200(self):
        mod = importlib.import_module("market-access.app.main")
        client = TestClient(mod.app)
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "market-access"

    def test_health_uptime_is_int(self):
        mod = importlib.import_module("market-access.app.main")
        client = TestClient(mod.app)
        resp = client.get("/health")
        assert isinstance(resp.json()["uptime"], int)

    def test_root_router_endpoint_registered(self):
        mod = importlib.import_module("market-access.app.main")
        routes = [r.path for r in mod.app.routes]
        assert "/api/bidding/price" in routes
        assert "/api/formulary/search" in routes
