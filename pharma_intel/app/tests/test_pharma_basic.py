from pharma_intel.app.database import set_cache


class TestKOL:
    def test_trending_kols_returns_ok(self, client):
        resp = client.get("/api/v1/api/kol/trending")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0


class TestPipeline:
    def test_trending_pipelines_returns_ok(self, client):
        resp = client.get("/api/v1/api/pipeline/trending")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0


class TestCompetitor:
    def test_market_news_returns_list(self, client):
        set_cache(
            "market:news:limit:10",
            {"total_news": 0, "news": [], "last_updated": "2026-06-08T00:00:00+00:00"},
            ttl=1800,
        )
        resp = client.get("/api/v1/api/competitor/news")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
