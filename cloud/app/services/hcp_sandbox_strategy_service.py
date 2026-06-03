import json

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import (
    HcpInteractionsRepository,
    HcpProfilesRepository,
    HcpSimulationsRepository,
)
from cloud.app.services.base import BaseService


class HcpSandboxStrategyService(BaseService):
    """HcpSandboxStrategy 服务类。"""

    def list_strategies(self) -> list:
        """获取策略列表。

        Returns:
            描述
        """
        cursor = self.db.execute("SELECT * FROM sandbox_strategies ORDER BY is_default DESC, name ASC")
        return [dict(r) for r in cursor.fetchall()]

    def create_strategy(self, name: str, description: str, parameters: dict, created_by: int) -> dict:
        """创建策略。

        Args:
            name: 描述
            description: 描述
            parameters: 描述
            created_by: 描述

        Returns:
            描述
        """
        cursor = self.db.execute(
            "INSERT INTO sandbox_strategies (name, description, parameters, created_by) VALUES (?, ?, ?, ?)",
            (name, description, json.dumps(parameters, ensure_ascii=False), created_by),
        )
        self.db.commit()
        row = self.db.execute("SELECT * FROM sandbox_strategies WHERE id=?", (cursor.lastrowid,)).fetchone()
        return dict(row)

    def delete_strategy(self, strategy_id: int) -> None:
        """删除策略。

        Args:
            strategy_id: 描述

        Returns:
            描述
        """
        cursor = self.db.execute("DELETE FROM sandbox_strategies WHERE id=?", (strategy_id,))
        self.db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Strategy not found")

    def simulate_v2(self, hcp_id: int, strategy_id: int, scenario_label: str, user_id: int) -> dict:
        """simulate_v2 操作。

        Args:
            hcp_id: 描述
            strategy_id: 描述
            scenario_label: 描述
            user_id: 描述

        Returns:
            描述
        """
        profiles_repo = HcpProfilesRepository(self.db)
        hcp = profiles_repo.get_by_id(hcp_id)
        if not hcp:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="HCP profile not found")
        strategy = self.db.execute("SELECT * FROM sandbox_strategies WHERE id=?", (strategy_id,)).fetchone()
        if not strategy:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Strategy not found")
        params = json.loads(strategy["parameters"]) if isinstance(strategy["parameters"], str) else strategy["parameters"]
        base = {
            "prescription_volume": hcp["prescription_volume"],
            "influence_score": hcp["influence_score"],
            "digital_engagement": hcp["digital_engagement"],
        }
        sim = dict(base)
        mult = {"high": 0.7, "medium": 0.85}.get(params.get("competitor_intensity", ""), 1.0)
        vf = params.get("visit_freq", "")
        if vf == "high":
            sim["prescription_volume"] += base["prescription_volume"] * 0.15 * mult
            sim["influence_score"] += base["influence_score"] * 0.10 * mult
        elif vf == "medium":
            sim["prescription_volume"] += base["prescription_volume"] * 0.08 * mult
            sim["influence_score"] += base["influence_score"] * 0.05 * mult
        elif vf == "low":
            sim["prescription_volume"] += base["prescription_volume"] * 0.03 * mult
        ct = params.get("content_type", "")
        if ct == "academic":
            sim["influence_score"] += base["influence_score"] * 0.08 * mult
        elif ct == "digital":
            sim["digital_engagement"] += base["digital_engagement"] * 0.15 * mult
        delta = self._calc_delta(base, sim)
        interactions_repo = HcpInteractionsRepository(self.db)
        icount = interactions_repo.count_by_hcp_id(hcp_id)
        sim_repo = HcpSimulationsRepository(self.db)
        scount = sim_repo.count_by_hcp_id(hcp_id)
        confidence = 0.6
        if icount > 0:
            confidence += 0.1
        if hcp.get("traits") and hcp["traits"] not in ("{}", "", "null"):
            confidence += 0.1
        if scount > 3:
            confidence += 0.1
        bscore = base["prescription_volume"] + base["influence_score"] + base["digital_engagement"]
        sscore = sim["prescription_volume"] + sim["influence_score"] + sim["digital_engagement"]
        cursor = self.db.execute(
            "INSERT INTO sandbox_simulations_v2 (hcp_id, strategy_id, baseline_score, simulated_score, delta, confidence, scenario_label, parameters_used, result_detail, created_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                hcp_id,
                strategy_id,
                bscore,
                sscore,
                json.dumps(delta, ensure_ascii=False),
                confidence,
                scenario_label,
                json.dumps(params, ensure_ascii=False),
                json.dumps({"baseline": base, "simulated": sim, "delta": delta}, ensure_ascii=False),
                user_id,
            ),
        )
        self.db.commit()
        return {
            "id": cursor.lastrowid,
            "baseline": base,
            "simulated": sim,
            "delta": delta,
            "confidence": confidence,
            "scenario_label": scenario_label,
            "strategy_name": strategy["name"],
            "parameters_used": params,
        }

    def get_impact_report(self, hcp_id: int) -> dict:
        """get_impact_report 操作。

        Args:
            hcp_id: 描述

        Returns:
            描述
        """
        profiles_repo = HcpProfilesRepository(self.db)
        hcp = profiles_repo.get_by_id(hcp_id)
        if not hcp:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="HCP profile not found")
        sims = self.db.execute(
            "SELECT * FROM sandbox_simulations_v2 WHERE hcp_id=? ORDER BY created_at DESC LIMIT 5",
            (hcp_id,),
        ).fetchall()
        interactions_repo = HcpInteractionsRepository(self.db)
        ics = interactions_repo.get_recent_by_hcp_id(hcp_id, limit=5)
        return {
            "profile": {k: v for k, v in hcp.items() if k != "traits"},
            "recent_simulations": [dict(s) for s in sims],
            "interaction_summary": ics,
        }

    @staticmethod
    def _calc_delta(base: dict, simulated: dict) -> dict:
        """return {k: round(simulated.get(k, 0) - base.get(k, 0), 4) for k in base}"""
