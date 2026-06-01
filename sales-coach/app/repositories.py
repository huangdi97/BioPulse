import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from shared.columns import (
    TABLE_COACH_SCENARIO_COLS,
    TABLE_COACH_SESSION_COLS,
    TABLE_EDUCATION_ASSESSMENT_COLS,
    TABLE_TRAINING_MODULE_COLS,
)
from shared.repository import BaseRepository


class ModuleRepository(BaseRepository):
    def __init__(self, db: sqlite3.Connection):
        super().__init__(db, "training_module", TABLE_TRAINING_MODULE_COLS)

    def get_active_by_id(self, module_id: int) -> Optional[sqlite3.Row]:
        return self.db.execute(
            "SELECT * FROM training_module WHERE id = ? AND is_active = 1",
            (module_id,),
        ).fetchone()

    def get_active_or_404(self, module_id: int) -> sqlite3.Row:
        row = self.get_active_by_id(module_id)
        if not row:
            from fastapi import HTTPException
            from starlette import status

            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Module not found")
        return row

    def soft_delete_module(self, module_id: int) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self.db.execute(
            "UPDATE training_module SET is_active = 0, updated_at = ? WHERE id = ?",
            (now, module_id),
        )
        self.db.commit()

    def list_active(self, conditions=None, params=None, order_by="id DESC"):
        conds = ["is_active = 1"]
        if conditions:
            conds.extend(conditions)
        return self.list_all(conditions=conds, params=params, order_by=order_by)

    def paginate_active(
        self, page=1, page_size=20, conditions=None, params=None, order_by="id DESC"
    ):
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


class ScenarioRepository(BaseRepository):
    def __init__(self, db: sqlite3.Connection):
        super().__init__(db, "coach_scenario", TABLE_COACH_SCENARIO_COLS)

    def get_active_by_id(self, scenario_id: int) -> Optional[sqlite3.Row]:
        return self.db.execute(
            "SELECT * FROM coach_scenario WHERE id = ? AND is_active = 1",
            (scenario_id,),
        ).fetchone()

    def get_active_or_404(self, scenario_id: int) -> sqlite3.Row:
        row = self.get_active_by_id(scenario_id)
        if not row:
            from fastapi import HTTPException
            from starlette import status

            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Scenario not found")
        return row

    def soft_delete_scenario(self, scenario_id: int) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self.db.execute(
            "UPDATE coach_scenario SET is_active = 0, updated_at = ? WHERE id = ?",
            (now, scenario_id),
        )
        self.db.commit()

    def list_active(self, conditions=None, params=None, order_by="id DESC"):
        conds = ["is_active = 1"]
        if conditions:
            conds.extend(conditions)
        return self.list_all(conditions=conds, params=params, order_by=order_by)

    def paginate_active(
        self, page=1, page_size=20, conditions=None, params=None, order_by="id DESC"
    ):
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


class SessionRepository(BaseRepository):
    def __init__(self, db: sqlite3.Connection):
        super().__init__(db, "coach_session", TABLE_COACH_SESSION_COLS)

    def get_session_or_404(self, session_id: int) -> sqlite3.Row:
        row = self.get_by_id(session_id)
        if not row:
            from fastapi import HTTPException
            from starlette import status

            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Session not found")
        return row

    def list_by_module(self, module_id: int, order_by="id DESC"):
        return self.db.execute(
            "SELECT * FROM coach_session WHERE module_id = ? ORDER BY " + order_by,
            (module_id,),
        ).fetchall()

    def paginate_by_module(
        self, module_id: int, page=1, page_size=20, order_by="id DESC"
    ):
        total = self.db.execute(
            "SELECT COUNT(*) FROM coach_session WHERE module_id = ?",
            (module_id,),
        ).fetchone()[0]
        total_pages = max(1, (total + page_size - 1) // page_size)
        offset = (page - 1) * page_size
        rows = self.db.execute(
            "SELECT * FROM coach_session WHERE module_id = ? ORDER BY "
            + order_by
            + " LIMIT ? OFFSET ?",
            (module_id, page_size, offset),
        ).fetchall()
        return total, total_pages, rows

    def hard_delete(self, session_id: int) -> None:
        self.db.execute("DELETE FROM coach_session WHERE id = ?", (session_id,))
        self.db.commit()


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

            raise HTTPException(
                status.HTTP_404_NOT_FOUND, detail="Assessment not found"
            )
        return row

    def soft_delete_assessment(self, assessment_id: int) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self.db.execute(
            "UPDATE education_assessment SET is_active = 0, updated_at = ? "
            "WHERE id = ?",
            (now, assessment_id),
        )
        self.db.commit()

    def list_active(self, conditions=None, params=None, order_by="id DESC"):
        conds = ["is_active = 1"]
        if conditions:
            conds.extend(conditions)
        return self.list_all(conditions=conds, params=params, order_by=order_by)

    def paginate_active(
        self, page=1, page_size=20, conditions=None, params=None, order_by="id DESC"
    ):
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

        total = self.db.execute(
            "SELECT COUNT(*) FROM education_assessment WHERE is_active = 1"
        ).fetchone()[0]

        dist_rows = self.db.execute(
            "SELECT current_level, COUNT(*) as cnt "
            "FROM education_assessment WHERE is_active = 1 "
            "GROUP BY current_level"
        ).fetchall()
        level_dist = {r["current_level"]: r["cnt"] for r in dist_rows}

        weakness_rows = self.db.execute(
            "SELECT weaknesses FROM education_assessment "
            "WHERE is_active = 1 AND weaknesses IS NOT NULL AND weaknesses != ''"
        ).fetchall()
        counter: Counter = Counter()
        for row in weakness_rows:
            for w in row["weaknesses"].split(","):
                stripped = w.strip()
                if stripped:
                    counter[stripped] += 1
        top_weaknesses = [
            {"weakness": w, "count": c} for w, c in counter.most_common(10)
        ]

        recent = self.db.execute(
            "SELECT COUNT(*) FROM education_assessment "
            "WHERE assessment_date >= date('now', '-30 days') AND is_active = 1"
        ).fetchone()[0]

        return {
            "total_assessments": total,
            "level_distribution": level_dist,
            "top_weaknesses": top_weaknesses,
            "recent_assessments": recent,
        }


class StatsRepository:
    def __init__(self, db: sqlite3.Connection):
        self.db = db

    def get_coach_stats(self) -> Dict[str, Any]:
        row = self.db.execute(
            "SELECT COUNT(*) as cnt, AVG(score) as avg FROM coach_session"
        ).fetchone()
        total = row["cnt"]
        avg_score = round(row["avg"] or 0, 1)

        mod_rows = self.db.execute(
            "SELECT cs.module_id, tm.title AS module_title, "
            "COUNT(*) as cnt, AVG(cs.score) as avg_score "
            "FROM coach_session cs "
            "LEFT JOIN training_module tm ON cs.module_id = tm.id "
            "GROUP BY cs.module_id"
        ).fetchall()
        module_distribution = [
            {
                "module_id": r["module_id"],
                "module_title": r["module_title"] or "",
                "count": r["cnt"],
                "avg_score": round(r["avg_score"] or 0, 1),
            }
            for r in mod_rows
        ]

        trainee_rows = self.db.execute(
            "SELECT trainee_name, AVG(score) as avg_score, "
            "COUNT(*) as session_count "
            "FROM coach_session "
            "WHERE trainee_name IS NOT NULL AND trainee_name != '' "
            "GROUP BY trainee_name "
            "ORDER BY avg_score DESC LIMIT 10"
        ).fetchall()
        top_trainees = [
            {
                "trainee_name": r["trainee_name"],
                "avg_score": round(r["avg_score"] or 0, 1),
                "session_count": r["session_count"],
            }
            for r in trainee_rows
        ]

        dist_rows = self.db.execute(
            "SELECT "
            "  CASE "
            "    WHEN score >= 90 THEN '90-100' "
            "    WHEN score >= 80 THEN '80-89' "
            "    WHEN score >= 70 THEN '70-79' "
            "    WHEN score >= 60 THEN '60-69' "
            "    ELSE '<60' "
            "  END as score_range, "
            "  COUNT(*) as cnt "
            "FROM coach_session "
            "GROUP BY score_range"
        ).fetchall()

        score_dist = {"90-100": 0, "80-89": 0, "70-79": 0, "60-69": 0, "<60": 0}
        for r in dist_rows:
            score_dist[r["score_range"]] = r["cnt"]

        return {
            "total_assessments": total,
            "average_score": avg_score,
            "module_distribution": module_distribution,
            "top_trainees": top_trainees,
            "score_distribution": score_dist,
        }
