"""反思评分模块，基于对话日志计算维度评分并生成反思报告。"""

import json
from datetime import datetime, timezone
from typing import Optional

import httpx

from shared.app_settings import settings

AI_GATEWAY_URL = f"{settings.cloud_api_base}/ai/chat"


def _calculate_dimension_scores(dialogue_log: list, compliance_violations: int, weights: Optional[dict] = None) -> dict:
    rounds = len(dialogue_log) if dialogue_log else 0
    violations = compliance_violations or 0

    product_knowledge = max(0, min(100, 70 + rounds * 2 - violations * 5))
    communication = max(0, min(100, 65 + rounds * 1.5 - violations * 3))
    compliance = max(0, min(100, 100 - violations * 20))
    objection_handling = max(0, min(100, 60 + rounds * 2.5 - violations * 4))

    return {
        "product_knowledge": round(product_knowledge, 1),
        "communication": round(communication, 1),
        "compliance": round(compliance, 1),
        "objection_handling": round(objection_handling, 1),
    }


def _compare_with_history(session_id: int, current_scores: dict, db) -> dict:
    try:
        rows = db.execute(
            "SELECT score, auto_assessment FROM coach_session WHERE id != ? AND auto_assessment IS NOT NULL ORDER BY id DESC LIMIT 10",
            (session_id,),
        ).fetchall()
    except Exception:
        rows = []

    if not rows:
        return {"vs_average": 0, "vs_best": 0, "trend": "stable"}

    overall = current_scores.get("overall", 0)
    scores = []
    for r in rows:
        try:
            aa = json.loads(r["auto_assessment"])
            scores.append(aa.get("overall", aa.get("score", r["score"] or 0)))
        except (json.JSONDecodeError, TypeError, AttributeError):
            scores.append(r["score"] or 0)

    avg_score = sum(scores) / len(scores) if scores else 0
    best_score = max(scores) if scores else 0

    vs_average = round(overall - avg_score, 1)
    vs_best = round(overall - best_score, 1)

    if len(scores) >= 3 and scores[-1] < scores[-3]:
        trend = "declining"
    elif len(scores) >= 3 and scores[-1] > scores[-3]:
        trend = "improving"
    else:
        trend = "stable"

    return {"vs_average": vs_average, "vs_best": vs_best, "trend": trend}


def _parse_ai_response(content: str) -> dict:
    result = {"strengths": [], "weaknesses": [], "improvements": []}
    if not content:
        return result
    lines = [ln.strip() for ln in content.split("\n") if ln.strip()]
    current_section = None
    priority = 1
    for line in lines:
        lower = line.lower()
        if "优势" in lower or "strength" in lower:
            current_section = "strengths"
        elif "弱项" in lower or "weakness" in lower:
            current_section = "weaknesses"
        elif "改进" in lower or "improvement" in lower or "建议" in lower:
            current_section = "improvements"
        elif line.startswith("-") or line.startswith("*") or line[0].isdigit():
            text = line.lstrip("-*0123456789. ")
            if current_section == "improvements":
                result["improvements"].append(
                    {
                        "priority": priority,
                        "suggestion": text,
                    }
                )
                priority += 1
            elif current_section:
                result[current_section].append(text)
    return result


def generate_reflection_report(
    session_id: int,
    dialogue_log: list,
    compliance_violations: int,
    scenario: Optional[dict] = None,
    scoring_weights: Optional[dict] = None,
    ai_gateway_url: str = AI_GATEWAY_URL,
) -> dict:
    from sales_coach.app.services.reflection_feedback import _generate_improvements, _recommend_scenarios

    rounds = len(dialogue_log) if dialogue_log else 0
    duration_minutes = rounds * 2
    violations = compliance_violations or 0
    scenario_title = (scenario or {}).get("title", "")

    dim_scores = _calculate_dimension_scores(dialogue_log, violations, scoring_weights)

    weights = scoring_weights or {
        "product_knowledge": 0.3,
        "communication": 0.25,
        "compliance": 0.25,
        "objection_handling": 0.2,
    }
    overall = sum(dim_scores[k] * weights[k] for k in weights if k in dim_scores)
    dim_scores["overall"] = round(overall, 1)

    ai_suggestions = {}
    try:
        prompt = (
            f"分析以下销售对话记录（共{rounds}轮，合规违规{violations}次）。"
            f"请给出3条优势、3条弱项和3个改进建议。"
            f"对话内容：{json.dumps(dialogue_log, ensure_ascii=False)[:2000]}"
        )
        resp = httpx.post(
            ai_gateway_url,
            json={"messages": [{"role": "user", "content": prompt}]},
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            ai_content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            if data.get("data") and data["data"].get("choices"):
                ai_content = data["data"]["choices"][0].get("message", {}).get("content", "")
            ai_suggestions = _parse_ai_response(ai_content)
    except Exception:
        ai_suggestions = {}

    strengths = ai_suggestions.get(
        "strengths",
        [
            "能够主动与客户建立沟通" if rounds > 2 else "态度积极",
            "基本掌握产品核心卖点" if dim_scores.get("product_knowledge", 0) > 60 else "有待提升",
            "对话流程基本完整",
        ],
    )

    weaknesses = ai_suggestions.get(
        "weaknesses",
        [
            "合规话术不够熟练" if violations > 0 else "无明显违规行为",
            "异议处理经验不足" if dim_scores.get("objection_handling", 0) < 70 else "异议处理表现良好",
            "产品知识深度有待加强" if dim_scores.get("product_knowledge", 0) < 75 else "产品知识扎实",
        ],
    )

    improvements = ai_suggestions.get("improvements", _generate_improvements(dim_scores))

    comparison = _compare_with_history(session_id, dim_scores, None)

    recommended = _recommend_scenarios(dim_scores, weaknesses)

    return {
        "session_id": session_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "rounds": rounds,
            "duration_minutes": duration_minutes,
            "scenario": scenario_title,
        },
        "scores": dim_scores,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "improvements": improvements,
        "comparison": comparison,
        "recommended_scenarios": recommended,
    }
