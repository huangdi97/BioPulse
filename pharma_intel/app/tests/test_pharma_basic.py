class TestKOL:
    def test_trending_kols_returns_ok(self, client):
        resp = client.get("/api/v1/kol/trending")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0


class TestPipeline:
    def test_trending_pipelines_returns_ok(self, client):
        resp = client.get("/api/v1/pipeline/trending")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0


class TestCompetitor:
    def test_market_news_returns_list(self, client):
        resp = client.get("/api/v1/competitor/news")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
