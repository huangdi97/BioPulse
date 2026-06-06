"""种子数据：预设决策案例与跨案例洞察。"""

import sqlite3


def seed_decision_intel(conn: sqlite3.Connection) -> None:
    """Insert preset decision cases and cross-case insights if tables are empty."""
    count = conn.execute("SELECT COUNT(*) FROM decision_cases").fetchone()[0]
    if count > 0:
        return
    now = "2026-05-25 10:00:00"
    cases = [
        (
            "竞品A新药上市应对",
            "对竞品A新药上市后的销售策略效果分析",
            "待评估",
            0.3,
            {
                "product_area": "肿瘤",
                "competitor": "竞品A",
                "input_features": {
                    "response_speed": "slow",
                    "data_preparation": "moderate",
                },
            },
            ["竞品分析", "策略评估"],
        ),
        (
            "集采政策应对策略",
            "集采政策出台后的市场应对策略评估",
            "失败",
            -0.5,
            {
                "product_area": "心血管",
                "policy": "国家集采",
                "input_features": {
                    "adjustment_speed": "slow",
                    "portfolio_depth": "shallow",
                },
            },
            ["政策应对", "集采"],
        ),
        (
            "学术推广活动效果评估",
            "针对关键意见领袖精准投放的学术推广效果",
            "成功",
            0.8,
            {
                "product_area": "免疫",
                "channel": "KOL",
                "input_features": {"targeting": "precise", "content_quality": "high"},
            },
            ["学术推广", "KOL"],
        ),
    ]
    import json as _json

    for name, desc, outcome, score, ctx, tags in cases:
        cur = conn.execute(
            "INSERT INTO decision_cases (name, description, outcome, outcome_score, context, tags, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
            (
                name,
                desc,
                outcome,
                score,
                _json.dumps(ctx, ensure_ascii=False),
                _json.dumps(tags, ensure_ascii=False),
                now,
                now,
            ),
        )
        case_id = cur.lastrowid
        drivers = _json.dumps(
            [
                {
                    "factor": k,
                    "impact": "medium",
                    "direction": "positive" if score > 0 else "negative",
                }
                for k in ctx.get("input_features", {}).keys()
            ],
            ensure_ascii=False,
        )
        chain = _json.dumps(
            [{"cause": "策略执行", "effect": outcome, "strength": abs(score)}],
            ensure_ascii=False,
        )
        attr = _json.dumps(
            {k: score / max(1, len(ctx.get("input_features", {}))) for k in ctx.get("input_features", {})},
            ensure_ascii=False,
        )
        recs = _json.dumps(["继续强化该策略" if score > 0 else "重新评估策略方向"], ensure_ascii=False)
        conn.execute(
            "INSERT INTO causal_analyses (case_id, summary, key_drivers, causal_chain, "
            "attribution_scores, recommendations, ai_response_raw) VALUES (?,?,?,?,?,?,?)",
            (
                case_id,
                f"预置分析: {desc}",
                drivers,
                chain,
                attr,
                recs,
                _json.dumps({"simulated": True}, ensure_ascii=False),
            ),
        )
    insights = [
        (
            "抢先发布竞品对比数据可提升市场份额",
            "pattern",
            "多案例显示，率先发布客观竞品临床数据对比的团队市场份额增长显著高于被动应对者",
            "成功案例中竞品分析节奏早于竞品3个月以上的团队份额提升15%-20%",
            0.7,
            "general",
        ),
        (
            "忽视政策变化信号将导致策略失效",
            "pitfall",
            "失败案例普遍存在政策信号响应延迟超过2个月的问题",
            "集采政策案例中，未提前准备产品线的团队丢失了关键市场份额",
            0.8,
            "pipeline_type",
        ),
        (
            "联合关键意见领袖进行学术推广效果显著",
            "best_practice",
            "联合核心医院意见领袖进行学术推广的案例，产品认知度平均提升40%",
            "学术推广案例中，精准KOL投放结合学术活动使处方量增长35%",
            0.65,
            "general",
        ),
    ]
    for title, itype, summary, detail, conf, appl in insights:
        conn.execute(
            "INSERT INTO cross_case_insights (title, insight_type, summary, detail, "
            "confidence, applicability, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
            (title, itype, summary, detail, conf, appl, now, now),
        )
    conn.commit()
