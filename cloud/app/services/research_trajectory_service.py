"""科研轨迹服务，负责 PI 研究轨迹记录、领域转移预测与趋势分析。"""

import json
from collections import Counter
from datetime import datetime, timedelta

from fastapi import HTTPException
from starlette import status

from cloud.app.research_database import get_research_db
from cloud.app.services.feature_analyzer import causal_attribution, run_prediction_fallback
from cloud.app.services.feature_extractor import extract_time_series, normalize_areas


class ResearchTrajectoryService:
    """科研轨迹服务，提供 PI 轨迹记录、领域转移预测与评分、趋势分析。"""

    def _init_db_table(self):
        """初始化 pi_trajectories 和 pi_predictions 数据库表（如不存在则创建）。"""
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

    def get_trajectory(self, pi_id: int) -> dict:
        """Retrieve the full research trajectory for a PI, including observations, predictions, and quotations.

        Args:
            pi_id: The PI's ID.

        Returns:
            A dict with pi_info, trajectory_points, recent_predictions, and quotation_trend.

        Raises:
            HTTPException: 404 if the PI is not found.
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
        """Predict a PI's future research trajectory using AI analysis of time-series features.

        Extracts features from trajectory points and quotations over the past year,
        calls an LLM for prediction, and stores the result in pi_predictions.

        Args:
            pi_id: The PI's ID.
            horizon_days: Number of days to forecast (default 90).

        Returns:
            A dict containing predicted_areas, confidence, rationale, and area_transition.

        Raises:
            HTTPException: 404 if the PI is not found.
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

            features = extract_time_series(pi_id)
            ai_result = self._ai_predict_transition(pi_info, features, horizon_days)

            if ai_result:
                result = ai_result
                result["area_transition"] = {
                    "from_areas": [t["from_area"] for t in features["dominant_transitions"][-2:]] if features["dominant_transitions"] else [],
                    "to_areas": [p["area"] for p in ai_result["predicted_areas"][:2]],
                    "transition_path": ai_result.get("transition_path", []),
                }
                result["confidence"] = round(result["confidence"] * features["stat_features"]["latest_stability_measure"], 2)
                causal_attribution(result, features)
            else:
                result = run_prediction_fallback(points, quotations, pi_info, horizon_days)

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
                    json.dumps(result.get("area_transition", {}), ensure_ascii=False),
                ),
            )
            db.commit()
            return result
        finally:
            db.close()

    def _ai_predict_transition(self, pi_info: dict, features: dict, horizon_days: int) -> dict | None:
        """调用 LLM 对 PI 进行领域转移预测。

        Args:
            pi_info: PI 信息字典。
            features: 时间序列特征。
            horizon_days: 预测天数。

        Returns:
            预测结果字典，若 LLM 未返回有效预测则返回 None。
        """
        from cloud.app.services.research_trajectory_ai import build_prediction_prompt, call_llm_for_prediction

        prompt = build_prediction_prompt(pi_info, features, horizon_days)
        result = call_llm_for_prediction(prompt)
        if not result.get("predicted_areas"):
            return None
        return result

    def get_pi_trajectory_score(self, pi_id: int, area: str | None = None) -> dict:
        """Compute a trajectory score for a PI, optionally scoped to a specific research area.

        Uses the latest prediction, data quality weighting, and trend bonuses to produce
        a 0-100 score with a human-readable recommendation.

        Args:
            pi_id: The PI's ID.
            area: Optional specific research area to score. If None, scores all areas.

        Returns:
            A dict with pi_id, area, trajectory_score, data_quality, recommendation, and source_prediction_id.
        """
        QUALITY_MAP = {"high": 1.0, "medium": 0.8, "low": 0.5}
        db = get_research_db()
        try:
            pred_row = db.execute(
                "SELECT * FROM pi_predictions WHERE pi_id = ? ORDER BY created_at DESC LIMIT 1",
                (pi_id,),
            ).fetchone()
            if not pred_row:
                return {
                    "pi_id": pi_id,
                    "area": area or "all",
                    "trajectory_score": 0,
                    "data_quality": "low",
                    "recommendation": "尚无预测数据，请先执行预测",
                    "source_prediction_id": None,
                }
            pred = dict(pred_row)
            predicted_areas = normalize_areas(pred.get("predicted_areas", "[]"))
            quality = pred.get("data_quality", "medium") if "data_quality" in pred else "medium"
            quality_factor = QUALITY_MAP.get(quality, 0.8)

            if area:
                target = [p for p in predicted_areas if isinstance(p, dict) and p.get("area") == area]
            else:
                target = [p for p in predicted_areas if isinstance(p, dict)]

            if not target:
                return {
                    "pi_id": pi_id,
                    "area": area or "all",
                    "trajectory_score": 0,
                    "data_quality": quality,
                    "recommendation": "指定领域无预测数据",
                    "source_prediction_id": pred["id"],
                }

            max_prob = max(p.get("probability", 0) for p in target)
            best = max(target, key=lambda x: x.get("probability", 0))
            trend = best.get("trend", "stable")
            trend_bonus = 10 if trend == "up" else -10 if trend == "down" else 0
            trajectory_score = min(100, round(max_prob * 100 * quality_factor + trend_bonus))

            if trajectory_score >= 70:
                recommendation = "高潜力领域，建议重点跟进"
            elif trajectory_score >= 40:
                recommendation = "中等潜力，建议保持关注"
            else:
                recommendation = "低活跃度，建议观察"

            return {
                "pi_id": pi_id,
                "area": area or "all",
                "trajectory_score": trajectory_score,
                "data_quality": quality,
                "recommendation": recommendation,
                "source_prediction_id": pred["id"],
            }
        finally:
            db.close()

    def get_trends(self, days: int = 90) -> dict:
        """Retrieve research area trends including hot, emerging, and declining areas.

        Analyzes dominant areas from trajectories and predicted areas from predictions
        over the specified number of days.

        Args:
            days: Lookback window in days (default 90).

        Returns:
            A dict with hot_areas, emerging_areas, and declining_areas lists.
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
                for a in normalize_areas(row["active_areas"]):
                    if isinstance(a, str):
                        active_counter[a] += 1
            pred_area_counter = Counter()
            for row in pred_rows:
                for p in normalize_areas(row["predicted_areas"]):
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
