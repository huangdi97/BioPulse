import uuid


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


class TestInteractionRouter:
    def test_get_interactions(self, client, auth_token):
        resp = client.get(
            "/interactions/",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200


class TestTaskRouter:
    def test_get_tasks(self, client, auth_token):
        resp = client.get(
            "/tasks/",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200


class TestPiRouter:
    def test_search_pi(self, client, auth_token):
        resp = client.get(
            "/api/pi/search?q=test",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["code"] == 0

    def test_search_pi_empty_query(self, client, auth_token):
        resp = client.get(
            "/api/pi/search?q=",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["code"] == 0
        assert isinstance(resp.json()["data"], list)

    def test_create_pi(self, client, auth_token):
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
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["name"] == "Dr. Test PI"
        assert data["institution"] == "Test University"

    def test_get_pi(self, client, auth_token):
        create_resp = client.post(
            "/api/pi",
            json={
                "name": "Dr. Get Test",
                "institution": "Get University",
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        pi_id = create_resp.json()["data"]["pi_id"]
        resp = client.get(
            f"/api/pi/{pi_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["pi_id"] == pi_id

    def test_get_pi_not_found(self, client, auth_token):
        resp = client.get(
            "/api/pi/99999",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 404

    def test_update_pi(self, client, auth_token):
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
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        pi_id = create_resp.json()["data"]["pi_id"]
        resp = client.put(
            f"/api/pi/{pi_id}",
            json={"name": "Dr. Updated PI", "h_index": 15},
            headers={"Authorization": f"Bearer {auth_token}"},
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
    def test_search_products(self, client, auth_token):
        resp = client.get(
            "/api/products/search?q=test",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["code"] == 0

    def test_search_products_empty_query(self, client, auth_token):
        resp = client.get(
            "/api/products/search?q=",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        assert isinstance(resp.json()["data"], list)

    def test_search_products_with_category(self, client, auth_token):
        client.post(
            "/api/products",
            json={
                "name": "Cat Test Product",
                "category": "reagent",
                "brand": "TestCorp",
                "unit_price": 99.0,
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        resp = client.get(
            "/api/products/search?category=reagent",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        items = resp.json()["data"]
        assert any(it.get("category") == "reagent" for it in items)

    def test_create_product(self, client, auth_token):
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
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["name"] == "Test Product X"
        assert data["category"] == "equipment"

    def test_get_product(self, client, auth_token):
        create_resp = client.post(
            "/api/products",
            json={"name": "Get Product Y", "brand": "GetBrand"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        product_id = create_resp.json()["data"]["product_id"]
        resp = client.get(
            f"/api/products/{product_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["product_id"] == product_id

    def test_get_product_not_found(self, client, auth_token):
        resp = client.get(
            "/api/products/99999",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 404

    def test_product_auth_required(self, client):
        resp = client.get("/api/products/search")
        assert resp.status_code == 401
        resp = client.post("/api/products", json={"name": "x"})
        assert resp.status_code == 401


class TestWorldTreeRouter:
    def test_create_node(self, client, auth_token):
        resp = client.post(
            "/world-tree/nodes",
            json={
                "name": f"node-{uuid.uuid4().hex[:6]}",
                "description": "A test node",
                "node_type": "tag",
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["name"] is not None
        assert "id" in data

    def test_list_nodes(self, client):
        resp = client.get("/world-tree/nodes")
        assert resp.status_code == 200
        assert isinstance(resp.json()["data"], list)

    def test_get_node(self, client, auth_token):
        create_resp = client.post(
            "/world-tree/nodes",
            json={
                "name": f"get-node-{uuid.uuid4().hex[:6]}",
                "node_type": "category",
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        node_id = create_resp.json()["data"]["id"]
        resp = client.get(f"/world-tree/nodes/{node_id}")
        assert resp.status_code == 200
        assert resp.json()["data"]["id"] == node_id

    def test_get_node_not_found(self, client):
        resp = client.get("/world-tree/nodes/99999")
        assert resp.status_code == 404

    def test_update_node(self, client, auth_token):
        create_resp = client.post(
            "/world-tree/nodes",
            json={
                "name": f"upd-node-{uuid.uuid4().hex[:6]}",
                "node_type": "tag",
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        node_id = create_resp.json()["data"]["id"]
        resp = client.patch(
            f"/world-tree/nodes/{node_id}",
            json={"name": "Updated Node Name", "description": "Updated desc"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "Updated Node Name"

    def test_delete_node(self, client, auth_token):
        create_resp = client.post(
            "/world-tree/nodes",
            json={
                "name": f"del-node-{uuid.uuid4().hex[:6]}",
                "node_type": "tag",
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        node_id = create_resp.json()["data"]["id"]
        resp = client.delete(f"/world-tree/nodes/{node_id}")
        assert resp.status_code == 200

    def test_full_tree(self, client):
        resp = client.get("/world-tree/tree/full")
        assert resp.status_code == 200
        assert isinstance(resp.json()["data"], list)

    def test_world_tree_auth_required(self, client):
        resp = client.post("/world-tree/nodes", json={"name": "x"})
        assert resp.status_code == 401
