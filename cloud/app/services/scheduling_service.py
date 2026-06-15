from datetime import datetime, timedelta
from typing import Any

from shared.base_service import BaseService


class SchedulingService(BaseService):
    """路线调度优化服务，负责医药代表的拜访路线规划与优化。"""

    def optimize_route(self, rep_id: int, date_range: str) -> list[dict[str, Any]]:
        hcps = self._get_hcp_list(rep_id)
        if not hcps:
            return []

        weights = [hcp.get("weight", 5) for hcp in hcps]
        distances = [hcp.get("distance", 1) for hcp in hcps]
        frequencies = [hcp.get("frequency", 1) for hcp in hcps]
        urgencies = [hcp.get("urgency", 1) for hcp in hcps]

        w_min, w_max = min(weights), max(weights)
        d_min, d_max = min(distances), max(distances)
        f_min, f_max = min(frequencies), max(frequencies)
        u_min, u_max = min(urgencies), max(urgencies)

        def _normalize(val, vmin, vmax):
            if vmax == vmin:
                return 0.5
            return (val - vmin) / (vmax - vmin)

        scored = []
        for hcp in hcps:
            w_norm = _normalize(hcp.get("weight", 5), w_min, w_max)
            d_norm = 1.0 - _normalize(hcp.get("distance", 1), d_min, d_max)
            f_norm = 1.0 - _normalize(hcp.get("frequency", 1), f_min, f_max)
            u_norm = _normalize(hcp.get("urgency", 1), u_min, u_max)

            score = w_norm * 0.4 + d_norm * 0.3 + f_norm * 0.2 + u_norm * 0.1

            reason_parts = []
            if hcp.get("weight", 5) >= 8:
                reason_parts.append("高优先级HCP权重高")
            if hcp.get("distance", 999) < 10:
                reason_parts.append("距离近可优先拜访")
            if hcp.get("frequency", 1) < 2:
                reason_parts.append("拜访频率偏低需加强")
            if hcp.get("urgency", 1) >= 8:
                reason_parts.append("有紧急跟进事项")

            scored.append(
                {
                    "hcp_id": hcp["id"],
                    "hcp_name": hcp["name"],
                    "visit_time": (datetime.now() + timedelta(hours=len(scored) * 2)).strftime("%Y-%m-%d %H:%M"),
                    "priority_score": round(score, 2),
                    "reason": "；".join(reason_parts) if reason_parts else "常规拜访",
                }
            )

        scored.sort(key=lambda x: x["priority_score"], reverse=True)
        return scored

    def _get_hcp_list(self, rep_id: int) -> list[dict[str, Any]]:
        return [
            {"id": 1, "name": "张建国", "weight": 9, "distance": 3.5, "frequency": 2, "urgency": 8},
            {"id": 2, "name": "李明辉", "weight": 7, "distance": 8.2, "frequency": 1, "urgency": 6},
            {"id": 3, "name": "王芳", "weight": 8, "distance": 1.2, "frequency": 3, "urgency": 5},
            {"id": 4, "name": "陈志远", "weight": 6, "distance": 15.0, "frequency": 1, "urgency": 9},
            {"id": 5, "name": "刘美琴", "weight": 5, "distance": 6.0, "frequency": 4, "urgency": 3},
        ]

    def get_plan(self, rep_id: int) -> list[dict[str, Any]]:
        return self.optimize_route(rep_id, "today")
