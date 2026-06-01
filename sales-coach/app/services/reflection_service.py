"""反思报告生成服务：对练结束后自动生成多维度评估和改进建议。"""

import json
import httpx
from datetime import datetime, timezone
from typing import Optional

AI_GATEWAY_URL = "http://localhost:8000/ai/chat"


def _calculate_dimension_scores(dialogue_log: list, compliance_violations: int, weights: Optional[dict] = None) -> dict:
    """从对话数据计算各维度分数。

    Args:
        dialogue_log: 对话历史列表。
        compliance_violations: 合规违规次数。
        weights: 可选权重配置。

    Returns:
        包含各维度分数的字典。
    """
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


def _generate_improvements(scores: dict, strengths_weaknesses: Optional[dict] = None) -> list:
    """根据弱项生成改进建议。

    Args:
        scores: 各维度分数。
        strengths_weaknesses: 可选的优势和弱项信息。

    Returns:
        按优先级排序的改进建议列表。
    """
    suggestions = []
    priority = 1

    thresholds = [
        ("compliance", "加强合规意识培训，熟记合规检查清单", 70),
        ("product_knowledge", "建议深入学习产品知识手册，增加产品培训频次", 65),
        ("communication", "提升沟通技巧，建议参加沟通表达专项训练", 60),
        ("objection_handling", "加强异议处理演练，模拟更多客户异议场景", 55),
    ]

    for dim, suggestion, threshold in thresholds:
        if scores.get(dim, 100) < threshold:
            suggestions.append({
                "priority": priority,
                "dimension": dim,
                "suggestion": suggestion,
            })
            priority += 1

    if not suggestions:
        suggestions.append({
            "priority": 1,
            "dimension": "overall",
            "suggestion": "整体表现良好，建议保持并挑战更高难度的场景",
        })

    if strengths_weaknesses and strengths_weaknesses.get("weaknesses"):
        for w in strengths_weaknesses["weaknesses"]:
            suggestions.append({
                "priority": priority,
                "dimension": "custom",
                "suggestion": f"针对弱项「{w}」制定专项提升计划",
            })
            priority += 1

    return suggestions


def _compare_with_history(session_id: int, current_scores: dict, db) -> dict:
    """与历史评分数据对比。

    Args:
        session_id: 当前会话ID。
        current_scores: 当前评分。
        db: 数据库连接。

    Returns:
        包含对比数据的字典。
    """
    try:
        rows = db.execute(
            "SELECT score, auto_assessment FROM coach_session "
            "WHERE id != ? AND auto_assessment IS NOT NULL "
            "ORDER BY id DESC LIMIT 10",
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


def generate_reflection_report(
    session_id: int,
    dialogue_log: list,
    compliance_violations: int,
    scenario: Optional[dict] = None,
    scoring_weights: Optional[dict] = None,
    ai_gateway_url: str = AI_GATEWAY_URL,
) -> dict:
    """生成反思报告。

    输入：会话ID、对话历史、合规违规次数、场景信息、评分权重
    返回报告结构：
    {
        "session_id": int,
        "generated_at": str,
        "summary": {"rounds": int, "duration_minutes": int, "scenario": str},
        "scores": {
            "product_knowledge": float,
            "communication": float,
            "compliance": float,
            "objection_handling": float,
            "overall": float
        },
        "strengths": [str],
        "weaknesses": [str],
        "improvements": [{"priority": 1, "suggestion": str}],
        "comparison": {"vs_average": float, "vs_best": float, "trend": str},
        "recommended_scenarios": [str]
    }
    """
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

    strengths = ai_suggestions.get("strengths", [
        "能够主动与客户建立沟通" if rounds > 2 else "态度积极",
        "基本掌握产品核心卖点" if dim_scores.get("product_knowledge", 0) > 60 else "有待提升",
        "对话流程基本完整",
    ])

    weaknesses = ai_suggestions.get("weaknesses", [
        "合规话术不够熟练" if violations > 0 else "无明显违规行为",
        "异议处理经验不足" if dim_scores.get("objection_handling", 0) < 70 else "异议处理表现良好",
        "产品知识深度有待加强" if dim_scores.get("product_knowledge", 0) < 75 else "产品知识扎实",
    ])

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


def _parse_ai_response(content: str) -> dict:
    """解析AI返回的文本内容，提取优势、弱项和改进建议。

    Args:
        content: AI返回的文本。

    Returns:
        包含strengths、weaknesses和improvements的字典。
    """
    result = {"strengths": [], "weaknesses": [], "improvements": []}
    if not content:
        return result
    lines = [l.strip() for l in content.split("\n") if l.strip()]
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
                result["improvements"].append({
                    "priority": priority,
                    "suggestion": text,
                })
                priority += 1
            elif current_section:
                result[current_section].append(text)
    return result


def _recommend_scenarios(scores: dict, weaknesses: list) -> list:
    """根据评分和弱项推荐场景。

    Args:
        scores: 各维度分数。
        weaknesses: 弱项列表。

    Returns:
        推荐场景列表。
    """
    recommended = []
    if scores.get("compliance", 100) < 80:
        recommended.append("合规话术专项训练")
    if scores.get("objection_handling", 100) < 70:
        recommended.append("异议处理强化场景")
    if scores.get("communication", 100) < 70:
        recommended.append("沟通技巧进阶练习")
    if scores.get("product_knowledge", 100) < 70:
        recommended.append("产品知识问答实战")
    if not recommended:
        recommended.append("高级综合销售场景")
    return recommended
