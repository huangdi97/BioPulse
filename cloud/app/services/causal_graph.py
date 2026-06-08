"""因果图谱构建与反事实模拟方法。"""

import json
import uuid
from typing import Optional

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import CausalGraphsRepository, CounterfactualScenariosRepository


def _gen_graph_id() -> str:
    """生成因果图谱 ID，格式 cg:xxxxxxxx。"""
    return "cg:" + uuid.uuid4().hex[:8]


def _gen_scenario_id() -> str:
    """生成反事实场景 ID，格式 cf:xxxxxxxx。"""
    return "cf:" + uuid.uuid4().hex[:8]


def _generate_template_graph(decision_id: str) -> dict:
    """生成包含默认节点和边的因果图谱模板。

    Args:
        decision_id: 决策 ID

    Returns:
        含 nodes 和 edges 的图谱数据字典
    """
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
    """对单个反事实场景执行线性模拟计算。

    Args:
        scenario: 含 variable、from、to 的场景字典

    Returns:
        含变量、delta、预测结果和置信度的字典
    """
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
    """将因果图谱数据库行转换为字典。

    Args:
        row: 数据库行或字典

    Returns:
        含解析后 graph_data 的图谱字典
    """
    return {
        "id": row["id"],
        "graph_id": row["graph_id"],
        "decision_id": row["decision_id"],
        "graph_data": json.loads(row["graph_data"]) if isinstance(row["graph_data"], str) else row["graph_data"],
        "summary": row["summary"],
        "node_count": row["node_count"],
        "edge_count": row["edge_count"],
        "created_by": row["created_by"],
        "created_at": row["created_at"],
    }


def _scenario_to_dict(row) -> dict:
    """将反事实场景数据库行转换为字典。

    Args:
        row: 数据库行或字典

    Returns:
        含解析后 variable_changes 和 predicted_outcome 的场景字典
    """
    return {
        "id": row["id"],
        "scenario_id": row["scenario_id"],
        "strategy_id": row["strategy_id"],
        "base_description": row["base_description"],
        "variable_changes": json.loads(row["variable_changes"]) if isinstance(row["variable_changes"], str) else row["variable_changes"],
        "predicted_outcome": json.loads(row["predicted_outcome"]) if isinstance(row["predicted_outcome"], str) else row["predicted_outcome"],
        "confidence": row["confidence"],
        "created_by": row["created_by"],
        "created_at": row["created_at"],
    }


class CausalGraphMixin:
    """因果图谱持久化和反事实场景查询方法。"""

    def build_graph(self, decision_id: str, include_metrics: bool, user_id: int) -> dict:
        """构建一个因果图谱并持久化。

        Args:
            decision_id: 决策 ID，用于关联图与决策
            include_metrics: 是否包含额外指标（当前模板生成不使用）
            user_id: 创建者用户 ID

        Returns:
            新创建的因果图谱记录字典
        """
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
        """获取指定因果图谱详情。

        Args:
            graph_id: 图谱 ID

        Returns:
            因果图谱记录字典

        Raises:
            HTTPException: 图谱不存在时返回 404
        """
        cg_repo = CausalGraphsRepository(self.db)
        row = cg_repo.db.execute("SELECT * FROM causal_graphs WHERE graph_id=?", (graph_id,)).fetchone()
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Causal graph not found")
        return _causal_graph_to_dict(row)

    def simulate_counterfactual(self, strategy_id: str, scenarios: list[dict], user_id: int) -> dict:
        """对给定策略执行反事实模拟并持久化结果。

        Args:
            strategy_id: 策略 ID
            scenarios: 场景列表，每项含 variable、from、to 字段
            user_id: 创建者用户 ID

        Returns:
            包含 simulations 列表和 total 计数的字典
        """
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
                    "predicted_outcome": json.dumps(sim["predicted_outcome"], ensure_ascii=False),
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

    def list_counterfactuals(self, strategy_id: Optional[str] = None, page: int = 1, page_size: int = 20) -> dict:
        """分页查询反事实模拟场景列表。

        Args:
            strategy_id: 可选，按策略 ID 过滤
            page: 页码，默认 1
            page_size: 每页条数，默认 20

        Returns:
            包含 items、total、page、page_size 的字典
        """
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
