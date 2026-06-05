from collections import Counter

from .feature_extractor import QUALITY_MAP, extract_areas_from_quotations, normalize_areas


def causal_attribution(prediction_result: dict, time_series_features: dict) -> dict:
    features = time_series_features
    stat = features["stat_features"]
    points = features["time_points"]
    transitions = features["dominant_transitions"]
    weights_series = features["area_weights_series"]
    events = features["event_timeline"]

    drivers = []
    blocking_factors = []

    for area, series in weights_series.items():
        vals = [w["weight"] for w in series]
        if len(vals) >= 3 and vals[-1] > vals[0] * 1.5:
            drivers.append(
                {
                    "factor": f"领域「{area}」权重持续上升",
                    "source": "area_weights_series",
                    "impact": "high",
                    "evidence": f"过去{len(vals)}个轨迹点从{round(vals[0], 2)}升至{round(vals[-1], 2)}",
                }
            )

    recent_events = [e for e in events if e["status"] != "draft"]
    area_event_count = {}
    for e in recent_events:
        for kw in weights_series:
            if kw in e.get("title", ""):
                area_event_count[kw] = area_event_count.get(kw, 0) + 1
    for area, count in area_event_count.items():
        if count >= 3:
            drivers.append(
                {
                    "factor": f"报价频次增加（{area}）",
                    "source": "event_timeline",
                    "impact": "medium",
                    "evidence": f"近期相关报价从0增至{count}次",
                }
            )

    if len(transitions) >= 2:
        last_t = transitions[-1]
        drivers.append(
            {
                "factor": "临近领域转移",
                "source": "dominant_transitions",
                "impact": "medium",
                "evidence": f"上次转移距今{last_t['interval_days']}天",
            }
        )

    if points:
        last_point = points[-1]
        last_dominant = last_point["dominant_area"]
        if last_dominant:
            dwell_months = 0
            for i in range(len(points) - 1, -1, -1):
                if points[i]["dominant_area"] == last_dominant:
                    dwell_months += 1
                else:
                    break
            if dwell_months >= 6:
                blocking_factors.append(
                    {
                        "factor": "PI驻留时间过长",
                        "source": "dominant_transitions",
                        "impact": "low",
                        "evidence": f"当前领域已驻留{dwell_months}个轨迹点",
                    }
                )

        if len(weights_series) > 0:
            volatile_areas = []
            for area, series in weights_series.items():
                vals = [w["weight"] for w in series]
                if len(vals) >= 3:
                    mean_v = sum(vals) / len(vals)
                    variance = sum((v - mean_v) ** 2 for v in vals) / len(vals)
                    if mean_v > 0 and (variance**0.5) / mean_v > 0.8:
                        volatile_areas.append(area)
            if volatile_areas:
                blocking_factors.append(
                    {
                        "factor": f"领域权重波动大: {', '.join(volatile_areas[:2])}",
                        "source": "area_weights_series",
                        "impact": "medium",
                        "evidence": f"{len(volatile_areas)}个领域CV>0.8",
                    }
                )

    if stat["observation_count"] < 3:
        blocking_factors.append(
            {
                "factor": "数据稀疏",
                "source": "area_weights_series",
                "impact": "high",
                "evidence": f"仅{stat['observation_count']}个轨迹点",
            }
        )

    count_factor = min(stat["observation_count"] / 12, 1.0)
    quality_values = [QUALITY_MAP.get(p.get("data_quality", "medium"), 0.8) for p in points]
    avg_quality = sum(quality_values) / len(quality_values) if quality_values else 0.8
    clarity = 1.0
    if stat["transition_count"] > 0:
        clarity = min(stat["transition_count"] / max(stat["observation_count"], 1) * 2, 1.0)
    overall_causal_confidence = round(avg_quality * count_factor * clarity, 2)

    prediction_result["causal_attribution"] = {
        "drivers": drivers,
        "blocking_factors": blocking_factors,
        "overall_causal_confidence": overall_causal_confidence,
    }
    return prediction_result


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
