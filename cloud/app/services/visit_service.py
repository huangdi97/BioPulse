import json
import sqlite3

from fastapi import HTTPException
from starlette import status

from cloud.app.database import DB_PATH
from cloud.app.repositories.visit_repository import VisitRepository


class VisitService:
    def __init__(self, db: sqlite3.Connection = None):
        if db is None:
            db = sqlite3.connect(DB_PATH)
            db.row_factory = sqlite3.Row
        self.repo = VisitRepository(db)

    def create_visit(self, body) -> dict:
        self.repo.init_table()
        record = self.repo.create_visit(
            hcp_id=body.hcp_id,
            hcp_name=body.hcp_name,
            content=body.content,
            visit_type=body.visit_type,
            evidence_photos_json=json.dumps(body.evidence_photos),
            location=body.location,
            location_mode=body.location_mode,
        )
        record["evidence_photos"] = json.loads(record["evidence_photos"])
        return record

    def get_visit(self, visit_id: int) -> dict:
        self.repo.init_table()
        record = self.repo.get_visit(visit_id)
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visit not found")
        record["evidence_photos"] = json.loads(record["evidence_photos"])
        return record
