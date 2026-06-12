"""BD Pipeline management service — CRUD for pipeline stages, amounts, probabilities."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any, Optional

STAGES = ["prospecting", "qualification", "proposal", "negotiation", "closed_won", "closed_lost"]


class BDPipelineService:
    """BD pipeline CRUD management."""

    def __init__(self, db: sqlite3.Connection):
        self._db = db
        self._init_table()

    def _init_table(self) -> None:
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS bd_pipeline (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id TEXT NOT NULL UNIQUE,
                lead_name TEXT NOT NULL,
                company TEXT DEFAULT '',
                stage TEXT NOT NULL DEFAULT 'prospecting',
                amount REAL DEFAULT 0.0,
                probability REAL DEFAULT 0.0,
                owner TEXT DEFAULT '',
                score REAL DEFAULT 0.0,
                tier TEXT DEFAULT 'cold',
                notes TEXT DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        self._db.commit()

    def create(
        self,
        lead_id: str,
        lead_name: str,
        company: str = "",
        amount: float = 0.0,
        probability: float = 0.0,
        owner: str = "",
        score: float = 0.0,
        tier: str = "cold",
        notes: str = "",
    ) -> dict[str, Any]:
        """Create a new pipeline entry."""
        now = datetime.now(timezone.utc).isoformat()
        self._db.execute(
            "INSERT INTO bd_pipeline (lead_id, lead_name, company, stage, amount, probability, owner, score, tier, notes, created_at, updated_at) "
            "VALUES (?, ?, ?, 'prospecting', ?, ?, ?, ?, ?, ?, ?, ?)",
            (lead_id, lead_name, company, amount, probability, owner, score, tier, notes, now, now),
        )
        self._db.commit()
        return self.get(lead_id)

    def get(self, lead_id: str) -> Optional[dict[str, Any]]:
        row = self._db.execute("SELECT * FROM bd_pipeline WHERE lead_id = ?", (lead_id,)).fetchone()
        return dict(row) if row else None

    def list_all(self, stage: Optional[str] = None, owner: Optional[str] = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM bd_pipeline WHERE 1=1"
        params = []
        if stage:
            query += " AND stage = ?"
            params.append(stage)
        if owner:
            query += " AND owner = ?"
            params.append(owner)
        query += " ORDER BY updated_at DESC"
        return [dict(r) for r in self._db.execute(query, params).fetchall()]

    def update_stage(
        self,
        lead_id: str,
        stage: str,
        amount: float | None = None,
        probability: float | None = None,
        notes: str | None = None,
    ) -> dict[str, Any] | None:
        """Update pipeline stage and optional fields."""
        if stage not in STAGES:
            return None
        now = datetime.now(timezone.utc).isoformat()
        fields = ["stage = ?", "updated_at = ?"]
        params = [stage, now]
        if amount is not None:
            fields.append("amount = ?")
            params.append(amount)
        if probability is not None:
            fields.append("probability = ?")
            params.append(probability)
        if notes is not None:
            fields.append("notes = ?")
            params.append(notes)
        params.append(lead_id)
        self._db.execute(f"UPDATE bd_pipeline SET {', '.join(fields)} WHERE lead_id = ?", params)
        self._db.commit()
        return self.get(lead_id)

    def delete(self, lead_id: str) -> bool:
        cur = self._db.execute("DELETE FROM bd_pipeline WHERE lead_id = ?", (lead_id,))
        self._db.commit()
        return cur.rowcount > 0

    def summary(self) -> dict[str, Any]:
        """Return pipeline summary metrics."""
        rows = self._db.execute(
            "SELECT stage, COUNT(*) as count, SUM(amount) as total_amount, AVG(probability) as avg_probability FROM bd_pipeline GROUP BY stage"
        ).fetchall()
        total = sum((r["total_amount"] or 0.0) * (r["avg_probability"] or 0.0) for r in rows)
        return {
            "by_stage": [dict(r) for r in rows],
            "weighted_total": round(total, 2),
            "total_deals": sum(r["count"] for r in rows),
        }
