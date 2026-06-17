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

    def test_pi_endpoint_works_with_auth(self, client):
        resp = client.get("/api/intel/pi")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0

    def test_targets_categories_works_with_auth(self, client):
        resp = client.get("/api/intel/targets/categories")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0

    def test_search_papers_works_with_auth(self, client):
        resp = client.get("/api/intel/papers", params={"q": "zzz_no_results_xxxx"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert "items" in data["data"]


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


class TestMisc:
    def test_trending_endpoint_returns_ok(self, client):
        from shared.auth import create_access_token

        token = create_access_token(user_id=1)
        resp = client.get(
            "/api/v1/kol/trending",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
