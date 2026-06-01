import json
import urllib.error
import urllib.request
from typing import Optional

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import (
    TrainingAttributionsRepository,
    TrainingModulesRepository,
    TrainingSessionsRepository,
    UsersRepository,
)
from cloud.app.services.base import BaseService
from shared.config import settings
from shared.base import PaginatedResponse

DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
TIMEOUT_SECONDS = 30

DIFFICULTY_LEVELS = ["beginner", "medium", "advanced", "expert"]

MODULE_COLS = [
    "id", "title", "category", "difficulty", "content", "prerequisites",
    "passing_score", "estimated_minutes", "is_active", "created_by",
    "created_at", "updated_at",
]
SESSION_COLS = [
    "id", "user_id", "module_id", "score", "passed", "time_spent_seconds",
    "answers", "feedback", "difficulty_used", "next_difficulty",
    "completed_at", "created_at",
]
ATTR_COLS = [
    "id", "user_id", "training_session_id", "metric_name", "metric_before",
    "metric_after", "change_pct", "attribution_score", "confidence",
    "analysis", "period_days", "created_at",
]


class TrainingCoachService(BaseService):

    @staticmethod
    def _rd(row, cols):
        if row is None:
            return None
        d = dict(row) if not isinstance(row, dict) else row
        for key in ("prerequisites", "answers"):
            if key in d and isinstance(d[key], str):
                d[key] = json.loads(d[key])
        return d

    @staticmethod
    def _calc_next_difficulty(score: float, current: str) -> str:
        idx = DIFFICULTY_LEVELS.index(current) if current in DIFFICULTY_LEVELS else 1
        if score >= 0.9 and idx < len(DIFFICULTY_LEVELS) - 1:
            return DIFFICULTY_LEVELS[idx + 1]
        if score <= 0.5 and idx > 0:
            return DIFFICULTY_LEVELS[idx - 1]
        return current

    @staticmethod
    def _call_ai(system_prompt: str, user_prompt: str) -> str:
        api_key = settings.deepseek_api_key
        if not api_key:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail="DEEPSEEK_API_KEY not configured")
        req_body = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 2048,
        }
        req = urllib.request.Request(
            DEEPSEEK_URL,
            data=json.dumps(req_body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
                payload = json.loads(resp.read())
        except urllib.error.URLError as exc:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=f"AI call failed: {exc}")
        choices = payload.get("choices", [])
        return choices[0].get("message", {}).get("content", "") if choices else ""

    @staticmethod
    def _suggest_diff(avg_score: float) -> str:
        if avg_score >= 0.8:
            return "expert"
        if avg_score >= 0.6:
            return "advanced"
        if avg_score >= 0.4:
            return "medium"
        return "beginner"

    def create_module(self, title: str, category: str, difficulty: str,
                      content: str, prerequisites: list, passing_score: float,
                      estimated_minutes: int, created_by: int) -> dict:
        modules_repo = TrainingModulesRepository(self.db)
        module_id = modules_repo.create({
            "title": title,
            "category": category,
            "difficulty": difficulty,
            "content": content,
            "prerequisites": json.dumps(prerequisites, ensure_ascii=False),
            "passing_score": passing_score,
            "estimated_minutes": estimated_minutes,
            "created_by": created_by,
        })
        row = modules_repo.get_by_id(module_id)
        return self._rd(row, MODULE_COLS)

    def list_modules(self, category: Optional[str] = None,
                     difficulty: Optional[str] = None) -> list:
        modules_repo = TrainingModulesRepository(self.db)
        conditions = ["is_active=1"]
        params = []
        if category:
            conditions.append("category=?")
            params.append(category)
        if difficulty:
            conditions.append("difficulty=?")
            params.append(difficulty)
        rows = modules_repo.list_all(conditions=conditions, params=params, order_by="id ASC")
        return [self._rd(r, MODULE_COLS) for r in rows]

    def create_session(self, user_id: int, module_id: int, score: float,
                       passed: int, time_spent_seconds: int, answers: list,
                       feedback: str, difficulty_used: str) -> dict:
        modules_repo = TrainingModulesRepository(self.db)
        sessions_repo = TrainingSessionsRepository(self.db)

        mod = modules_repo.get_by_id(module_id)
        if not mod or not mod.get("is_active"):
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Module not found")
        next_diff = self._calc_next_difficulty(score, difficulty_used)
        session_id = sessions_repo.create({
            "user_id": user_id,
            "module_id": module_id,
            "score": score,
            "passed": passed,
            "time_spent_seconds": time_spent_seconds,
            "answers": json.dumps(answers, ensure_ascii=False),
            "feedback": feedback,
            "difficulty_used": difficulty_used,
            "next_difficulty": next_diff,
        })
        row = sessions_repo.get_by_id(session_id)
        return self._rd(row, SESSION_COLS)

    def list_sessions(self, user_id: Optional[int] = None,
                      module_id: Optional[int] = None,
                      page: int = 1, page_size: int = 20) -> dict:
        sessions_repo = TrainingSessionsRepository(self.db)
        conditions = []
        params = []
        if user_id is not None:
            conditions.append("user_id=?")
            params.append(user_id)
        if module_id is not None:
            conditions.append("module_id=?")
            params.append(module_id)
        total, total_pages, rows = sessions_repo.paginate(
            page=page, page_size=page_size,
            conditions=conditions or None, params=params or None,
            order_by="created_at DESC",
        )
        return {
            "items": [self._rd(r, SESSION_COLS) for r in rows],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    def get_session(self, session_id: int) -> dict:
        sessions_repo = TrainingSessionsRepository(self.db)
        row = sessions_repo.get_by_id(session_id)
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Session not found")
        return self._rd(row, SESSION_COLS)

    def recommend(self, user_id: int) -> dict:
        sessions_repo = TrainingSessionsRepository(self.db)
        modules_repo = TrainingModulesRepository(self.db)

        rows = sessions_repo.list_all(
            conditions=["user_id=?"], params=[user_id], order_by="created_at DESC"
        )
        rows = rows[:3]
        if not rows:
            mods = modules_repo.list_all(
                conditions=["is_active=1"], order_by="id ASC"
            )
            return {
                "recommended": self._rd(mods[0], MODULE_COLS) if mods else None,
                "reason": "no_history",
                "avg_score": None,
                "suggested_difficulty": "beginner",
            }
        avg_score = sum(r["score"] for r in rows) / len(rows)
        suggested = self._suggest_diff(avg_score)
        completed_ids = [r["module_id"] for r in rows]
        ph = ",".join("?" * len(completed_ids))
        candidates = self.db.execute(
            f"SELECT * FROM training_modules WHERE is_active=1 AND id NOT IN ({ph}) "
            f"ORDER BY CASE WHEN difficulty='{suggested}' THEN 0 ELSE 1 END, id LIMIT 1",
            completed_ids,
        ).fetchall()
        rec = self._rd(candidates[0], MODULE_COLS) if candidates else None
        return {
            "recommended": rec,
            "reason": "based_on_score",
            "avg_score": round(avg_score, 2),
            "suggested_difficulty": suggested,
        }

    def create_attribution(self, user_id: int, metric_name: str,
                           metric_before: float, metric_after: float,
                           period_days: int) -> dict:
        attrs_repo = TrainingAttributionsRepository(self.db)
        cp = round((metric_after - metric_before) / metric_before, 4) if metric_before else 0.0
        att_id = attrs_repo.create({
            "user_id": user_id,
            "metric_name": metric_name,
            "metric_before": metric_before,
            "metric_after": metric_after,
            "change_pct": cp,
            "period_days": period_days,
        })
        row = attrs_repo.get_by_id(att_id)
        return self._rd(row, ATTR_COLS)

    def list_attributions(self, user_id: Optional[int] = None,
                          metric_name: Optional[str] = None) -> list:
        attrs_repo = TrainingAttributionsRepository(self.db)
        conditions = []
        params = []
        if user_id is not None:
            conditions.append("user_id=?")
            params.append(user_id)
        if metric_name:
            conditions.append("metric_name=?")
            params.append(metric_name)
        rows = attrs_repo.list_all(
            conditions=conditions or None, params=params or None,
            order_by="created_at DESC",
        )
        return [self._rd(r, ATTR_COLS) for r in rows]

    def analyze_attribution(self, att_id: int) -> dict:
        attrs_repo = TrainingAttributionsRepository(self.db)
        users_repo = UsersRepository(self.db)

        attr_row = attrs_repo.get_by_id(att_id)
        if not attr_row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Attribution not found")
        user_row = users_repo.get_by_id(attr_row["user_id"])
        username = user_row["username"] if user_row else "unknown"
        sys_prompt = ("你是一名培训效果分析专家。请对培训前后指标变化进行深入分析，评估培训效果贡献度。"
                      "输出JSON格式：{\"attribution_score\":0.8,\"analysis\":\"...\"}，"
                      "attribution_score为0-1之间表示培训贡献度，analysis为详细分析文本。")
        user_prompt = (f"用户：{username}\n指标：{attr_row['metric_name']}\n"
                       f"培训前：{attr_row['metric_before']}\n培训后：{attr_row['metric_after']}\n"
                       f"变化率：{attr_row['change_pct']}\n统计周期：{attr_row['period_days']}天\n"
                       "请分析该指标变化中培训的贡献程度，并给出详细分析。")
        try:
            result = json.loads(self._call_ai(sys_prompt, user_prompt))
            a_score = float(result.get("attribution_score", 0.0))
            analysis = str(result.get("analysis", ""))
        except Exception:
            ch = abs(attr_row["change_pct"])
            a_score = 0.8 if ch > 0.3 else (0.5 if ch > 0.1 else (0.3 if ch > 0.05 else 0.1))
            analysis = f"指标{attr_row['metric_name']}变化率{attr_row['change_pct']}，基于变化率自动评估培训贡献度。"
        conf = round(min(abs(attr_row["change_pct"]) * 100, 100) / 100, 2)
        attrs_repo.update(att_id, {
            "attribution_score": a_score,
            "analysis": analysis,
            "confidence": conf,
        })
        row = attrs_repo.get_by_id(att_id)
        return self._rd(row, ATTR_COLS)

    def dashboard(self) -> dict:
        modules_repo = TrainingModulesRepository(self.db)
        sessions_repo = TrainingSessionsRepository(self.db)

        tm = modules_repo.count(conditions=["is_active=1"])
        ts = sessions_repo.count()
        tu = self.db.execute("SELECT COUNT(DISTINCT user_id) FROM training_sessions").fetchone()[0]
        asr = self.db.execute("SELECT AVG(score) FROM training_sessions").fetchone()
        avg = round(asr[0], 2) if asr[0] else 0.0
        prr = self.db.execute(
            "SELECT CAST(SUM(passed) AS REAL)/NULLIF(COUNT(*),0) FROM training_sessions"
        ).fetchone()
        pr = round(prr[0], 2) if prr and prr[0] else 0.0
        cd = {
            r["category"]: r["cnt"]
            for r in self.db.execute(
                "SELECT category,COUNT(*) cnt FROM training_modules WHERE is_active=1 GROUP BY category"
            ).fetchall()
        }
        recent = sessions_repo.list_all(order_by="created_at DESC")
        recent = recent[:5]
        return {
            "total_modules": tm,
            "total_sessions": ts,
            "total_trainees": tu,
            "avg_score": avg,
            "pass_rate": pr,
            "module_category_distribution": cd,
            "recent_sessions": [self._rd(r, SESSION_COLS) for r in recent],
        }
