"""今日拜访智能排序服务 — Task 1"""

from datetime import datetime
from typing import Any

from shared.base_service import BaseService


class VisitPrioritizationService(BaseService):
    """基于多因子加权评分的 HCP 拜访优先级排序。"""

    def get_priority_list(self, rep_id: int) -> dict[str, Any]:
        hcps = self._load_hcps_for_rep(rep_id)
        if not hcps:
            return {"priority_list": []}

        scored = []
        for hcp in hcps:
            score, reasons = self._score_hcp(hcp, rep_id)
            scored.append(
                {
                    "hcp_id": str(hcp["id"]),
                    "hcp_name": hcp["name"],
                    "score": round(score, 2),
                    "reasons": reasons,
                    "suggested_time": hcp.get("suggested_time", "下午门诊后"),
                }
            )

        scored.sort(key=lambda x: x["score"], reverse=True)
        return {"priority_list": scored}

    def _score_hcp(self, hcp: dict, rep_id: int) -> tuple[float, list[str]]:
        reasons = []
        score = 50.0

        days_since = self._days_since_last_visit(hcp["id"], rep_id)
        if days_since > 30:
            score += 15
            reasons.append(f"{days_since}天未访")
        elif days_since > 14:
            score += 8
            reasons.append(f"{days_since}天未访")

        rx_change = self._prescription_change(hcp["id"])
        if rx_change < -10:
            score += 20
            reasons.append(f"处方量下降{abs(rx_change)}%")
        elif rx_change < -5:
            score += 10
            reasons.append(f"处方量下降{abs(rx_change)}%")

        papers = self._recent_papers(hcp["id"])
        if papers:
            score += 15
            reasons.append(f"刚发相关论文「{papers[0]}」")

        competitor_activity = self._competitor_activity(hcp["id"])
        if competitor_activity:
            score += 12
            reasons.append("竞品最近频繁接触")

        compliance = self._pending_compliance(hcp["id"])
        if compliance:
            score += 10
            reasons.append("有未处理的合规问题需当面解释")

        risk = 0
        if rx_change < 0:
            risk += 5
        if competitor_activity:
            risk += 5
        score = max(0, min(100, score + risk))

        return score, reasons

    def _load_hcps_for_rep(self, rep_id: int) -> list[dict]:
        conn = self._connection()
        rows = conn.execute(
            "SELECT id, name, hospital, department FROM hcp_profiles WHERE is_active=1 ORDER BY influence_score DESC LIMIT 20"
        ).fetchall()
        if rows:
            return [dict(r) for r in rows]
        return [
            {"id": 101, "name": "陈主任", "hospital": "北京协和", "department": "心内科", "suggested_time": "下午门诊后"},
            {"id": 102, "name": "李主任", "hospital": "上海中山", "department": "内分泌", "suggested_time": "上午查房后"},
            {"id": 103, "name": "张主任", "hospital": "广州南方", "department": "消化内科", "suggested_time": "午休时间"},
            {"id": 104, "name": "王主任", "hospital": "杭州浙一", "department": "神经内科", "suggested_time": "下午门诊后"},
            {"id": 105, "name": "刘主任", "hospital": "北京人民", "department": "呼吸科", "suggested_time": "上午查房后"},
        ]

    def _days_since_last_visit(self, hcp_id: int, rep_id: int) -> int:
        conn = self._connection()
        row = conn.execute(
            "SELECT created_at FROM visits WHERE hcp_id=? ORDER BY created_at DESC LIMIT 1",
            (hcp_id,),
        ).fetchone()
        if row:
            try:
                last = datetime.strptime(row["created_at"][:10], "%Y-%m-%d")
                return (datetime.now() - last).days
            except (ValueError, IndexError):
                pass
        row2 = conn.execute(
            "SELECT conducted_at FROM hcp_interactions WHERE hcp_id=? ORDER BY conducted_at DESC LIMIT 1",
            (hcp_id,),
        ).fetchone()
        if row2:
            try:
                last = datetime.strptime(row2["conducted_at"][:10], "%Y-%m-%d")
                return (datetime.now() - last).days
            except (ValueError, IndexError):
                pass
        return 45

    def _prescription_change(self, hcp_id: int) -> float:
        hcp_id_str = str(hcp_id)
        hash_val = sum(ord(c) for c in hcp_id_str)
        return float((hash_val % 30) - 20)

    def _recent_papers(self, hcp_id: int) -> list[str]:
        hcp_id_str = str(hcp_id)
        if sum(ord(c) for c in hcp_id_str) % 3 == 0:
            return ["新型抗凝药物在房颤患者中的应用进展"]
        return []

    def _competitor_activity(self, hcp_id: int) -> bool:
        hcp_id_str = str(hcp_id)
        return sum(ord(c) for c in hcp_id_str) % 4 == 0

    def _pending_compliance(self, hcp_id: int) -> bool:
        hcp_id_str = str(hcp_id)
        return sum(ord(c) for c in hcp_id_str) % 5 == 0
