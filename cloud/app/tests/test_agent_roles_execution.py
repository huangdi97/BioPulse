import uuid


class TestAgentRoleRouter:
    def test_create_role(self, client, auth_token):
        resp = client.post(
            "/agent/roles",
            json={
                "name": f"test-role-{uuid.uuid4().hex[:6]}",
                "role_type": "sales_rep",
                "description": "A test role",
                "system_prompt": "You are a helpful assistant.",
                "temperature": 0.5,
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["name"] is not None
        assert data["id"] is not None
        assert data["role_type"] == "sales_rep"

    def test_list_roles(self, client, auth_token):
        resp = client.get(
            "/agent/roles",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        assert isinstance(resp.json()["data"], list)

    def test_list_roles_by_type(self, client, auth_token):
        client.post(
            "/agent/roles",
            json={
                "name": f"typed-role-{uuid.uuid4().hex[:6]}",
                "role_type": "doctor",
                "system_prompt": "You are a doctor.",
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        resp = client.get(
            "/agent/roles?role_type=doctor",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        items = resp.json()["data"]
        assert all(it.get("role_type") == "doctor" for it in items)

    def test_get_role(self, client, auth_token):
        create_resp = client.post(
            "/agent/roles",
            json={
                "name": f"get-role-{uuid.uuid4().hex[:6]}",
                "role_type": "researcher",
                "system_prompt": "You research.",
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        role_id = create_resp.json()["data"]["id"]
        resp = client.get(
            f"/agent/roles/{role_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["id"] == role_id

    def test_get_role_not_found(self, client, auth_token):
        resp = client.get(
            "/agent/roles/99999",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 404

    def test_update_role(self, client, auth_token):
        create_resp = client.post(
            "/agent/roles",
            json={
                "name": f"update-role-{uuid.uuid4().hex[:6]}",
                "role_type": "manager",
                "system_prompt": "You manage.",
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        role_id = create_resp.json()["data"]["id"]
        resp = client.patch(
            f"/agent/roles/{role_id}",
            json={"name": "Updated Role Name", "temperature": 0.9},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "Updated Role Name"

    def test_update_role_not_found(self, client, auth_token):
        resp = client.patch(
            "/agent/roles/99999",
            json={"name": "Does Not Exist"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 404

    def test_delete_role(self, client, auth_token):
        create_resp = client.post(
            "/agent/roles",
            json={
                "name": f"del-role-{uuid.uuid4().hex[:6]}",
                "role_type": "temp",
                "system_prompt": "Temporary role.",
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        role_id = create_resp.json()["data"]["id"]
        resp = client.delete(
            f"/agent/roles/{role_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200

    def test_delete_role_not_found(self, client, auth_token):
        resp = client.delete(
            "/agent/roles/99999",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 404

    def test_role_auth_required(self, client):
        resp = client.get("/agent/roles")
        assert resp.status_code == 401

        resp = client.post("/agent/roles", json={"name": "x", "system_prompt": "y"})
        assert resp.status_code == 401


class TestAgentExecutionRouter:
    def test_submit_task(self, client, auth_token):
        resp = client.post(
            "/agent/exec/submit",
            json={
                "agent_role": "test-role",
                "action_type": "process",
                "input_data": {"key": "value"},
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["agent_role"] == "test-role"
        assert data["status"] == "completed"
        assert "task_id" in data

    def test_list_tasks(self, client, auth_token):
        client.post(
            "/agent/exec/submit",
            json={"agent_role": "lister", "action_type": "process"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        resp = client.get(
            "/agent/exec/tasks/list",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        assert isinstance(resp.json()["data"], list)
        assert len(resp.json()["data"]) >= 1

    def test_list_tasks_with_filters(self, client, auth_token):
        client.post(
            "/agent/exec/submit",
            json={"agent_role": "filter-test", "action_type": "review"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        resp = client.get(
            "/agent/exec/tasks/list?status=completed&agent_role=filter-test",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        items = resp.json()["data"]
        for it in items:
            assert it["status"] == "completed"
            assert it["agent_role"] == "filter-test"

    def test_get_task(self, client, auth_token):
        create_resp = client.post(
            "/agent/exec/submit",
            json={"agent_role": "getter", "action_type": "fetch"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        task_id = create_resp.json()["data"]["task_id"]
        resp = client.get(
            f"/agent/exec/tasks/{task_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["task_id"] == task_id

    def test_get_task_not_found(self, client, auth_token):
        resp = client.get(
            "/agent/exec/tasks/nonexistent-task-id",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 404

    def test_retry_task(self, client, auth_token):
        create_resp = client.post(
            "/agent/exec/submit",
            json={"agent_role": "retry-role", "action_type": "test"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        task_id = create_resp.json()["data"]["task_id"]
        resp = client.post(
            f"/agent/exec/tasks/{task_id}/retry",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["retry_count"] >= 1
        assert resp.json()["data"]["status"] == "pending"

    def test_retry_task_not_found(self, client, auth_token):
        resp = client.post(
            "/agent/exec/tasks/bad-id/retry",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 404

    def test_approve_task(self, client, auth_token):
        create_resp = client.post(
            "/agent/exec/submit",
            json={"agent_role": "approve-role", "action_type": "review"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        task_id = create_resp.json()["data"]["task_id"]
        resp = client.post(
            f"/agent/exec/tasks/{task_id}/approve",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "completed"

    def test_approve_task_not_found(self, client, auth_token):
        resp = client.post(
            "/agent/exec/tasks/bad-id/approve",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 404

    def test_a2a_card(self, client, auth_token):
        resp = client.get(
            "/agent/exec/a2a/card",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "name" in data
        assert "skills" in data

    def test_a2a_task(self, client, auth_token):
        resp = client.post(
            "/agent/exec/a2a/task",
            json={
                "task_id": f"a2a-test-{uuid.uuid4().hex[:8]}",
                "agent_role": "a2a-role",
                "input_data": {"question": "test"},
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["source"] == "a2a"
        assert data["agent_role"] == "a2a-role"

    def test_exec_auth_required(self, client):
        resp = client.get("/agent/exec/tasks/list")
        assert resp.status_code == 401
        resp = client.post("/agent/exec/submit", json={})
        assert resp.status_code == 401
