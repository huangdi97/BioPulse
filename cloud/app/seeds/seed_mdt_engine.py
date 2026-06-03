import sqlite3


def seed_mdt_engine(conn: sqlite3.Connection) -> None:
    """Insert preset MDT debate sessions, participants and opinions if empty."""
    count = conn.execute("SELECT COUNT(*) FROM mdt_sessions").fetchone()[0]
    if count > 0:
        return
    now = "2026-05-25 10:00:00"
    import json as _json

    sessions = [
        (
            "集采政策应对策略辩论",
            "面对国家集采政策，我们应采取什么样的市场应对策略？",
            "国家医保局持续推进药品集中带量采购，覆盖品种不断扩大。企业面临降价压力和市场份额重新分配。",
            "active",
            1,
            now,
            now,
        ),
        (
            "新市场准入与产品差异化策略",
            "新市场准入过程中如何平衡产品差异化和成本控制？",
            "新产品进入三甲医院面临院药事会、招标采购等多个环节，竞争激烈。",
            "active",
            0,
            now,
            now,
        ),
    ]
    session_ids = []
    for title, q, ctx, st, rc, ca, ua in sessions:
        cur = conn.execute(
            "INSERT INTO mdt_sessions (title, question, context, status, round_count, created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
            (title, q, ctx, st, rc, ca, ua),
        )
        session_ids.append(cur.lastrowid)
    session1_participants = [
        (session_ids[0], 1, "情报分析师Agent", "中立分析", 1.0),
        (session_ids[0], 2, "策略规划Agent", "支持差异化与创新", 1.2),
        (session_ids[0], 3, "销售代表Agent", "关注执行可行性", 1.0),
        (session_ids[0], 4, "复盘分析师Agent", "以数据与历史案例为据", 1.0),
    ]
    session2_participants = [
        (session_ids[1], 1, "情报分析师Agent", "中立数据驱动", 1.0),
        (session_ids[1], 2, "策略规划Agent", "差异化优先", 1.2),
        (session_ids[1], 3, "销售代表Agent", "成本与落地优先", 1.0),
        (session_ids[1], 4, "复盘分析师Agent", "案例验证导向", 1.0),
    ]
    all_participants = session1_participants + session2_participants
    part_ids = []
    for sid, arid, rn, stance, vw in all_participants:
        cur = conn.execute(
            "INSERT INTO mdt_participants (session_id, agent_role_id, role_name, stance, vote_weight, created_at) VALUES (?,?,?,?,?,?)",
            (sid, arid, rn, stance, vw, now),
        )
        part_ids.append(cur.lastrowid)
    s1_opinions = [
        (
            session_ids[0],
            part_ids[0],
            1,
            "根据情报分析，集采政策已覆盖65%以上的公立医院市场，降价幅度平均52%。建议加强创新药管线布局，降低对仿制药的依赖。",
            "集采影响范围扩大，创新转型是根本出路",
            "constructive",
            0.85,
            _json.dumps(
                ["集采覆盖率65%", "平均降幅52%", "创新药转型", "仿制药风险"],
                ensure_ascii=False,
            ),
            _json.dumps({"simulated": True}, ensure_ascii=False),
        ),
        (
            session_ids[0],
            part_ids[1],
            1,
            "策略上建议采取差异化产品定位：一是聚焦未集采的治疗领域开发高价值产品，二是通过学术推广建立品牌护城河，三是考虑探索医联体内部用药目录。",
            "差异化定位三大策略：领域选择、品牌建设、医联体渠道",
            "positive",
            0.90,
            _json.dumps(
                ["差异化定位", "学术推广", "医联体渠道", "品牌护城河"],
                ensure_ascii=False,
            ),
            _json.dumps({"simulated": True}, ensure_ascii=False),
        ),
        (
            session_ids[0],
            part_ids[2],
            1,
            "从执行层面看，学术推广成本上升约30%，需要评估ROI。建议结合数字化营销工具降低触达成本，同时关注基层市场增量机会。",
            "需要关注执行成本和基层市场机会",
            "mixed",
            0.78,
            _json.dumps(
                ["推广成本上升30%", "数字化工具", "ROI评估", "基层市场"],
                ensure_ascii=False,
            ),
            _json.dumps({"simulated": True}, ensure_ascii=False),
        ),
        (
            session_ids[0],
            part_ids[3],
            1,
            "复盘历史数据：成功应对集采的企业普遍提前2-3年布局创新产品线，同时在成本控制上做到行业前30%。建议量化各策略的时间成本和预期收益。",
            "历史数据显示提前布局和成本控制是关键成功因素",
            "analytical",
            0.88,
            _json.dumps(
                ["提前2-3年布局", "成本控制行业前30%", "量化分析", "时间成本"],
                ensure_ascii=False,
            ),
            _json.dumps({"simulated": True}, ensure_ascii=False),
        ),
    ]
    for sid, pid, rn, opinion, summary, sentiment, conf, kp, ai_raw in s1_opinions:
        conn.execute(
            "INSERT INTO mdt_opinions (session_id, participant_id, round_number, opinion, summary, "
            "sentiment, confidence, key_points, ai_response_raw, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (sid, pid, rn, opinion, summary, sentiment, conf, kp, ai_raw, now),
        )
    conn.commit()
