import json
import urllib.error
import urllib.request

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import (
    TrainingAttributionsRepository,
    TrainingModulesRepository,
    TrainingSessionsRepository,
    UsersRepository,
)
from shared.config import settings

DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
TIMEOUT_SECONDS = 30

ATTR_COLS = [
    "id",
    "user_id",
    "training_session_id",
    "metric_name",
    "metric_before",
    "metric_after",
    "change_pct",
    "attribution_score",
    "confidence",
    "analysis",
    "period_days",
    "created_at",
]
SESSION_COLS = [
    "id",
    "user_id",
    "module_id",
    "score",
    "passed",
    "time_spent_seconds",
    "answers",
    "feedback",
    "difficulty_used",
    "next_difficulty",
    "completed_at",
    "created_at",
]


class CoachGap:
    @staticmethod
    def _call_ai(system_prompt: str, user_prompt: str) -> str:
        api_key = settings.deepseek_api_key
        if not api_key:
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="DEEPSEEK_API_KEY not configured",
            )
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

    def analyze_attribution(self, att_id: int) -> dict:
        attrs_repo = TrainingAttributionsRepository(self.db)
        users_repo = UsersRepository(self.db)

        attr_row = attrs_repo.get_by_id(att_id)
        if not attr_row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Attribution not found")
        user_row = users_repo.get_by_id(attr_row["user_id"])
        username = user_row["username"] if user_row else "unknown"
        sys_prompt = (
            "你是一名培训效果分析专家。请对培训前后指标变化进行深入分析，评估培训效果贡献度。"
            '输出JSON格式：{"attribution_score":0.8,"analysis":"..."}，'
            "attribution_score为0-1之间表示培训贡献度，analysis为详细分析文本。"
        )
        user_prompt = (
            f"用户：{username}\n指标：{attr_row['metric_name']}\n"
            f"培训前：{attr_row['metric_before']}\n培训后：{attr_row['metric_after']}\n"
            f"变化率：{attr_row['change_pct']}\n统计周期：{attr_row['period_days']}天\n"
            "请分析该指标变化中培训的贡献程度，并给出详细分析。"
        )
        try:
            result = json.loads(self._call_ai(sys_prompt, user_prompt))
            a_score = float(result.get("attribution_score", 0.0))
            analysis = str(result.get("analysis", ""))
        except Exception:
            ch = abs(attr_row["change_pct"])
            a_score = 0.8 if ch > 0.3 else (0.5 if ch > 0.1 else (0.3 if ch > 0.05 else 0.1))
            analysis = f"指标{attr_row['metric_name']}变化率{attr_row['change_pct']}，基于变化率自动评估培训贡献度。"
        conf = round(min(abs(attr_row["change_pct"]) * 100, 100) / 100, 2)
        attrs_repo.update(
            att_id,
            {
                "attribution_score": a_score,
                "analysis": analysis,
                "confidence": conf,
            },
        )
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
        prr = self.db.execute("SELECT CAST(SUM(passed) AS REAL)/NULLIF(COUNT(*),0) FROM training_sessions").fetchone()
        pr = round(prr[0], 2) if prr and prr[0] else 0.0
        cd = {
            r["category"]: r["cnt"]
            for r in self.db.execute("SELECT category,COUNT(*) cnt FROM training_modules WHERE is_active=1 GROUP BY category").fetchall()
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
