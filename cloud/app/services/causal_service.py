import json
import uuid
from typing import Optional

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import (
    CausalGraphsRepository,
    CounterfactualScenariosRepository,
    EpisodicMemoryRepository,
    KgEntitiesRepository,
)
from cloud.app.services.base import BaseService


def _gen_graph_id() -> str:
    return "cg:" + uuid.uuid4().hex[:8]


def _gen_scenario_id() -> str:
    return "cf:" + uuid.uuid4().hex[:8]


def _generate_template_graph(decision_id: str) -> dict:
    return {
        "nodes": [
            {"id": "factor_a", "label": "关键因子A", "weight": 0.5},
            {"id": "factor_b", "label": "关键因子B", "weight": 0.3},
            {"id": "outcome", "label": "目标结果", "weight": 0.0},
        ],
        "edges": [
            {"source": "factor_a", "target": "outcome", "strength": 0.5},
            {"source": "factor_b", "target": "outcome", "strength": 0.3},
        ],
    }


def _linear_simulate(scenario: dict) -> dict:
    variable = scenario.get("variable", "unknown")
    from_val = float(scenario.get("from", 0))
    to_val = float(scenario.get("to", 0))
    delta = to_val - from_val
    multiplier = 5.0
    change_pct = round(delta * multiplier, 1)
    outcome = {f"{variable}影响": f"{change_pct:+.1f}%"}
    conf = min(0.95, max(0.3, 0.55 + abs(delta) * 0.05))
    return {
        "variable": variable,
        "from": from_val,
        "to": to_val,
        "delta": delta,
        "predicted_outcome": outcome,
        "confidence": round(conf, 4),
    }


def _causal_graph_to_dict(row) -> dict:
    return {
        "id": row["id"],
        "graph_id": row["graph_id"],
        "decision_id": row["decision_id"],
        "graph_data": json.loads(row["graph_data"])
        if isinstance(row["graph_data"], str)
        else row["graph_data"],
        "summary": row["summary"],
        "node_count": row["node_count"],
        "edge_count": row["edge_count"],
        "created_by": row["created_by"],
        "created_at": row["created_at"],
    }


def _scenario_to_dict(row) -> dict:
    return {
        "id": row["id"],
        "scenario_id": row["scenario_id"],
        "strategy_id": row["strategy_id"],
        "base_description": row["base_description"],
        "variable_changes": json.loads(row["variable_changes"])
        if isinstance(row["variable_changes"], str)
        else row["variable_changes"],
        "predicted_outcome": json.loads(row["predicted_outcome"])
        if isinstance(row["predicted_outcome"], str)
        else row["predicted_outcome"],
        "confidence": row["confidence"],
        "created_by": row["created_by"],
        "created_at": row["created_at"],
    }


class CausalService(BaseService):
    def build_graph(
        self, decision_id: str, include_metrics: bool, user_id: int
    ) -> dict:
        cg_repo = CausalGraphsRepository(self.db)
        graph_id = _gen_graph_id()
        graph_data = _generate_template_graph(decision_id)
        node_count = len(graph_data["nodes"])
        edge_count = len(graph_data["edges"])
        row_id = cg_repo.create(
            {
                "graph_id": graph_id,
                "decision_id": decision_id,
                "graph_data": json.dumps(graph_data, ensure_ascii=False),
                "node_count": node_count,
                "edge_count": edge_count,
                "created_by": user_id,
            }
        )
        row = cg_repo.get_by_id(row_id)
        return _causal_graph_to_dict(row)

    def get_graph(self, graph_id: str) -> dict:
        cg_repo = CausalGraphsRepository(self.db)
        row = cg_repo.db.execute(
            "SELECT * FROM causal_graphs WHERE graph_id=?", (graph_id,)
        ).fetchone()
        if not row:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, detail="Causal graph not found"
            )
        return _causal_graph_to_dict(row)

    def simulate_counterfactual(
        self, strategy_id: str, scenarios: list[dict], user_id: int
    ) -> dict:
        cs_repo = CounterfactualScenariosRepository(self.db)
        results: list[dict] = []
        for sc in scenarios:
            sim = _linear_simulate(sc)
            scenario_id = _gen_scenario_id()
            cs_repo.create(
                {
                    "scenario_id": scenario_id,
                    "strategy_id": strategy_id,
                    "variable_changes": json.dumps(
                        [
                            {
                                "variable": sim["variable"],
                                "from": sim["from"],
                                "to": sim["to"],
                            }
                        ],
                        ensure_ascii=False,
                    ),
                    "predicted_outcome": json.dumps(
                        sim["predicted_outcome"], ensure_ascii=False
                    ),
                    "confidence": sim["confidence"],
                    "created_by": user_id,
                }
            )
            results.append(
                {
                    "scenario_id": scenario_id,
                    "strategy_id": strategy_id,
                    "variable": sim["variable"],
                    "delta": sim["delta"],
                    "predicted_outcome": sim["predicted_outcome"],
                    "confidence": sim["confidence"],
                }
            )
        return {"simulations": results, "total": len(results)}

    def list_counterfactuals(
        self, strategy_id: Optional[str] = None, page: int = 1, page_size: int = 20
    ) -> dict:
        cs_repo = CounterfactualScenariosRepository(self.db)
        conditions = []
        params: list = []
        if strategy_id:
            conditions.append("strategy_id=?")
            params.append(strategy_id)
        total, total_pages, items = cs_repo.paginate(
            page=page,
            page_size=page_size,
            conditions=conditions or None,
            params=params or None,
            order_by="created_at DESC",
        )
        return {
            "items": [_scenario_to_dict(r) for r in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def causal_infer(self, features: dict, target: str, method: str = "linear") -> dict:
        total_weight = sum(abs(v) for v in features.values()) if features else 1.0
        weights = {
            k: round(v / total_weight if total_weight else 0, 4)
            for k, v in features.items()
        }
        return {
            "method": method,
            "target": target,
            "feature_weights": weights,
        }

    def hcp_prescription_attribution(
        self, hcp_entity_id: str, factors: list[str], date_range: dict
    ) -> dict:
        kg_repo = KgEntitiesRepository(self.db)
        em_repo = EpisodicMemoryRepository(self.db)
        hcp_row = kg_repo.db.execute(
            "SELECT * FROM kg_entities WHERE entity_id=? AND status='active'",
            (hcp_entity_id,),
        ).fetchone()
        if not hcp_row:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, detail="HCP entity not found in KG"
            )

        kg_id = hcp_row["id"]
        where_parts = ["(related_entity_type='kg_entity' AND related_entity_id=?)"]
        em_params = [kg_id]
        if factors:
            placeholders = ",".join(["?"] * len(factors))
            where_parts.append(f"event_type IN ({placeholders})")
            em_params.extend(factors)
        if date_range and date_range.get("start") and date_range.get("end"):
            where_parts.append("created_at BETWEEN ? AND ?")
            em_params.extend([date_range["start"], date_range["end"]])
        em_where = " AND ".join(where_parts)
        em_rows = em_repo.db.execute(
            f"SELECT * FROM episodic_memory WHERE {em_where} ORDER BY created_at DESC LIMIT 50",
            em_params,
        ).fetchall()

        activities = []
        for em in em_rows:
            ctx = (
                json.loads(em["context"])
                if isinstance(em["context"], str) and em["context"]
                else {}
            )
            activities.append(
                {
                    "event_type": em["event_type"],
                    "title": em["title"],
                    "outcome": em["outcome"],
                    "valence": em["valence"],
                    "intensity": em["intensity"],
                    "context": ctx,
                    "created_at": em["created_at"],
                }
            )

        hcp_props = (
            json.loads(hcp_row.get("properties", "{}") or "{}")
            if isinstance(hcp_row.get("properties", "{}"), str)
            else (hcp_row.get("properties") or {})
        )
        attribution = {
            "hcp": {
                "entity_id": hcp_row["entity_id"],
                "name": hcp_row["name"],
                "entity_type": hcp_row["entity_type"],
                "properties": hcp_props,
            },
            "related_activities": activities,
            "activity_count": len(activities),
            "attribution_summary": f"{hcp_row['name']} 关联 {len(activities)} 条活动记录",
        }
        if activities:
            avg_valence = sum(a["valence"] for a in activities) / len(activities)
            avg_intensity = sum(a["intensity"] for a in activities) / len(activities)
            attribution["aggregated_metrics"] = {
                "avg_valence": round(avg_valence, 4),
                "avg_intensity": round(avg_intensity, 4),
            }
        return attribution
