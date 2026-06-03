import json
import sqlite3


def seed_s2(conn: sqlite3.Connection) -> None:
    count_mcp = conn.execute("SELECT COUNT(*) FROM mcp_tools").fetchone()[0]
    count_ot = conn.execute("SELECT COUNT(*) FROM orchestration_templates").fetchone()[0]
    if count_mcp > 0 and count_ot > 0:
        return
    now = "2026-05-25 10:00:00"

    if count_mcp == 0:
        conn.execute(
            "INSERT INTO mcp_tools (tool_name, description, endpoint_url, input_schema, output_schema, "
            "created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
            (
                "知识图谱查询",
                "根据entity_id查KG",
                "",
                json.dumps({"entity_id": "string"}, ensure_ascii=False),
                json.dumps({}, ensure_ascii=False),
                now,
                now,
            ),
        )
        conn.execute(
            "INSERT INTO mcp_tools (tool_name, description, endpoint_url, input_schema, output_schema, "
            "created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
            (
                "合规检查",
                "检查内容合规性",
                "",
                json.dumps({"content": "string"}, ensure_ascii=False),
                json.dumps({}, ensure_ascii=False),
                now,
                now,
            ),
        )

    if count_ot == 0:
        conn.execute(
            "INSERT INTO orchestration_templates (template_name, description, steps, "
            "created_at, updated_at) VALUES (?,?,?,?,?)",
            (
                "竞品分析流水线",
                "市场情报→合规审查→HCP策略",
                json.dumps(
                    [
                        {"agent_role": "market_intel", "action": "analyze"},
                        {"agent_role": "compliance_checker", "action": "review"},
                        {"agent_role": "hcp_outreach", "action": "generate_strategy"},
                    ],
                    ensure_ascii=False,
                ),
                now,
                now,
            ),
        )
        conn.execute(
            "INSERT INTO orchestration_templates (template_name, description, steps, "
            "created_at, updated_at) VALUES (?,?,?,?,?)",
            (
                "HCP策略生成",
                "HCP画像分析→推荐策略",
                json.dumps(
                    [
                        {"agent_role": "hcp_outreach", "action": "analyze_profile"},
                        {"agent_role": "recommend", "action": "generate_strategy"},
                    ],
                    ensure_ascii=False,
                ),
                now,
                now,
            ),
        )

    conn.commit()
