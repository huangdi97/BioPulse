import json
import sqlite3


def seed_s3(conn: sqlite3.Connection) -> None:
    count_cg = conn.execute("SELECT COUNT(*) FROM causal_graphs").fetchone()[0]
    count_cs = conn.execute("SELECT COUNT(*) FROM counterfactual_scenarios").fetchone()[0]
    if count_cg > 0 and count_cs > 0:
        return
    now = "2026-05-25 10:00:00"

    if count_cg == 0:
        conn.execute(
            "INSERT INTO causal_graphs (graph_id, decision_id, graph_data, node_count, edge_count, created_at) VALUES (?,?,?,?,?,?)",
            (
                "cg:test-001",
                "decision-01",
                json.dumps(
                    {
                        "nodes": [
                            {"id": "拜访频率", "label": "拜访频率", "weight": 0.6},
                            {"id": "处方量", "label": "处方量", "weight": 0},
                            {"id": "学术活动", "label": "学术活动参与", "weight": 0.4},
                        ],
                        "edges": [
                            {"source": "拜访频率", "target": "处方量", "strength": 0.6},
                            {"source": "学术活动", "target": "处方量", "strength": 0.4},
                        ],
                    },
                    ensure_ascii=False,
                ),
                3,
                2,
                now,
            ),
        )

    if count_cs == 0:
        conn.execute(
            "INSERT INTO counterfactual_scenarios (scenario_id, strategy_id, base_description, "
            "variable_changes, predicted_outcome, confidence, created_at) VALUES (?,?,?,?,?,?,?)",
            (
                "cf:test-001",
                "strategy-01",
                "",
                json.dumps([{"variable": "拜访频率", "from": 3, "to": 6}], ensure_ascii=False),
                json.dumps({"处方量变化": "+15%"}, ensure_ascii=False),
                0.75,
                now,
            ),
        )
        conn.execute(
            "INSERT INTO counterfactual_scenarios (scenario_id, strategy_id, base_description, "
            "variable_changes, predicted_outcome, confidence, created_at) VALUES (?,?,?,?,?,?,?)",
            (
                "cf:test-002",
                "strategy-01",
                "",
                json.dumps([{"variable": "学术活动", "from": 1, "to": 3}], ensure_ascii=False),
                json.dumps({"处方量变化": "+10%"}, ensure_ascii=False),
                0.65,
                now,
            ),
        )

    conn.commit()
