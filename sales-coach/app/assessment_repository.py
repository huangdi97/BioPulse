import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from shared.columns import TABLE_EDUCATION_ASSESSMENT_COLS
from shared.repository import BaseRepository


class AssessmentRepository(BaseRepository):
    def __init__(self, db: sqlite3.Connection):
        super().__init__(db, "education_assessment", TABLE_EDUCATION_ASSESSMENT_COLS)

    def get_active_by_id(self, assessment_id: int) -> Optional[sqlite3.Row]:
        return self.db.execute(
            "SELECT * FROM education_assessment WHERE id = ? AND is_active = 1",
            (assessment_id,),
        ).fetchone()

    def get_active_or_404(self, assessment_id: int) -> sqlite3.Row:
        row = self.get_active_by_id(assessment_id)
        if not row:
            from fastapi import HTTPException
            from starlette import status

            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Assessment not found")
        return row

    def soft_delete_assessment(self, assessment_id: int) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self.db.execute(
            "UPDATE education_assessment SET is_active = 0, updated_at = ? WHERE id = ?",
            (now, assessment_id),
        )
        self.db.commit()

    def list_active(self, conditions=None, params=None, order_by="id DESC"):
        conds = ["is_active = 1"]
        if conditions:
            conds.extend(conditions)
        return self.list_all(conditions=conds, params=params, order_by=order_by)

    def paginate_active(self, page=1, page_size=20, conditions=None, params=None, order_by="id DESC"):
        conds = ["is_active = 1"]
        if conditions:
            conds.extend(conditions)
        return self.paginate(
            page=page,
            page_size=page_size,
            conditions=conds,
            params=params,
            order_by=order_by,
        )

    def get_stats(self) -> Dict[str, Any]:
        from collections import Counter

        total = self.db.execute("SELECT COUNT(*) FROM education_assessment WHERE is_active = 1").fetchone()[0]

        dist_rows = self.db.execute(
            "SELECT current_level, COUNT(*) as cnt FROM education_assessment WHERE is_active = 1 GROUP BY current_level"
        ).fetchall()
        level_dist = {r["current_level"]: r["cnt"] for r in dist_rows}

        weakness_rows = self.db.execute(
            "SELECT weaknesses FROM education_assessment WHERE is_active = 1 AND weaknesses IS NOT NULL AND weaknesses != ''"
        ).fetchall()
        counter: Counter = Counter()
        for row in weakness_rows:
            for w in row["weaknesses"].split(","):
                stripped = w.strip()
                if stripped:
                    counter[stripped] += 1
        top_weaknesses = [{"weakness": w, "count": c} for w, c in counter.most_common(10)]

        recent = self.db.execute(
            "SELECT COUNT(*) FROM education_assessment WHERE assessment_date >= date('now', '-30 days') AND is_active = 1"
        ).fetchone()[0]

        return {
            "total_assessments": total,
            "level_distribution": level_dist,
            "top_weaknesses": top_weaknesses,
            "recent_assessments": recent,
        }
