import json

from fastapi import HTTPException
from starlette import status

from cloud.app.services.base import BaseService


class VisitService(BaseService):
    """Visit 服务类。"""

    def init_table(self):
        """init_table 操作。"""
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

    def create_visit(self, body, user_id: int) -> dict:
        """create_visit 操作。

        Args:
            user_id: 描述

        Returns:
            描述
        """
        self.init_table()
        cursor = self.db.execute(
            """
            INSERT INTO visits (hcp_id, hcp_name, content, visit_type, evidence_photos, location, location_mode)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                body.hcp_id,
                body.hcp_name,
                body.content,
                body.visit_type,
                json.dumps(body.evidence_photos),
                body.location,
                body.location_mode,
            ),
        )
        self.db.commit()
        row = self.db.execute("SELECT * FROM visits WHERE id = ?", (cursor.lastrowid,)).fetchone()
        record = dict(row)
        record["evidence_photos"] = json.loads(record["evidence_photos"])
        return record

    def get_visit(self, visit_id: int) -> dict:
        """get_visit 操作。

        Args:
            visit_id: 描述

        Returns:
            描述
        """
        self.init_table()
        row = self.db.execute("SELECT * FROM visits WHERE id = ?", (visit_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visit not found")
        record = dict(row)
        record["evidence_photos"] = json.loads(record["evidence_photos"])
        return record
