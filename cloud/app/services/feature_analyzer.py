"""特征分析模块，提供因果归因、动态演化预测等时间序列分析功能。"""

from collections import Counter

from .feature_extractor import QUALITY_MAP, extract_areas_from_quotations, normalize_areas


def run_prediction_fallback(points, quotations, pi_info, horizon_days):
    n = len(points)
    quality_factor = QUALITY_MAP.get(points[-1].get("data_quality", "medium"), 0.8) if n >= 1 else 0.8

    if n == 0:
        areas = extract_areas_from_quotations(quotations)
        if not areas:
            default_areas = normalize_areas(pi_info.get("research_areas", "[]"))
            areas = default_areas if default_areas else ["通用科研"]
        predicted = [{"area": a, "probability": round(1.0 / len(areas), 2), "trend": "stable"} for a in areas]
        return {
            "predicted_areas": predicted,
            "confidence": 0.1,
            "rationale": "无轨迹数据，基于PI资料和询价历史推测",
            "area_transition": {"from_areas": [], "to_areas": areas[:2], "transition_path": []},
        }

    if n < 2:
        areas = extract_areas_from_quotations(quotations)
        if not areas:
            last_active = normalize_areas(points[-1].get("active_areas", "[]"))
            areas = last_active if last_active else ["通用科研"]
        predicted = [{"area": a, "probability": round(1.0 / len(areas), 2), "trend": "stable"} for a in areas]
        return {
            "predicted_areas": predicted,
            "confidence": round(min(n / 12, 0.9) * quality_factor * 0.5, 2),
            "rationale": f"轨迹点不足2个，基于{len(points)}个点及询价记录推测",
            "area_transition": {
                "from_areas": [points[-1].get("dominant_area", "")] if points[-1].get("dominant_area") else [],
                "to_areas": areas[:2],
                "transition_path": [],
            },
        }

    area_counter = Counter()
    total_weight = 0.0
    for i, pt in enumerate(points):
        recency = (i + 1) / n
        weights = normalize_areas(pt.get("area_weights", "{}"))
        if isinstance(weights, dict) and weights:
            for area, w in weights.items():
                weighted = w * recency
                area_counter[area] += weighted
                total_weight += weighted
        else:
            for area in normalize_areas(pt.get("active_areas", "[]")):
                area_counter[area] += recency
                total_weight += recency

    last_dominant = points[-1].get("dominant_area", "")
    dominant_areas = [p.get("dominant_area", "") for p in points if p.get("dominant_area")]
    from_areas = list(dict.fromkeys(dominant_areas[:-1])) if len(dominant_areas) > 1 else []
    to_areas = [dominant_areas[-1]] if dominant_areas else []
    transition_path = dominant_areas.copy()

    for qa in extract_areas_from_quotations(quotations):
        area_counter[qa] += 0.1 * quality_factor
        total_weight += 0.1 * quality_factor

    if total_weight > 0 and area_counter:
        predicted = []
        for area, weight in area_counter.most_common(5):
            prob = round(weight / total_weight, 2)
            trend = "up"
            if last_dominant and area == last_dominant:
                trend = "stable"
            if area in from_areas and area not in to_areas:
                trend = "down"
            predicted.append({"area": area, "probability": prob, "trend": trend})
        predicted.sort(key=lambda x: x["probability"], reverse=True)
    else:
        predicted = []

    confidence = round(min(n / 12, 0.9) * quality_factor, 2)
    if predicted:
        to_areas = [p["area"] for p in predicted[:2]]
    rationale_parts = [f"基于{len(points)}个轨迹点"]
    if transition_path:
        rationale_parts.append(f"领域迁移路径: {'→'.join(transition_path)}")
    rationale_parts.append("短期预测" if horizon_days <= 90 else "中长期预测")
    return {
        "predicted_areas": predicted,
        "confidence": confidence,
        "rationale": "；".join(rationale_parts),
        "area_transition": {"from_areas": from_areas, "to_areas": to_areas, "transition_path": transition_path},
    }
