import sqlite3
from typing import Optional


class VisitRepository:
    def __init__(self, db: sqlite3.Connection):
        self.db = db

    def init_table(self):
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS visits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hcp_id INTEGER NOT NULL,
                hcp_name TEXT NOT NULL,
                content TEXT NOT NULL,
                visit_type TEXT DEFAULT "",
                evidence_photos TEXT DEFAULT "[]",
                location TEXT DEFAULT "",
                location_mode TEXT DEFAULT "",
                compliance_status TEXT DEFAULT "passed",
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.db.commit()

    def create_visit(
        self,
        hcp_id: int,
        hcp_name: str,
        content: str,
        visit_type: str,
        evidence_photos_json: str,
        location: str,
        location_mode: str,
    ) -> dict:
        cursor = self.db.execute(
            "INSERT INTO visits (hcp_id, hcp_name, content, visit_type, evidence_photos, location, location_mode) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (hcp_id, hcp_name, content, visit_type, evidence_photos_json, location, location_mode),
        )
        self.db.commit()
        row = self.db.execute("SELECT * FROM visits WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return dict(row)

    def get_visit(self, visit_id: int) -> Optional[dict]:
        row = self.db.execute("SELECT * FROM visits WHERE id = ?", (visit_id,)).fetchone()
        return dict(row) if row else None
