"""Tests for flying inspection (飞检准备度) API endpoints."""

import uuid


class TestFlyingInspection:
    def test_get_checklist(self, client, auth_token):
        resp = client.get("/api/inspection/checklist", headers={"Authorization": f"Bearer {auth_token}"})
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) == 4
        assert data[0]["id"] == "chk-license"
        assert data[0]["status"] == "passed"

    def test_get_checklist_filtered(self, client, auth_token):
        resp = client.get(
            "/api/inspection/checklist?category=冷链管理",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) == 1
        assert data[0]["category"] == "冷链管理"

    def test_create_task(self, client, auth_token):
        resp = client.post(
            "/api/inspection/task",
            json={
                "title": "测试整改任务",
                "description": "单元测试创建的任务",
                "assignee": "测试员",
                "deadline": "2026-07-01",
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["title"] == "测试整改任务"
        assert data["assignee"] == "测试员"
        assert data["status"] == "pending"
        assert data["id"].startswith("task-")

    def test_confirm_task(self, client, auth_token):
        resp = client.put(
            "/api/inspection/task/task-cold-chain-001/confirm",
            json={},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["id"] == "task-cold-chain-001"
        assert data["status"] == "confirmed"

    def test_confirm_task_not_found(self, client, auth_token):
        resp = client.put(
            f"/api/inspection/task/task-{uuid.uuid4().hex[:8]}/confirm",
            json={},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 404

    def test_get_history(self, client, auth_token):
        resp = client.get("/api/inspection/history", headers={"Authorization": f"Bearer {auth_token}"})
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) >= 2
        assert data[0]["inspection_id"] == "inspection-2026-06"

    def test_auth_required(self, client):
        for method, path in [
            ("GET", "/api/inspection/checklist"),
            ("GET", "/api/inspection/history"),
            ("POST", "/api/inspection/task"),
            ("PUT", "/api/inspection/task/task-cold-chain-001/confirm"),
        ]:
            if method == "GET":
                resp = client.get(path)
            elif method == "POST":
                resp = client.post(path, json={"title": "x", "assignee": "x", "deadline": "x"})
            elif method == "PUT":
                resp = client.put(path, json={})
            assert resp.status_code == 401, f"{method} {path} should return 401"
