"""
商机因果归因评分服务。

利用已有 causal_service 的因果推断能力 + opportunity 端的因子数据，
为每个商机计算因果影响分解。
"""

import json
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from starlette import status

from cloud.app.services.base import BaseService


def _today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _days_ago(n: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=n)).strftime("%Y-%m-%d")


_FACTOR_META = [
    {
        "name": "visit_frequency",
        "display_name": "拜访频率",
        "max_score": 35,
        "description": "近30天客户拜访次数。>5次给30-35分，3-5次给20-29分，1-2次给5-19分，0次给0分",
    },
    {
        "name": "product_match",
        "display_name": "产品匹配度",
        "max_score": 25,
        "description": "商机阶段匹配度。negotiation/won给20-25分，proposal给10-19分，lead/qualify给0-9分",
    },
    {
        "name": "hcp_relation",
        "display_name": "HCP关系强度",
        "max_score": 20,
        "description": "近60天与该客户关联的正面交互占比*20",
    },
    {
        "name": "competitor_threat",
        "display_name": "竞品活动",
        "max_score": 15,
        "description": "竞品活动记录扣分，最多-15分",
    },
    {
        "name": "time_window",
        "display_name": "时间窗口",
        "max_score": 10,
        "description": "距close_date<30天给8-10分，30-60天给4-7分，>60天或空给0分",
    },
    {
        "name": "stage_weight",
        "display_name": "阶段权重",
        "max_score": 10,
        "description": "won=10, negotiation=8, proposal=6, qualify=3, lead=1, lost=0",
    },
]

_STAGE_WEIGHTS = {
    "won": 10,
    "closed_won": 10,
    "negotiation": 8,
    "proposal": 6,
    "qualify": 3,
    "qualification": 3,
    "lead": 1,
    "lost": 0,
    "closed_lost": 0,
}

_RECOMMENDATIONS = {
    "visit_frequency": "建议增加HCP拜访频次，提升商机推进速度。",
    "product_match": "产品匹配度处于高位，建议加快商务谈判进程。",
    "hcp_relation": "HCP关系是当前最强驱动因子，建议维持并深化合作关系。",
    "competitor_threat": "竞品活动活跃，建议加强差异化价值传递并密切关注竞品动向。",
    "time_window": "时间窗口紧迫，建议优先处理该商机的关键决策节点。",
    "stage_weight": "商机阶段权重较高，建议保持当前推进节奏。",
}


def _calc_month_days(close_date: str) -> int:
    try:
        clean = close_date.replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return (dt - datetime.now(timezone.utc)).days
    except (ValueError, TypeError):
        return -1


class CausalAttributionService(BaseService):
    """CausalAttribution 服务类。"""

    def get_attribution(self, opp_id: int) -> dict:
        """get_attribution 操作。

        Args:
            opp_id: 描述

        Returns:
            描述
        """
        row = self.db.execute(
            "SELECT * FROM opportunity_attributions WHERE opportunity_id=?",
            (opp_id,),
        ).fetchone()
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Attribution not found")
        return self._row_to_dict(row)

    def refresh_attribution(self, opp_id: int) -> dict:
        """refresh_attribution 操作。

        Args:
            opp_id: 描述

        Returns:
            描述
        """
        opp = self.db.execute(
            "SELECT * FROM opportunities WHERE id=? AND is_active=1",
            (opp_id,),
        ).fetchone()
        if not opp:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail="Opportunity not found",
            )

        stage = opp["stage"] or "lead"
        customer_id = opp["customer_id"]
        close_date = opp.get("close_date") or ""

        visit_count = self._count_visits(customer_id)
        product_match = self._calc_product_match(stage)
        hcp_score = self._calc_hcp_relation(customer_id)
        competitor = self._calc_competitor_threat(customer_id)
        time_score = self._calc_time_window(close_date)
        stage_score = _STAGE_WEIGHTS.get(stage, 1)

        factors_list = [
            {"name": "visit_frequency", "impact": visit_count, "direction": "positive", "weight": 0.3},
            {"name": "product_match", "impact": product_match, "direction": "positive", "weight": 0.25},
            {"name": "hcp_relation", "impact": hcp_score, "direction": "positive", "weight": 0.2},
            {"name": "competitor_threat", "impact": -competitor, "direction": "negative", "weight": 0.15},
            {"name": "time_window", "impact": time_score, "direction": "positive", "weight": 0.1},
            {"name": "stage_weight", "impact": stage_score, "direction": "positive", "weight": 0.0},
        ]

        total_score = visit_count + product_match + hcp_score - competitor + time_score + stage_score
        total_score = max(0, min(total_score, 105))

        has_visit = visit_count > 0
        has_interaction = hcp_score > 0
        if has_visit and has_interaction:
            confidence = round(0.7 + 0.2 * min(visit_count / 10, 1.0), 2)
        else:
            confidence = round(0.3 + 0.2 * (1 if has_visit or has_interaction else 0), 2)

        top_factor = max(factors_list, key=lambda f: abs(f["impact"]))
        top_factor_name = top_factor["name"]
        recommendation = _RECOMMENDATIONS.get(top_factor_name, "")

        now = _today_str()
        self.db.execute(
            "INSERT OR REPLACE INTO opportunity_attributions "
            "(opportunity_id, total_score, confidence, factors, factor_count, top_factor_name, recommendation, model_version, updated_at) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (
                opp_id,
                total_score,
                confidence,
                json.dumps(factors_list, ensure_ascii=False),
                len(factors_list),
                top_factor_name,
                recommendation,
                "causal_v1",
                now,
            ),
        )
        self.db.commit()

        return self.get_attribution(opp_id)

    def simulate_outcome(self, opp_id: int, what_if_changes: dict[str, float]) -> dict:
        """simulate_outcome 操作。

        Args:
            opp_id: 描述
            what_if_changes: 描述

        Returns:
            描述
        """
        attribution = self.refresh_attribution(opp_id)

        original_score = attribution["total_score"]
        original_factors: list[dict] = attribution["factors"]

        simulated_factors = []
        for f in original_factors:
            f_copy = dict(f)
            name = f_copy["name"]
            if name in what_if_changes:
                f_copy["impact"] = what_if_changes[name]
            simulated_factors.append(f_copy)

        simulated_score = sum(f["impact"] for f in simulated_factors)
        simulated_score = max(0, min(simulated_score, 105))

        delta = round(simulated_score - original_score, 2)

        factors_impact = []
        for orig, sim in zip(original_factors, simulated_factors):
            factors_impact.append(
                {
                    "name": orig["name"],
                    "original_impact": orig["impact"],
                    "simulated_impact": sim["impact"],
                    "delta": round(sim["impact"] - orig["impact"], 2),
                }
            )

        return {
            "opportunity_id": opp_id,
            "original_score": original_score,
            "simulated_score": simulated_score,
            "delta": delta,
            "factors_impact": factors_impact,
        }

    def list_factors(self) -> list[dict]:
        """list_factors 操作。

        Returns:
            描述
        """
        return list(_FACTOR_META)

    def _count_visits(self, customer_id: int) -> int:
        since = _days_ago(30)
        row = self.db.execute(
            "SELECT COUNT(*) AS cnt FROM customer_interactions WHERE customer_id=? AND conducted_at>=?",
            (customer_id, since),
        ).fetchone()
        count = row["cnt"] if row else 0
        if count > 5:
            return min(30 + (count - 5), 35)
        if count >= 3:
            return 20 + (count - 3) * 5
        if count >= 1:
            return 5 + (count - 1) * 14
        return 0

    def _calc_product_match(self, stage: str) -> int:
        stage_lower = stage.lower()
        if stage_lower in ("negotiation", "closed_won", "won"):
            return 25
        if stage_lower in ("proposal",):
            return 15
        if stage_lower in ("qualify", "qualification"):
            return 5
        return 0

    def _calc_hcp_relation(self, customer_id: int) -> int:
        since = _days_ago(60)
        rows = self.db.execute(
            "SELECT outcome FROM episodic_memory WHERE related_entity_id=? AND created_at>=?",
            (customer_id, since),
        ).fetchall()
        if not rows:
            return 0
        positive = sum(1 for r in rows if r["outcome"] in ("success", "positive", "completed"))
        ratio = positive / len(rows)
        return int(ratio * 20)

    def _calc_competitor_threat(self, customer_id: int) -> int:
        since = _days_ago(60)
        row = self.db.execute(
            "SELECT COUNT(*) AS cnt FROM market_intel_items WHERE item_type='competitor' AND collected_at>=?",
            (since,),
        ).fetchone()
        count = row["cnt"] if row else 0
        return min(count * 5, 15)

    def _calc_time_window(self, close_date: str) -> int:
        if not close_date:
            return 0
        days = _calc_month_days(close_date)
        if days < 0:
            return 0
        if days < 30:
            return 10
        if days <= 60:
            return 7
        return 0

    @staticmethod
    def _row_to_dict(row) -> dict:
        factors_raw = row["factors"]
        if isinstance(factors_raw, str):
            factors = json.loads(factors_raw)
        else:
            factors = factors_raw or []
        return {
            "opportunity_id": row["opportunity_id"],
            "total_score": row["total_score"],
            "confidence": row["confidence"],
            "factors": factors,
            "factor_count": row["factor_count"],
            "top_factor_name": row["top_factor_name"],
            "recommendation": row["recommendation"],
            "model_version": row["model_version"],
            "created_at": row["created_at"],
            "updated_at": row.get("updated_at", ""),
        }
