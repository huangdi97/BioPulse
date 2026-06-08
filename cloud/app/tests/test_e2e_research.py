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
            json={"method_description": "zzz_no_match_zzz"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data == []

    def test_pi_to_quotation_flow(self, client):
        db_path = _get_research_db_path()
        conn = sqlite3.connect(db_path)
        try:
            conn.execute(
                "INSERT INTO research_products (name, category, keywords) VALUES (?, ?, ?)",
                ("PCR Master Mix Pro", "试剂盒", json.dumps(["PCR", "amplification", "DNA", "qPCR"])),
            )
            conn.execute(
                "INSERT INTO research_products (name, category, keywords) VALUES (?, ?, ?)",
                ("RNA Extraction Kit", "试剂盒", json.dumps(["RNA", "extraction", "purification"])),
            )
            conn.commit()
        finally:
            conn.close()

        token = _get_research_token(client)

        pi_resp = client.post(
            "/api/research/pi",
            json={
                "name": "Dr. Chen Guang",
                "institution": "Fudan University",
                "department": "Molecular Biology",
                "title": "Associate Professor",
                "research_areas": ["PCR", "DNA sequencing", "RNA analysis"],
                "total_papers": 45,
                "total_grants": 8,
                "h_index": 22,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert pi_resp.status_code == 201
        pi = pi_resp.json()["data"]
        pi_id = pi["pi_id"]

        match_resp = client.post(
            "/api/research/matching/for-pi",
            json={"pi_id": pi_id},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert match_resp.status_code == 200
        match_data = match_resp.json()["data"]
        assert len(match_data) > 0

        quotation_resp = client.post(
            "/api/research/quotations/generate",
            json={
                "template_id": "reagent",
                "items": [
                    {"name": "PCR Master Mix Pro", "catalog_no": "PCR-001", "spec": "100 rxns", "unit_price": 2800, "quantity": 3},
                    {"name": "RNA Extraction Kit", "catalog_no": "RNA-002", "spec": "50 preps", "unit_price": 1500, "quantity": 2},
                ],
                "customer_info": {"pi_name": "Dr. Chen Guang", "institution": "Fudan University"},
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert quotation_resp.status_code == 200
        quotation = quotation_resp.json()["data"]
        assert quotation["template_id"] == "reagent"
        assert quotation["total"] > 0

        conn = sqlite3.connect(db_path)
        try:
            conn.execute("DELETE FROM research_products")
            conn.commit()
        finally:
            conn.close()

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
