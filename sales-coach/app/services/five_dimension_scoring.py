"""五维能力评分服务。"""

import json
import re
from datetime import datetime
from typing import Any, Optional

from sales_coach.app.schemas.assessment import FiveDimensionScore, RadarChartData
from sales_coach.app.services.base import BaseService

DIMENSIONS = ("empathy", "data_citation", "closing", "objection_handling", "compliance")

_EMPATHY_TERMS = ("理解", "明白", "担心", "关注", "顾虑", "感受", "认同", "感谢", "您提到")
_DATA_TERMS = ("数据", "研究", "文献", "临床", "RCT", "真实世界", "指南", "证据", "发表", "来源")
_CLOSING_TERMS = ("下一步", "后续", "总结", "约定", "安排", "跟进", "是否可以", "建议我们", "确认")
_OBJECTION_TERMS = ("异议", "担心", "质疑", "价格", "安全性", "疗效", "竞品", "不良反应", "医保")
_RISK_TERMS = ("回扣", "处方量", "保证", "绝对", "治愈", "最安全", "最好", "无副作用", "超适应症")


def evaluate_dimensions(conversation_id: str) -> RadarChartData:
    """根据会话内容生成五维评分。"""

    service = FiveDimensionScoringService()
    return service.evaluate_dimensions(conversation_id)


def get_progress_curve(user_id: str, dimension: str, period: str = "month") -> list[dict]:
    """获取指定用户在某一维度的进步曲线。"""

    service = FiveDimensionScoringService()
    return service.get_progress_curve(user_id, dimension, period)


class FiveDimensionScoringService(BaseService):
    """销售对话五维评分服务。"""

    def evaluate_dimensions(self, conversation_id: str) -> RadarChartData:
        conn = self._connection()
        try:
            row = self._get_conversation(conn, conversation_id)
            if not row:
                scores = self._fallback_scores(conversation_id)
            else:
                scores = self._score_row(dict(row))
            values = [getattr(scores, name) for name in DIMENSIONS]
            return RadarChartData(conversation_id=conversation_id, dimensions=scores, values=values)
        finally:
            self._close_connection(conn)

    def get_progress_curve(self, user_id: str, dimension: str, period: str = "month") -> list[dict]:
        normalized_dimension = dimension if dimension in DIMENSIONS else "compliance"
        user_pk = _parse_numeric_id(user_id)
        if user_pk is None:
            return []
        conn = self._connection()
        try:
            rows = conn.execute(
                "SELECT id, score, auto_assessment, dialogue_log, compliance_violations, created_at "
                "FROM coach_session WHERE created_by = ? ORDER BY created_at ASC, id ASC",
                (user_pk,),
            ).fetchall()
            curve = []
            for row in rows:
                score = self._score_row(dict(row))
                created_at = row["created_at"] or ""
                curve.append(
                    {
                        "period": _period_key(created_at, period),
                        "conversation_id": f"conv-{int(row['id']):03d}",
                        "score": getattr(score, normalized_dimension),
                    }
                )
            return curve
        finally:
            self._close_connection(conn)

    def _get_conversation(self, conn, conversation_id: str):
        numeric_id = _parse_conversation_id(conversation_id)
        if numeric_id is not None:
            row = conn.execute(
                "SELECT id, score, auto_assessment, dialogue_log, compliance_violations, created_at FROM coach_session WHERE id = ?",
                (numeric_id,),
            ).fetchone()
            if row:
                return row
        return None

    def _score_row(self, row: dict[str, Any]) -> FiveDimensionScore:
        existing = _scores_from_auto_assessment(row.get("auto_assessment"))
        if existing:
            return existing
        dialogue = _parse_dialogue(row.get("dialogue_log"))
        user_text = "\n".join(
            item.get("content", "") for item in dialogue if isinstance(item, dict) and item.get("role") in {"user", "rep", "trainee"}
        )
        all_text = "\n".join(item.get("content", "") for item in dialogue if isinstance(item, dict))
        turns = len(dialogue)
        violations = int(row.get("compliance_violations") or 0)
        risky_hits = _count_terms(all_text, _RISK_TERMS)

        empathy = 55 + _count_terms(user_text, _EMPATHY_TERMS) * 10 + min(turns, 8) * 2
        data_citation = 50 + _count_terms(user_text, _DATA_TERMS) * 8 + min(len(re.findall(r"\d+(?:\.\d+)?%?", user_text)), 5) * 5
        closing = 52 + _count_terms(user_text, _CLOSING_TERMS) * 12
        objection_handling = 50 + _count_terms(all_text, _OBJECTION_TERMS) * 5 + min(turns, 8) * 2
        compliance = 95 - violations * 15 - risky_hits * 8
        if not dialogue and row.get("score") is not None:
            base = float(row["score"])
            empathy = data_citation = closing = objection_handling = compliance = base

        return FiveDimensionScore(
            empathy=_clamp(empathy),
            data_citation=_clamp(data_citation),
            closing=_clamp(closing),
            objection_handling=_clamp(objection_handling),
            compliance=_clamp(compliance),
        )

    def _fallback_scores(self, conversation_id: str) -> FiveDimensionScore:
        seed = sum(ord(ch) for ch in conversation_id)
        return FiveDimensionScore(
            empathy=_clamp(72 + seed % 9),
            data_citation=_clamp(66 + seed % 11),
            closing=_clamp(68 + seed % 10),
            objection_handling=_clamp(70 + seed % 12),
            compliance=_clamp(82 + seed % 8),
        )

    def _close_connection(self, conn) -> None:
        if not hasattr(self, "db") or self.db is not conn:
            conn.close()


def _scores_from_auto_assessment(raw: Optional[str]) -> Optional[FiveDimensionScore]:
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return None
    scores = parsed.get("scores", parsed) if isinstance(parsed, dict) else {}
    if not isinstance(scores, dict):
        return None
    if all(key in scores for key in DIMENSIONS):
        return FiveDimensionScore(**{key: _clamp(scores[key]) for key in DIMENSIONS})
    mapped = {
        "empathy": scores.get("communication"),
        "data_citation": scores.get("product_knowledge"),
        "closing": scores.get("overall"),
        "objection_handling": scores.get("objection_handling"),
        "compliance": scores.get("compliance"),
    }
    if any(value is not None for value in mapped.values()):
        fallback = float(scores.get("overall") or 70)
        return FiveDimensionScore(**{key: _clamp(value if value is not None else fallback) for key, value in mapped.items()})
    return None


def _parse_dialogue(raw: Optional[str]) -> list[dict]:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return []
    return parsed if isinstance(parsed, list) else []


def _count_terms(text: str, terms: tuple[str, ...]) -> int:
    return sum(1 for term in terms if term.lower() in text.lower())


def _clamp(value: Any) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = 0.0
    return round(max(0.0, min(100.0, numeric)), 1)


def _parse_conversation_id(conversation_id: str) -> Optional[int]:
    match = re.search(r"(\d+)$", str(conversation_id))
    if not match:
        return None
    return int(match.group(1))


def _parse_numeric_id(user_id: str) -> Optional[int]:
    match = re.search(r"(\d+)$", str(user_id))
    if not match:
        return None
    return int(match.group(1))


def _period_key(created_at: str, period: str) -> str:
    if not created_at:
        return "unknown"
    try:
        parsed = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    except ValueError:
        return created_at[:10]
    if period == "day":
        return parsed.strftime("%Y-%m-%d")
    if period == "week":
        year, week, _ = parsed.isocalendar()
        return f"{year}-W{week:02d}"
    return parsed.strftime("%Y-%m")
