import json
from collections import Counter
from datetime import datetime, timedelta

from cloud.app.research_database import get_research_db

QUALITY_MAP = {"high": 1.0, "medium": 0.8, "low": 0.5}


def normalize_areas(obj):
    if isinstance(obj, str):
        try:
            return json.loads(obj)
        except (json.JSONDecodeError, TypeError):
            return []
    if isinstance(obj, (list, dict)):
        return obj
    return []


def extract_time_series(pi_id: int, months: int = 12) -> dict:
    db = get_research_db()
    try:
        since = (datetime.now() - timedelta(days=30 * months)).strftime("%Y-%m-%d")
        traj_rows = db.execute(
            "SELECT * FROM pi_trajectories WHERE pi_id = ? AND observation_date >= ? ORDER BY observation_date ASC",
            (pi_id, since),
        ).fetchall()
        points = [dict(r) for r in traj_rows]

        pi_row = db.execute("SELECT * FROM research_pi_profiles WHERE pi_id = ?", (pi_id,)).fetchone()
        pi_info = dict(pi_row) if pi_row else {}

        quotation_rows = db.execute(
            "SELECT * FROM research_quotations WHERE customer_name LIKE ? AND created_at >= ? ORDER BY created_at ASC",
            (f"%{pi_info.get('name', '')}%", since),
        ).fetchall()
        quotations = [dict(r) for r in quotation_rows]
    finally:
        db.close()

    time_points = []
    for pt in points:
        time_points.append(
            {
                "date": pt["observation_date"],
                "dominant_area": pt.get("dominant_area", ""),
                "active_areas": normalize_areas(pt.get("active_areas", "[]")),
                "area_weights": normalize_areas(pt.get("area_weights", "{}")),
                "source": pt.get("source", "manual"),
                "data_quality": pt.get("data_quality", "medium"),
            }
        )

    area_weights_series = {}
    for tp in time_points:
        weights = tp["area_weights"]
        if isinstance(weights, dict):
            for area, weight in weights.items():
                if area not in area_weights_series:
                    area_weights_series[area] = []
                area_weights_series[area].append({"date": tp["date"], "weight": weight})

    dominant_transitions = []
    prev_dominant = None
    prev_date = None
    for tp in time_points:
        curr = tp["dominant_area"]
        if curr and curr != prev_dominant:
            if prev_dominant:
                interval_days = 0
                if prev_date:
                    d1 = datetime.strptime(prev_date, "%Y-%m-%d")
                    d2 = datetime.strptime(tp["date"], "%Y-%m-%d")
                    interval_days = (d2 - d1).days
                dominant_transitions.append(
                    {
                        "from_area": prev_dominant,
                        "to_area": curr,
                        "transition_date": tp["date"],
                        "interval_days": interval_days,
                    }
                )
            prev_dominant = curr
            prev_date = tp["date"]

    event_timeline = []
    for q in quotations:
        event_timeline.append(
            {
                "date": q.get("created_at", ""),
                "type": "quotation",
                "title": q.get("title", ""),
                "amount": q.get("total_amount", 0),
                "status": q.get("status", ""),
            }
        )

    n = len(time_points)
    tc = len(dominant_transitions)
    avg_interval_days = 0
    if tc > 0:
        avg_interval_days = round(sum(t["interval_days"] for t in dominant_transitions) / tc)
    latest_stability_measure = 1.0
    if n >= 2 and tc > 0:
        latest_stability_measure = round(1.0 - min(tc / max(n, 1), 1.0), 2)

    return {
        "time_points": time_points,
        "area_weights_series": area_weights_series,
        "dominant_transitions": dominant_transitions,
        "event_timeline": event_timeline,
        "stat_features": {
            "observation_count": n,
            "transition_count": tc,
            "avg_interval_days": avg_interval_days,
            "latest_stability_measure": latest_stability_measure,
        },
    }


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


def extract_areas_from_quotations(quotations):
    areas = set()
    for q in quotations:
        items = normalize_areas(q.get("items_json", "[]"))
        for item in items:
            if isinstance(item, dict):
                cat = item.get("category", "")
                name = item.get("product_name", "") or item.get("name", "")
                if cat:
                    areas.add(cat)
                elif name:
                    areas.add(name)
        title = q.get("title", "")
        if title:
            for kw in ["试剂盒", "抗体", "测序", "PCR", "细胞", "基因", "蛋白"]:
                if kw in title:
                    areas.add(kw)
    return list(areas)


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
