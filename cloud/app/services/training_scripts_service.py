"""培训脚本服务管理培训脚本的创建与执行。"""

import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from cloud.app.repositories import (
    TrainingRoiAnalysisRepository,
    TrainingScriptsRepository,
)
from cloud.app.services.base import BaseService


class TrainingScriptsService(BaseService):
    def extract_scripts(self, source_agent_role: str, min_score: float, user_id: int) -> dict:
        rows = self.db.execute(
            """SELECT cs.session_id, cs.source_agent_role, cs.result_summary,
                      cs.total_steps, cs.completed_steps, cs.involved_agents
               FROM collaboration_sessions cs
               WHERE cs.status = 'completed'
                 AND cs.source_agent_role = ?
                 AND cs.result_summary != ''
               ORDER BY cs.completed_at DESC""",
            (source_agent_role,),
        ).fetchall()

        scripts_repo = TrainingScriptsRepository(self.db)
        now = datetime.now(timezone.utc).isoformat()
        created = []

        for row in rows:
            steps = []
            total = row["total_steps"] or 0
            score_val = round(min((row["completed_steps"] or 0) / max(total, 1), 1.0), 2)
            if score_val < min_score:
                continue
            if total > 0:
                for i in range(1, total + 1):
                    steps.append({"step": i, "action": f"步骤{i}：执行协作任务"})
                try:
                    involved = json.loads(row["involved_agents"] or "[]")
                    if involved:
                        for idx, agent in enumerate(involved):
                            if idx < len(steps):
                                steps[idx]["agent"] = agent
                except (json.JSONDecodeError, TypeError):
                    pass

            script_id = f"ts:extract:{uuid.uuid4().hex[:8]}"
            script_name = f"协作剧本-{row['source_agent_role']}"
            description = (row["result_summary"] or "")[:200]
            involved_agents = row["involved_agents"] or "[]"
            try:
                target_roles = json.dumps(list(set(json.loads(involved_agents))), ensure_ascii=False)
            except (json.JSONDecodeError, TypeError):
                target_roles = "[]"

            script_data = {
                "script_id": script_id,
                "script_name": script_name,
                "source_agent_role": row["source_agent_role"],
                "source_collaboration_id": row["session_id"],
                "description": description,
                "steps": json.dumps(steps, ensure_ascii=False),
                "difficulty": "mid",
                "target_roles": target_roles,
                "score": score_val,
                "created_by": user_id,
                "created_at": now,
                "updated_at": now,
            }
            existing = self.db.execute("SELECT id FROM training_scripts WHERE script_id=?", (script_id,)).fetchone()
            if not existing:
                scripts_repo.create(script_data)
                created.append(
                    {
                        "script_id": script_id,
                        "script_name": script_name,
                        "score": score_val,
                    }
                )

        return {"created_count": len(created), "scripts": created}

    def list_scripts(
        self,
        page: int = 1,
        page_size: int = 20,
        source_agent_role: Optional[str] = None,
        difficulty: Optional[str] = None,
        target_roles: Optional[str] = None,
    ) -> dict:
        scripts_repo = TrainingScriptsRepository(self.db)

        conditions = []
        params = []
        if source_agent_role:
            conditions.append("source_agent_role = ?")
            params.append(source_agent_role)
        if difficulty:
            conditions.append("difficulty = ?")
            params.append(difficulty)
        if target_roles:
            conditions.append("target_roles LIKE ?")
            params.append(f"%{target_roles}%")

        total, total_pages, rows = scripts_repo.paginate(
            page=page,
            page_size=page_size,
            conditions=conditions or None,
            params=params or None,
            order_by="id DESC",
        )

        return {
            "items": [dict(r) for r in rows],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    def analyze_roi(self, period_start: str, period_end: str) -> dict:
        roi_repo = TrainingRoiAnalysisRepository(self.db)
        now = datetime.now(timezone.utc).isoformat()

        training_row = self.db.execute(
            """SELECT COUNT(*) as sessions, COALESCE(SUM(time_spent_seconds), 0) as total_seconds
               FROM training_sessions
               WHERE completed_at >= ? AND completed_at <= ?""",
            (period_start, period_end),
        ).fetchone()

        participants = training_row["sessions"] or 1
        total_seconds = training_row["total_seconds"] or 0
        training_hours = round(total_seconds / 3600.0, 2)

        behavior_change_score = round(min(participants * 0.016, 1.0), 2)

        sales_impact = round(participants * 3333.33, 2)
        cost_savings = round(participants * 666.67, 2)
        roi_val = round((sales_impact + cost_savings) / max(training_hours or 1, 1), 2)

        analysis_id = f"roi:analyze:{uuid.uuid4().hex[:8]}"

        roi_repo.create(
            {
                "analysis_id": analysis_id,
                "period_start": period_start,
                "period_end": period_end,
                "training_hours": training_hours,
                "participants": participants,
                "behavior_change_score": behavior_change_score,
                "sales_impact": sales_impact,
                "cost_savings": cost_savings,
                "roi": roi_val,
                "metadata": json.dumps({"method": "simulation", "source": "auto"}, ensure_ascii=False),
                "created_at": now,
            }
        )

        return {
            "analysis_id": analysis_id,
            "period_start": period_start,
            "period_end": period_end,
            "training_hours": training_hours,
            "participants": participants,
            "behavior_change_score": behavior_change_score,
            "sales_impact": sales_impact,
            "cost_savings": cost_savings,
            "roi": roi_val,
        }

    def list_roi(self, page: int = 1, page_size: int = 20) -> dict:
        roi_repo = TrainingRoiAnalysisRepository(self.db)

        total, total_pages, rows = roi_repo.paginate(
            page=page,
            page_size=page_size,
            order_by="id DESC",
        )

        return {
            "items": [dict(r) for r in rows],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }
