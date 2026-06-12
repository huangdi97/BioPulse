import uuid

import pytest

from shared.auth import create_access_token


@pytest.fixture
def research_token(client):
    username = f"research_{uuid.uuid4().hex[:8]}"
    resp = client.post("/auth/register", json={"username": username, "password": "testpass123"})
    assert resp.status_code == 201
    user_id = resp.json()["data"]["user_id"]
    return create_access_token(user_id, "rep", "research")


class TestPiRouter:
    def test_search_pi(self, client, research_token):
        resp = client.get(
            "/api/pi/search?q=test",
            headers={"Authorization": f"Bearer {research_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["code"] == 0

    def test_search_pi_empty_query(self, client, research_token):
        resp = client.get(
            "/api/pi/search?q=",
            headers={"Authorization": f"Bearer {research_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["code"] == 0
        assert isinstance(resp.json()["data"], list)

    def test_create_pi(self, client, research_token):
        resp = client.post(
            "/api/pi",
            json={
                "name": "Dr. Test PI",
                "institution": "Test University",
                "department": "Immunology",
                "title": "Professor",
                "research_areas": ["oncology", "immunotherapy"],
                "total_papers": 45,
                "h_index": 18,
            },
            headers={"Authorization": f"Bearer {research_token}"},
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["name"] == "Dr. Test PI"
        assert data["institution"] == "Test University"

    def test_get_pi(self, client, research_token):
        create_resp = client.post(
            "/api/pi",
            json={
                "name": "Dr. Get Test",
                "institution": "Get University",
            },
            headers={"Authorization": f"Bearer {research_token}"},
        )
        pi_id = create_resp.json()["data"]["pi_id"]
        resp = client.get(
            f"/api/pi/{pi_id}",
            headers={"Authorization": f"Bearer {research_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["pi_id"] == pi_id

    def test_get_pi_not_found(self, client, research_token):
        resp = client.get(
            "/api/pi/99999",
            headers={"Authorization": f"Bearer {research_token}"},
        )
        assert resp.status_code == 404

    def test_update_pi(self, client, research_token):
        create_resp = client.post(
            "/api/pi",
            json={
                "name": "Dr. Update PI",
                "institution": "Update University",
                "department": "Biology",
                "title": "Associate Professor",
                "research_areas": ["genetics"],
                "total_papers": 12,
                "h_index": 8,
            },
            headers={"Authorization": f"Bearer {research_token}"},
        )
        pi_id = create_resp.json()["data"]["pi_id"]
        resp = client.put(
            f"/api/pi/{pi_id}",
            json={"name": "Dr. Updated PI", "h_index": 15},
            headers={"Authorization": f"Bearer {research_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["name"] == "Dr. Updated PI"
        assert data["h_index"] == 15

    def test_pi_auth_required(self, client):
        resp = client.get("/api/pi/search")
        assert resp.status_code == 401
        resp = client.post("/api/pi", json={"name": "x", "institution": "y"})
        assert resp.status_code == 401


class TestProductRouter:
    def test_search_products(self, client, research_token):
        resp = client.get(
            "/api/products/search?q=test",
            headers={"Authorization": f"Bearer {research_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["code"] == 0

    def test_search_products_empty_query(self, client, research_token):
        resp = client.get(
            "/api/products/search?q=",
            headers={"Authorization": f"Bearer {research_token}"},
        )
        assert resp.status_code == 200
        assert isinstance(resp.json()["data"], list)

    def test_search_products_with_category(self, client, research_token):
        client.post(
            "/api/products",
            json={
                "name": "Cat Test Product",
                "category": "reagent",
                "brand": "TestCorp",
                "unit_price": 99.0,
            },
            headers={"Authorization": f"Bearer {research_token}"},
        )
        resp = client.get(
            "/api/products/search?category=reagent",
            headers={"Authorization": f"Bearer {research_token}"},
        )
        assert resp.status_code == 200
        items = resp.json()["data"]
        assert any(it.get("category") == "reagent" for it in items)

    def test_create_product(self, client, research_token):
        resp = client.post(
            "/api/products",
            json={
                "name": "Test Product X",
                "category": "equipment",
                "brand": "MedTech",
                "model": "X100",
                "unit_price": 1500.0,
                "keywords": ["lab", "analysis"],
            },
            headers={"Authorization": f"Bearer {research_token}"},
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["name"] == "Test Product X"
        assert data["category"] == "equipment"

    def test_get_product(self, client, research_token):
        create_resp = client.post(
            "/api/products",
            json={"name": "Get Product Y", "brand": "GetBrand"},
            headers={"Authorization": f"Bearer {research_token}"},
        )
        product_id = create_resp.json()["data"]["product_id"]
        resp = client.get(
            f"/api/products/{product_id}",
            headers={"Authorization": f"Bearer {research_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["product_id"] == product_id

    def test_get_product_not_found(self, client, research_token):
        resp = client.get(
            "/api/products/99999",
            headers={"Authorization": f"Bearer {research_token}"},
        )
        assert resp.status_code == 404

    def test_product_auth_required(self, client):
        resp = client.get("/api/products/search")
        assert resp.status_code == 401
        resp = client.post("/api/products", json={"name": "x"})
        assert resp.status_code == 401


class TestCustomerRouter:
    def test_get_customers_unauthorized(self, client):
        resp = client.get("/customers/")
        assert resp.status_code == 401

    def test_create_customer(self, client, auth_token):
        resp = client.post(
            "/customers/",
            json={
                "name": f"cust-{uuid.uuid4().hex[:6]}",
                "hospital": "Test Hospital",
                "department": "Cardiology",
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code in (200, 201)
        data = resp.json()["data"] if "data" in resp.json() else resp.json()
        assert data is not None

    def test_list_customers(self, client, auth_token):
        resp = client.get(
            "/customers/",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200


class TestMarketIntelRouter:
    def test_get_sources(self, client, auth_token):
        resp = client.get(
            "/market-intel/sources",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200


class TestOpportunityRouter:
    def test_get_opportunities(self, client, auth_token):
        resp = client.get(
            "/opportunities/",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
