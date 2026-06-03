import json
from collections import Counter
from datetime import datetime, timedelta

from fastapi import HTTPException
from starlette import status

from cloud.app.research_database import get_research_db

QUALITY_MAP = {"high": 1.0, "medium": 0.8, "low": 0.5}


class ResearchTrajectoryService:
    """ResearchTrajectory 服务类。"""

    def _init_db_table(self):
        db = get_research_db()
        try:
            db.execute(
                "CREATE TABLE IF NOT EXISTS pi_trajectories ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, pi_id INTEGER NOT NULL, "
                "observation_date TEXT NOT NULL, active_areas TEXT DEFAULT '[]', "
                "area_weights TEXT DEFAULT '{}', dominant_area TEXT DEFAULT '', "
                "source TEXT DEFAULT 'manual', data_quality TEXT DEFAULT 'medium', "
                "created_at TEXT DEFAULT CURRENT_TIMESTAMP, "
                "FOREIGN KEY (pi_id) REFERENCES research_pi_profiles(pi_id))"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS pi_predictions ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, pi_id INTEGER NOT NULL, "
                "prediction_date TEXT NOT NULL, horizon_days INTEGER DEFAULT 90, "
                "predicted_areas TEXT DEFAULT '[]', confidence REAL DEFAULT 0.0, "
                "rationale TEXT DEFAULT '', area_transition TEXT DEFAULT '{}', "
                "created_at TEXT DEFAULT CURRENT_TIMESTAMP, "
                "FOREIGN KEY (pi_id) REFERENCES research_pi_profiles(pi_id))"
            )
            db.commit()
        finally:
            db.close()

    def _normalize_areas(self, obj):
        if isinstance(obj, str):
            try:
                return json.loads(obj)
            except (json.JSONDecodeError, TypeError):
                return []
        if isinstance(obj, (list, dict)):
            return obj
        return []

    def get_trajectory(self, pi_id: int) -> dict:
        """get_trajectory 操作。

        Args:
            pi_id: 描述

        Returns:
            描述
        """
        db = get_research_db()
        try:
            pi_row = db.execute("SELECT * FROM research_pi_profiles WHERE pi_id = ?", (pi_id,)).fetchone()
            if not pi_row:
                raise HTTPException(status.HTTP_404_NOT_FOUND, detail="PI not found")
            pi_info = dict(pi_row)
            traj_rows = db.execute("SELECT * FROM pi_trajectories WHERE pi_id = ? ORDER BY observation_date ASC", (pi_id,)).fetchall()
            pred_rows = db.execute("SELECT * FROM pi_predictions WHERE pi_id = ? ORDER BY created_at DESC LIMIT 2", (pi_id,)).fetchall()
            quotation_rows = db.execute(
                "SELECT * FROM research_quotations WHERE customer_name LIKE ? ORDER BY created_at DESC",
                (f"%{pi_info['name']}%",),
            ).fetchall()
            return {
                "pi_info": pi_info,
                "trajectory_points": [dict(r) for r in traj_rows],
                "recent_predictions": [dict(r) for r in pred_rows],
                "quotation_trend": [dict(r) for r in quotation_rows],
            }
        finally:
            db.close()

    def predict_trajectory(self, pi_id: int, horizon_days: int = 90) -> dict:
        """predict_trajectory 操作。

        Args:
            pi_id: 描述
            horizon_days: 描述

        Returns:
            描述
        """
        self._init_db_table()
        db = get_research_db()
        try:
            pi_row = db.execute("SELECT * FROM research_pi_profiles WHERE pi_id = ?", (pi_id,)).fetchone()
            if not pi_row:
                raise HTTPException(status.HTTP_404_NOT_FOUND, detail="PI not found")
            pi_info = dict(pi_row)
            twelve_months_ago = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            traj_rows = db.execute(
                "SELECT * FROM pi_trajectories WHERE pi_id = ? AND observation_date >= ? ORDER BY observation_date ASC",
                (pi_id, twelve_months_ago),
            ).fetchall()
            quotation_rows = db.execute(
                "SELECT * FROM research_quotations WHERE customer_name LIKE ? AND created_at >= ? ORDER BY created_at ASC",
                (f"%{pi_info['name']}%", twelve_months_ago),
            ).fetchall()
            points = [dict(r) for r in traj_rows]
            quotations = [dict(r) for r in quotation_rows]
            result = self._run_prediction(points, quotations, pi_info, horizon_days)
            now_str = datetime.now().strftime("%Y-%m-%d")
            db.execute(
                "INSERT INTO pi_predictions (pi_id, prediction_date, horizon_days, "
                "predicted_areas, confidence, rationale, area_transition) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    pi_id,
                    now_str,
                    horizon_days,
                    json.dumps(result["predicted_areas"], ensure_ascii=False),
                    result["confidence"],
                    result["rationale"],
                    json.dumps(result["area_transition"], ensure_ascii=False),
                ),
            )
            db.commit()
            return result
        finally:
            db.close()

    def _run_prediction(self, points, quotations, pi_info, horizon_days):
        n = len(points)
        quality_factor = QUALITY_MAP.get(points[-1].get("data_quality", "medium"), 0.8) if n >= 1 else 0.8

        if n == 0:
            areas = self._extract_areas_from_quotations(quotations)
            if not areas:
                default_areas = self._normalize_areas(pi_info.get("research_areas", "[]"))
                areas = default_areas if default_areas else ["通用科研"]
            predicted = [{"area": a, "probability": round(1.0 / len(areas), 2), "trend": "stable"} for a in areas]
            return {
                "predicted_areas": predicted,
                "confidence": 0.1,
                "rationale": "无轨迹数据，基于PI资料和询价历史推测",
                "area_transition": {"from_areas": [], "to_areas": areas[:2], "transition_path": []},
            }

        if n < 2:
            areas = self._extract_areas_from_quotations(quotations)
            if not areas:
                last_active = self._normalize_areas(points[-1].get("active_areas", "[]"))
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
            weights = self._normalize_areas(pt.get("area_weights", "{}"))
            if isinstance(weights, dict) and weights:
                for area, w in weights.items():
                    weighted = w * recency
                    area_counter[area] += weighted
                    total_weight += weighted
            else:
                for area in self._normalize_areas(pt.get("active_areas", "[]")):
                    area_counter[area] += recency
                    total_weight += recency

        last_dominant = points[-1].get("dominant_area", "")
        dominant_areas = [p.get("dominant_area", "") for p in points if p.get("dominant_area")]
        from_areas = list(dict.fromkeys(dominant_areas[:-1])) if len(dominant_areas) > 1 else []
        to_areas = [dominant_areas[-1]] if dominant_areas else []
        transition_path = dominant_areas.copy()

        for qa in self._extract_areas_from_quotations(quotations):
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

    def _extract_areas_from_quotations(self, quotations):
        areas = set()
        for q in quotations:
            items = self._normalize_areas(q.get("items_json", "[]"))
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

    def get_trends(self, days: int = 90) -> dict:
        """get_trends 操作。

        Args:
            days: 描述

        Returns:
            描述
        """
        db = get_research_db()
        try:
            since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            traj_rows = db.execute("SELECT dominant_area, active_areas FROM pi_trajectories WHERE observation_date >= ?", (since,)).fetchall()
            pred_rows = db.execute("SELECT predicted_areas FROM pi_predictions WHERE prediction_date >= ?", (since,)).fetchall()
            dominant_counter = Counter()
            active_counter = Counter()
            for row in traj_rows:
                if row["dominant_area"]:
                    dominant_counter[row["dominant_area"]] += 1
                for a in self._normalize_areas(row["active_areas"]):
                    if isinstance(a, str):
                        active_counter[a] += 1
            pred_area_counter = Counter()
            for row in pred_rows:
                for p in self._normalize_areas(row["predicted_areas"]):
                    if isinstance(p, dict):
                        area = p.get("area", "")
                        if area:
                            pred_area_counter[area] += 1
                    elif isinstance(p, str):
                        pred_area_counter[p] += 1
            all_areas = dominant_counter + active_counter + pred_area_counter
            total = sum(all_areas.values()) or 1
            sorted_areas = all_areas.most_common()
            hot = [{"area": a, "count": c, "ratio": round(c / total, 2)} for a, c in sorted_areas[:5]]
            emerging = []
            declining = []
            for a, c in sorted_areas:
                ratio = c / total
                in_traj = a in dominant_counter
                in_pred = a in pred_area_counter
                if in_pred and not in_traj:
                    emerging.append({"area": a, "count": c, "ratio": round(ratio, 2)})
                if in_traj and not in_pred:
                    declining.append({"area": a, "count": c, "ratio": round(ratio, 2)})
            return {"hot_areas": hot[:5], "emerging_areas": emerging[:5], "declining_areas": declining[:5]}
        finally:
            db.close()
