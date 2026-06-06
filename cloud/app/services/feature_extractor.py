"""特征提取模块，从研究数据库中抽取时间序列特征数据。"""

import json
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
