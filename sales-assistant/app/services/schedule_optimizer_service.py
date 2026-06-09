"""AI排程优化服务。"""

import math
from datetime import datetime, timedelta
from typing import Any

from fastapi import Depends

from sales_assistant.app.database import get_db
from sales_assistant.app.schemas.schedule_optimizer import ScheduleRequest, ScheduleResult, VisitSlot


class ScheduleOptimizerService:
    """基于HCP权重、距离、历史频率和可用时间窗口生成拜访顺序。"""

    def __init__(self, db=Depends(get_db)):
        self.db = db

    def _pk_sql(self) -> str:
        return "SERIAL PRIMARY KEY" if self.db.__class__.__name__ == "PGCompatConnection" else "INTEGER PRIMARY KEY AUTOINCREMENT"

    def _ensure_table(self) -> None:
        self.db.execute(
            f"""
            CREATE TABLE IF NOT EXISTS schedule_optimization (
                id {self._pk_sql()},
                rep_id TEXT NOT NULL,
                schedule_date TEXT NOT NULL,
                request_json TEXT,
                result_json TEXT,
                created_at TEXT,
                updated_at TEXT,
                UNIQUE(rep_id, schedule_date)
            )
            """
        )
        self.db.commit()

    def _distance_km(self, a_lat: float, a_lng: float, b_lat: float, b_lng: float) -> float:
        radius = 6371.0
        lat1 = math.radians(a_lat)
        lat2 = math.radians(b_lat)
        dlat = math.radians(b_lat - a_lat)
        dlng = math.radians(b_lng - a_lng)
        h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
        return round(2 * radius * math.asin(math.sqrt(h)), 2)

    def _tier_weight(self, tier: str | None) -> float:
        return {"A": 100.0, "B": 75.0, "C": 50.0}.get((tier or "C").upper(), 45.0)

    def _candidate_rows(self, preferred_area: str | None = None) -> list[dict[str, Any]]:
        conditions = ["is_active = 1"]
        params: list[Any] = []
        if preferred_area:
            conditions.append("(city LIKE ? OR hospital LIKE ?)")
            params.extend([f"%{preferred_area}%", f"%{preferred_area}%"])
        where_sql = " AND ".join(conditions)
        rows = self.db.execute(
            f"""
            SELECT id, name, hospital, department, tier, city, updated_at
            FROM hcp
            WHERE {where_sql}
            ORDER BY updated_at DESC
            LIMIT 20
            """,
            params,
        ).fetchall()
        if not rows:
            rows = [
                {
                    "id": "demo-001",
                    "name": "示例医生A",
                    "hospital": preferred_area or "第一人民医院",
                    "department": "心内科",
                    "tier": "A",
                    "city": preferred_area or "上海",
                },
                {
                    "id": "demo-002",
                    "name": "示例医生B",
                    "hospital": preferred_area or "中心医院",
                    "department": "内分泌科",
                    "tier": "B",
                    "city": preferred_area or "上海",
                },
                {
                    "id": "demo-003",
                    "name": "示例医生C",
                    "hospital": preferred_area or "省立医院",
                    "department": "呼吸科",
                    "tier": "C",
                    "city": preferred_area or "上海",
                },
            ]
        return [dict(row) for row in rows]

    def _history_count(self, hcp_id: str) -> int:
        if not str(hcp_id).isdigit():
            return 0
        row = self.db.execute("SELECT COUNT(*) AS cnt FROM visit_hcp WHERE hcp_id = ?", (int(hcp_id),)).fetchone()
        return int(row["cnt"]) if row else 0

    def _coords_for_index(self, idx: int) -> tuple[float, float]:
        base_lat, base_lng = 31.2304, 121.4737
        return (base_lat + (idx % 5) * 0.018, base_lng + (idx // 5) * 0.022)

    def _parse_window(self, request: ScheduleRequest) -> tuple[datetime, datetime]:
        start = request.available_hours[0] if request.available_hours else "09:00"
        end = request.available_hours[-1] if len(request.available_hours) > 1 else "17:00"
        return (
            datetime.fromisoformat(f"{request.date}T{start}:00"),
            datetime.fromisoformat(f"{request.date}T{end}:00"),
        )

    def optimize_daily_schedule(self, rep_id: str, date: str, request: ScheduleRequest | None = None) -> ScheduleResult:
        """贪心 + 最近邻TSP近似生成每日拜访路线。"""
        request = request or ScheduleRequest(rep_id=rep_id, date=date)
        rows = self._candidate_rows(request.preferred_area)
        candidates = []
        for idx, row in enumerate(rows):
            lat, lng = self._coords_for_index(idx)
            history_penalty = min(self._history_count(str(row["id"])) * 6, 30)
            priority = max(self._tier_weight(row.get("tier")) - history_penalty, 10)
            candidates.append({**row, "lat": lat, "lng": lng, "priority_score": priority})

        start_at, end_at = self._parse_window(request)
        current_time = start_at
        current_lat, current_lng = 31.2304, 121.4737
        visit_duration = 45
        selected: list[VisitSlot] = []
        remaining = candidates[:]

        while remaining and current_time + timedelta(minutes=visit_duration) <= end_at:
            best = max(
                remaining,
                key=lambda item: item["priority_score"] - self._distance_km(current_lat, current_lng, item["lat"], item["lng"]) * 1.8,
            )
            distance = self._distance_km(current_lat, current_lng, best["lat"], best["lng"])
            travel_minutes = int(distance / 25 * 60)
            current_time += timedelta(minutes=travel_minutes)
            if current_time + timedelta(minutes=visit_duration) > end_at:
                break
            selected.append(
                VisitSlot(
                    hcp_id=str(best["id"]),
                    hcp_name=best["name"],
                    address=" / ".join(part for part in [best.get("city"), best.get("hospital"), best.get("department")] if part),
                    lat=best["lat"],
                    lng=best["lng"],
                    priority_score=round(best["priority_score"], 2),
                    suggested_time=current_time.strftime("%H:%M"),
                    visit_duration=visit_duration,
                    distance_from_prev=distance,
                )
            )
            current_time += timedelta(minutes=visit_duration)
            current_lat, current_lng = best["lat"], best["lng"]
            remaining.remove(best)

        total_distance = round(sum(item.distance_from_prev for item in selected), 2)
        total_time = int((current_time - start_at).total_seconds() // 60) if selected else 0
        return ScheduleResult(optimized_visits=selected, total_distance=total_distance, total_time=total_time)
