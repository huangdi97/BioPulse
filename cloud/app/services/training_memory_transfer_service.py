import json
from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from starlette import status

from cloud.app.services.base import BaseService


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class TrainingMemoryTransferService(BaseService):
    def __init__(self, db):
        super().__init__(db)
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS training_transferred_memory ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "title TEXT NOT NULL DEFAULT '', "
            "content TEXT NOT NULL DEFAULT '', "
            "skill_area TEXT NOT NULL DEFAULT '', "
            "scenario_type TEXT NOT NULL DEFAULT '', "
            "source_training_id INTEGER, "
            "score REAL DEFAULT 0.0, "
            "transfer_date TEXT DEFAULT CURRENT_TIMESTAMP"
            ")"
        )
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_ttm_skill_area ON training_transferred_memory(skill_area)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_ttm_scenario ON training_transferred_memory(scenario_type)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_ttm_source ON training_transferred_memory(source_training_id)")
        self.db.commit()

    def transfer_from_training(self, training_id: Optional[int] = None, min_score: float = 80.0) -> dict:
        conditions = ["ts.score >= ?"]
        params = [min_score]
        if training_id is not None:
            conditions.append("ts.id = ?")
            params.append(training_id)

        query = (
            "SELECT ts.id as session_id, ts.user_id, ts.module_id, ts.score, "
            "ts.passed, ts.feedback, ts.answers, ts.completed_at, "
            "tm.title as module_title, tm.category, tm.difficulty, tm.content as module_content "
            "FROM training_sessions ts "
            "JOIN training_modules tm ON ts.module_id = tm.id "
            "WHERE " + " AND ".join(conditions) + " ORDER BY ts.score DESC"
        )
        rows = self.db.execute(query, params).fetchall()

        transferred = 0
        skipped = 0
        items = []

        for row in rows:
            existing = self.db.execute(
                "SELECT id FROM training_transferred_memory WHERE source_training_id = ?",
                (row["session_id"],),
            ).fetchone()
            if existing:
                skipped += 1
                continue

            title = f"{row['module_title']} (score: {row['score']})"

            try:
                answers_data = json.loads(row["answers"]) if isinstance(row["answers"], str) else row["answers"]
            except (json.JSONDecodeError, TypeError):
                answers_data = row["answers"]

            content = json.dumps(
                {
                    "module_title": row["module_title"],
                    "difficulty": row["difficulty"],
                    "score": row["score"],
                    "passed": row["passed"],
                    "feedback": row["feedback"],
                    "answers": answers_data,
                    "user_id": row["user_id"],
                },
                ensure_ascii=False,
            )

            skill_area = row["category"]
            scenario_type = f"training_{row['difficulty']}"

            now = _now()
            cur = self.db.execute(
                "INSERT INTO training_transferred_memory "
                "(title, content, skill_area, scenario_type, source_training_id, score, transfer_date) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (title, content, skill_area, scenario_type, row["session_id"], row["score"], now),
            )
            transferred += 1
            items.append(
                {
                    "id": cur.lastrowid,
                    "title": title,
                    "skill_area": skill_area,
                    "scenario_type": scenario_type,
                    "source_training_id": row["session_id"],
                    "score": row["score"],
                    "transfer_date": now,
                }
            )

        self.db.commit()

        return {
            "transferred": transferred,
            "skipped": skipped,
            "total_processed": transferred + skipped,
            "items": items,
        }

    def list_transferred(self, discipline: Optional[str] = None, limit: int = 20) -> list:
        if discipline:
            rows = self.db.execute(
                "SELECT * FROM training_transferred_memory WHERE skill_area = ? ORDER BY score DESC, transfer_date DESC LIMIT ?",
                (discipline, limit),
            ).fetchall()
        else:
            rows = self.db.execute(
                "SELECT * FROM training_transferred_memory ORDER BY score DESC, transfer_date DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_stats(self) -> dict:
        total_row = self.db.execute("SELECT COUNT(*) FROM training_transferred_memory").fetchone()
        total = total_row[0] if total_row else 0

        dist_rows = self.db.execute(
            "SELECT skill_area, COUNT(*) as cnt FROM training_transferred_memory GROUP BY skill_area ORDER BY cnt DESC"
        ).fetchall()
        discipline_dist = {r["skill_area"]: r["cnt"] for r in dist_rows}

        scenario_rows = self.db.execute(
            "SELECT scenario_type, COUNT(*) as cnt FROM training_transferred_memory GROUP BY scenario_type ORDER BY cnt DESC"
        ).fetchall()
        scenario_dist = {r["scenario_type"]: r["cnt"] for r in scenario_rows}

        avg_row = self.db.execute("SELECT AVG(score) FROM training_transferred_memory").fetchone()
        avg_score = round(avg_row[0], 2) if avg_row and avg_row[0] else 0.0

        latest = self.db.execute("SELECT * FROM training_transferred_memory ORDER BY transfer_date DESC LIMIT 1").fetchone()

        return {
            "total": total,
            "discipline_distribution": discipline_dist,
            "scenario_distribution": scenario_dist,
            "avg_score": avg_score,
            "latest_transfer": dict(latest) if latest else None,
        }

    def create_manual_memory(
        self,
        title: str,
        content: str,
        skill_area: str,
        scenario_type: str,
        source_training_id: Optional[int] = None,
    ) -> dict:
        if not title:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Title is required",
            )
        if not skill_area:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Skill area is required",
            )

        now = _now()
        cur = self.db.execute(
            "INSERT INTO training_transferred_memory "
            "(title, content, skill_area, scenario_type, source_training_id, score, transfer_date) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (title, content, skill_area, scenario_type, source_training_id, 0.0, now),
        )
        self.db.commit()

        row = self.db.execute(
            "SELECT * FROM training_transferred_memory WHERE id = ?",
            (cur.lastrowid,),
        ).fetchone()
        return dict(row)
