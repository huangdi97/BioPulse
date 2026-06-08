class TestPapers:
    def test_search_papers_returns_list(self, client):
        resp = client.get("/api/intel/papers")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert "items" in data["data"]
        assert isinstance(data["data"]["items"], list)

    def test_search_papers_by_keyword(self, client):
        resp = client.get("/api/intel/papers", params={"q": "PD-1"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0


class TestPI:
    def test_search_pi_returns_list(self, client):
        resp = client.get("/api/intel/pi")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert "items" in data["data"]


class TestTargets:
    def test_list_categories(self, client):
        resp = client.get("/api/intel/targets/categories")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0

    def test_list_targets_with_filter(self, client):
        resp = client.get("/api/intel/targets", params={"category": "Immuno-Oncology"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
