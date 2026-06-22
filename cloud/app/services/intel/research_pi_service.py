"""科研 PI 服务，负责科研模式下的 PI 信息搜索与创建。"""

import json
from typing import Optional

from fastapi import HTTPException
from starlette import status

from cloud.app.research_database import get_research_db


class ResearchPiService:
    """科研 PI 服务，提供科研模式下 PI 的搜索、详情查询与创建。"""

    def search(self, q: str) -> list:
        db = get_research_db()
        try:
            pattern = f"%{q}%"
            rows = db.execute(
                "SELECT * FROM research_pi_profiles WHERE name LIKE ? OR institution LIKE ? OR research_areas LIKE ?",
                (pattern, pattern, pattern),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            db.close()

    def get_by_id(self, pi_id: int) -> dict:
        db = get_research_db()
        try:
            row = db.execute("SELECT * FROM research_pi_profiles WHERE pi_id = ?", (pi_id,)).fetchone()
            if not row:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PI not found")
            return dict(row)
        finally:
            db.close()

    def create(
        self,
        name: str,
        institution: str,
        department: str = "",
        title: str = "",
        hcp_id: Optional[int] = None,
        research_areas: list | None = None,
        total_papers: int = 0,
        total_grants: int = 0,
        h_index: int = 0,
    ) -> dict:
        db = get_research_db()
        try:
            cursor = db.execute(
                "INSERT INTO research_pi_profiles (name, hcp_id, institution, department, title, "
                "research_areas, total_papers, total_grants, h_index) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    name,
                    hcp_id,
                    institution,
                    department,
                    title,
                    json.dumps(research_areas or []),
                    total_papers,
                    total_grants,
                    h_index,
                ),
            )
            db.commit()
            pi_id = cursor.lastrowid
            row = db.execute("SELECT * FROM research_pi_profiles WHERE pi_id = ?", (pi_id,)).fetchone()
            return dict(row)
        finally:
            db.close()
