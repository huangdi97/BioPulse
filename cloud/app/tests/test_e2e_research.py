import json
import sqlite3
import uuid

from cloud.app.research_database import _get_research_db_path
from shared.auth import create_access_token


def _get_research_token(client):
    username = f"research_{uuid.uuid4().hex[:8]}"
    resp = client.post("/auth/register", json={"username": username, "password": "testpass123"})
    assert resp.status_code == 201
    user_id = resp.json()["data"]["user_id"]
    return create_access_token(user_id, "rep", "research")


class TestResearchE2E:
    def test_research_pi_crud_flow(self, client):
        token = _get_research_token(client)
        resp = client.post(
            "/api/research/pi",
            json={
                "name": "Dr. Zhang Wei",
                "institution": "Peking University",
                "department": "Biology",
                "title": "Professor",
                "research_areas": ["PCR", "DNA sequencing"],
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        pi_id = resp.json()["data"]["pi_id"]

        resp = client.get(
            "/api/research/pi/search?q=Zhang",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert any(p["pi_id"] == pi_id for p in data)

    def test_research_matching(self, client):
        db_path = _get_research_db_path()
        conn = sqlite3.connect(db_path)
        try:
            conn.execute(
                "INSERT INTO research_products (name, category, keywords) VALUES (?, ?, ?)",
                ("PCR Kit v2", "试剂盒", json.dumps(["PCR", "amplification", "DNA"])),
            )
            conn.commit()
            product_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        finally:
            conn.close()

        token = _get_research_token(client)
        resp = client.post(
            "/api/research/matching/by-method",
            json={"method_description": "PCR amplification for DNA sequencing"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) > 0

        conn = sqlite3.connect(db_path)
        try:
            conn.execute("DELETE FROM research_products WHERE product_id = ?", (product_id,))
            conn.commit()
        finally:
            conn.close()

    def test_boundary_empty_method(self, client):
        token = _get_research_token(client)
        resp = client.post(
            "/api/research/matching/by-method",
            json={"method_description": ""},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data == []

    def test_boundary_no_products(self, client):
        token = _get_research_token(client)
        resp = client.post(
            "/api/research/matching/by-method",
            json={"method_description": "PCR amplification"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data == []

    def test_research_quotation_export(self, client):
        db_path = _get_research_db_path()
        conn = sqlite3.connect(db_path)
        try:
            conn.execute(
                "INSERT INTO research_quotations (template_id, title, customer_name, items_json, total_amount, status, created_by, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    "tpl-001",
                    "Test Quotation",
                    "Test Customer",
                    "[]",
                    1000.0,
                    "draft",
                    "test_user",
                    "2026-05-31T00:00:00",
                ),
            )
            conn.commit()
            qid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        finally:
            conn.close()

        token = _get_research_token(client)
        resp = client.get(
            f"/api/research/export/quotation/{qid}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "watermark" in data
        assert data["watermark"] == "科研服务记录-学术合规"

        conn = sqlite3.connect(db_path)
        try:
            conn.execute("DELETE FROM research_quotations WHERE quotation_id = ?", (qid,))
            conn.commit()
        finally:
            conn.close()
