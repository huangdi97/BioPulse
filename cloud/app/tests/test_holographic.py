import uuid


class TestHolographicRouter:
    def _create_entry(self, client, auth_token, title=None, memory_type="insight", source_type="", source_id=None, context_tags=None, importance=0.5):
        title = title or f"h-test-{uuid.uuid4().hex[:6]}"
        payload = {
            "title": title,
            "content": f"Content for {title}",
            "memory_type": memory_type,
            "source_type": source_type,
            "importance": importance,
        }
        if source_id is not None:
            payload["source_id"] = source_id
        if context_tags is not None:
            payload["context_tags"] = context_tags
        resp = client.post(
            "/memory/entries",
            json=payload,
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 201, resp.text
        return resp.json()["data"]["id"]

    def test_create_association(self, client, auth_token):
        id_a = self._create_entry(client, auth_token, "Assoc Test A")
        id_b = self._create_entry(client, auth_token, "Assoc Test B")
        resp = client.post(
            f"/memory/{id_a}/associate",
            json={"memory_id_b": id_b, "relation_type": "cross_ref", "weight": 0.9},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()["data"]
        assert data["relation_type"] == "cross_ref"
        assert data["weight"] == 0.9
        assert {data["memory_id_a"], data["memory_id_b"]} == {id_a, id_b}

    def test_create_association_dedup(self, client, auth_token):
        id_a = self._create_entry(client, auth_token, "Dedup A")
        id_b = self._create_entry(client, auth_token, "Dedup B")
        params = {"memory_id_b": id_b, "relation_type": "related"}
        headers = {"Authorization": f"Bearer {auth_token}"}
        r1 = client.post(f"/memory/{id_a}/associate", json=params, headers=headers)
        assert r1.status_code == 201
        r2 = client.post(f"/memory/{id_a}/associate", json=params, headers=headers)
        assert r2.status_code == 201
        assert r1.json()["data"]["id"] == r2.json()["data"]["id"]

    def test_get_associations(self, client, auth_token):
        id_a = self._create_entry(client, auth_token, "GetAssoc A")
        id_b = self._create_entry(client, auth_token, "GetAssoc B")
        client.post(
            f"/memory/{id_a}/associate",
            json={"memory_id_b": id_b, "relation_type": "test_related"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        resp = client.get(f"/memory/{id_a}/associations")
        assert resp.status_code == 200
        items = resp.json()["data"]
        assert len(items) >= 1
        assert items[0]["related_memory"]["id"] == id_b
        assert items[0]["relation_type"] == "test_related"

    def test_holographic_graph(self, client, auth_token):
        id_a = self._create_entry(client, auth_token, "Graph Root")
        id_b = self._create_entry(client, auth_token, "Graph B")
        id_c = self._create_entry(client, auth_token, "Graph C")
        client.post(
            f"/memory/{id_a}/associate",
            json={"memory_id_b": id_b},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        client.post(
            f"/memory/{id_b}/associate",
            json={"memory_id_b": id_c},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        resp = client.get(f"/memory/{id_a}/holographic?depth=3")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["depth"] == 3
        assert data["total_nodes"] >= 3
        assert data["entry"]["id"] == id_a
        assert len(data["entry"]["associations"]) >= 1

    def test_holographic_with_depth_1(self, client, auth_token):
        id_a = self._create_entry(client, auth_token, "Depth1 Root")
        id_b = self._create_entry(client, auth_token, "Depth1 B")
        client.post(
            f"/memory/{id_a}/associate",
            json={"memory_id_b": id_b},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        resp = client.get(f"/memory/{id_a}/holographic?depth=1")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data["entry"]["associations"]) >= 1
        assert data["entry"]["associations"][0]["associations"] == []

    def test_delete_association(self, client, auth_token):
        id_a = self._create_entry(client, auth_token, "DelAssoc A")
        id_b = self._create_entry(client, auth_token, "DelAssoc B")
        assoc_resp = client.post(
            f"/memory/{id_a}/associate",
            json={"memory_id_b": id_b},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assoc_id = assoc_resp.json()["data"]["id"]
        resp = client.delete(
            f"/memory/associations/{assoc_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["deleted_id"] == assoc_id

    def test_self_association_rejected(self, client, auth_token):
        id_a = self._create_entry(client, auth_token, "Self A")
        resp = client.post(
            f"/memory/{id_a}/associate",
            json={"memory_id_b": id_a},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 400

    def test_associate_nonexistent_memory(self, client, auth_token):
        resp = client.post(
            "/memory/99999/associate",
            json={"memory_id_b": 99998},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 404

    def test_holographic_nonexistent_memory(self, client):
        resp = client.get("/memory/99999/holographic")
        assert resp.status_code == 404

    def test_auto_association_by_source(self, client, auth_token):
        src = f"shared-src-{uuid.uuid4().hex[:6]}"
        id_a = self._create_entry(client, auth_token, f"Src A {src}", source_id=src)
        self._create_entry(client, auth_token, f"Src B {src}", source_id=src)
        resp = client.get(f"/memory/{id_a}/associations")
        assert resp.status_code == 200
        items = resp.json()["data"]
        assert len(items) >= 1

    def test_associations_public_read(self, client, auth_token):
        id_a = self._create_entry(client, auth_token, "PublicRead A")
        id_b = self._create_entry(client, auth_token, "PublicRead B")
        client.post(
            f"/memory/{id_a}/associate",
            json={"memory_id_b": id_b},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        resp = client.get(f"/memory/{id_a}/associations")
        assert resp.status_code == 200

    def test_holographic_auth_required(self, client):
        resp = client.post(
            "/memory/1/associate",
            json={"memory_id_b": 2},
        )
        assert resp.status_code == 401

    def test_holographic_delete_auth_required(self, client):
        resp = client.delete("/memory/associations/1")
        assert resp.status_code == 401
