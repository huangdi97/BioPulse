import uuid


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
        assert resp.status_code == 201
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


class TestMemoryGateRouter:
    def test_get_memory_gates(self, client, auth_token):
        resp = client.get(
            "/memory-gates/",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200


class TestMemoryUtilityRouter:
    def test_memory_utility_scores_public(self, client):
        resp = client.get("/memory-utils/status")
        assert resp.status_code == 200


class TestCosmeticEndpointCoverage:
    def test_key_routes_require_auth(self, client):
        resp = client.get("/kg/entities/list")
        assert resp.status_code == 401

        resp = client.get("/recommend/list")
        assert resp.status_code == 401

        resp = client.get("/collaboration/sessions/list")
        assert resp.status_code == 401

        resp = client.get("/events/messages/list")
        assert resp.status_code == 401

        resp = client.get("/memory/consolidation/status")
        assert resp.status_code == 401

        resp = client.get("/orchestrate/templates/list")
        assert resp.status_code == 401

        resp = client.get("/causal/graph/test")
        assert resp.status_code == 401

        resp = client.get("/compute/job/list")
        assert resp.status_code == 401

        resp = client.get("/compliance/gov/logs/list")
        assert resp.status_code == 401

        resp = client.get("/training/scripts/list")
        assert resp.status_code == 401

        resp = client.get("/marketplace/metrics/dashboard")
        assert resp.status_code == 401

        resp = client.get("/mcp/tools/list")
        assert resp.status_code == 401
