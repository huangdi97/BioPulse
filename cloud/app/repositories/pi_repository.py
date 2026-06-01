import json
import sqlite3
from typing import Optional


class PiRepository:
    def __init__(self, db: sqlite3.Connection):
        self.db = db
        self._ensure_table()

    def _ensure_table(self):
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS pi_profiles ("
            "pi_id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "name TEXT NOT NULL, "
            "hcp_id INTEGER, "
            "institution TEXT NOT NULL DEFAULT '', "
            "department TEXT NOT NULL DEFAULT '', "
            "title TEXT NOT NULL DEFAULT '', "
            "research_areas TEXT NOT NULL DEFAULT '[]', "
            "total_papers INTEGER NOT NULL DEFAULT 0, "
            "total_grants INTEGER NOT NULL DEFAULT 0, "
            "h_index INTEGER NOT NULL DEFAULT 0, "
            "last_updated TEXT NOT NULL DEFAULT ''"
            ")"
        )
        self.db.commit()

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
        last_updated: str = "",
    ) -> int:
        cursor = self.db.execute(
            "INSERT INTO pi_profiles (name, hcp_id, institution, department, title, "
            "research_areas, total_papers, total_grants, h_index, last_updated) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
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
                last_updated,
            ),
        )
        self.db.commit()
        return cursor.lastrowid

    def get_by_id(self, pi_id: int) -> Optional[dict]:
        row = self.db.execute("SELECT * FROM pi_profiles WHERE pi_id = ?", (pi_id,)).fetchone()
        if row:
            return dict(row)
        return None

    def update(self, pi_id: int, **kwargs) -> bool:
        allowed = {
            "name",
            "hcp_id",
            "institution",
            "department",
            "title",
            "research_areas",
            "total_papers",
            "total_grants",
            "h_index",
            "last_updated",
        }
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return False
        if "research_areas" in updates:
            updates["research_areas"] = json.dumps(updates["research_areas"])
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [pi_id]
        cursor = self.db.execute(f"UPDATE pi_profiles SET {set_clause} WHERE pi_id = ?", values)
        self.db.commit()
        return cursor.rowcount > 0

    def delete(self, pi_id: int) -> bool:
        cursor = self.db.execute("DELETE FROM pi_profiles WHERE pi_id = ?", (pi_id,))
        self.db.commit()
        return cursor.rowcount > 0

    def list_all(self) -> list[dict]:
        return [dict(r) for r in self.db.execute("SELECT * FROM pi_profiles").fetchall()]

    def search(self, keyword: str) -> list[dict]:
        pattern = f"%{keyword}%"
        rows = self.db.execute(
            "SELECT * FROM pi_profiles WHERE name LIKE ? OR institution LIKE ? OR research_areas LIKE ?",
            (pattern, pattern, pattern),
        ).fetchall()
        return [dict(r) for r in rows]
