import uuid


class TestAgentPipelineRouter:
    def _create_role(self, client, auth_token):
        resp = client.post(
            "/agent/roles",
            json={
                "name": f"pipe-role-{uuid.uuid4().hex[:6]}",
                "role_type": "processor",
                "system_prompt": "You are a processor.",
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 201
        return resp.json()["data"]["id"]

    def test_create_pipeline(self, client, auth_token):
        role_id = self._create_role(client, auth_token)
        resp = client.post(
            "/agent/pipelines",
            json={
                "name": f"test-pipe-{uuid.uuid4().hex[:6]}",
                "description": "A test pipeline",
                "steps": [
                    {
                        "step_order": 1,
                        "agent_role_id": role_id,
                        "input_mapping": {"context": "previous_output"},
                    }
                ],
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["id"] is not None
        assert data["name"] is not None

    def test_list_pipelines(self, client, auth_token):
        role_id = self._create_role(client, auth_token)
        client.post(
            "/agent/pipelines",
            json={
                "name": f"list-pipe-{uuid.uuid4().hex[:6]}",
                "steps": [{"step_order": 1, "agent_role_id": role_id}],
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        resp = client.get(
            "/agent/pipelines",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        items = resp.json()["data"]
        assert isinstance(items, list)
        assert len(items) >= 1

    def test_get_pipeline(self, client, auth_token):
        role_id = self._create_role(client, auth_token)
        create_resp = client.post(
            "/agent/pipelines",
            json={
                "name": f"get-pipe-{uuid.uuid4().hex[:6]}",
                "steps": [{"step_order": 1, "agent_role_id": role_id}],
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        pid = create_resp.json()["data"]["id"]
        resp = client.get(
            f"/agent/pipelines/{pid}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["id"] == pid
        assert "steps" in data
        assert len(data["steps"]) >= 1

    def test_get_pipeline_not_found(self, client, auth_token):
        resp = client.get(
            "/agent/pipelines/99999",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 404

    def test_delete_pipeline(self, client, auth_token):
        role_id = self._create_role(client, auth_token)
        create_resp = client.post(
            "/agent/pipelines",
            json={
                "name": f"del-pipe-{uuid.uuid4().hex[:6]}",
                "steps": [{"step_order": 1, "agent_role_id": role_id}],
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        pid = create_resp.json()["data"]["id"]
        resp = client.delete(
            f"/agent/pipelines/{pid}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200

    def test_list_runs_empty(self, client, auth_token):
        role_id = self._create_role(client, auth_token)
        create_resp = client.post(
            "/agent/pipelines",
            json={
                "name": f"runs-pipe-{uuid.uuid4().hex[:6]}",
                "steps": [{"step_order": 1, "agent_role_id": role_id}],
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        pid = create_resp.json()["data"]["id"]
        resp = client.get(
            f"/agent/pipelines/{pid}/runs",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "items" in data or isinstance(data, dict)

    def test_pipeline_auth_required(self, client):
        resp = client.get("/agent/pipelines")
        assert resp.status_code == 401
        resp = client.post("/agent/pipelines", json={"name": "x", "steps": []})
        assert resp.status_code == 401
