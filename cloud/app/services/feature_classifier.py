"""特征分类模块，提供因果归因与分类分析。"""

from .feature_extractor import QUALITY_MAP


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
