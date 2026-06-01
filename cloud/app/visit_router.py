from fastapi import APIRouter, Depends, HTTPException, Request
from starlette import status
from pydantic import BaseModel
from typing import Optional
from cloud.app.database import DB_PATH
from shared.auth import verify_token
from shared.base import success
import json
import sqlite3
import os

router = APIRouter(prefix="", tags=["拜访"])


def get_direct_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_visits_table(db):
    db.execute("""
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
    db.commit()


conn = get_direct_db()
init_visits_table(conn)
conn.close()


def get_current_user(request: Request) -> dict:
    auth = request.headers.get("Authorization", "")
    scheme, _, token = auth.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth header")
    return verify_token(token)


class VisitCreate(BaseModel):
    hcp_id: int
    hcp_name: str
    content: str
    visit_type: str = ""
    evidence_photos: list[str] = []
    location: str = ""
    location_mode: str = ""


@router.post("/visit")
def create_visit(body: VisitCreate, user: dict = Depends(get_current_user)):
    db = get_direct_db()
    cursor = db.execute(
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
    db.commit()
    row = db.execute("SELECT * FROM visits WHERE id = ?", (cursor.lastrowid,)).fetchone()
    record = dict(row)
    record["evidence_photos"] = json.loads(record["evidence_photos"])
    db.close()
    return success(data=record)


@router.get("/visit/{visit_id}")
def get_visit(visit_id: int, user: dict = Depends(get_current_user)):
    db = get_direct_db()
    row = db.execute("SELECT * FROM visits WHERE id = ?", (visit_id,)).fetchone()
    db.close()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visit not found")
    record = dict(row)
    record["evidence_photos"] = json.loads(record["evidence_photos"])
    return success(data=record)
