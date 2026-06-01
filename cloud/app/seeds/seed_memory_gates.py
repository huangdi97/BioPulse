import json
import sqlite3


def seed_memory_gates(conn: sqlite3.Connection) -> None:
    """Insert default memory gates and preset entries if tables are empty."""
    count = conn.execute("SELECT COUNT(*) FROM memory_gates").fetchone()[0]
    if count > 0:
        return
    now = "2026-05-25 10:00:00"
    import json as _json
    gates = [
        ("insight_gate", "insight", 0.6, 90, "normal"),
        ("case_gate", "case", 0.7, 180, "normal"),
        ("compliance_gate", "compliance", 0.5, 60, "normal"),
    ]
    conn.executemany(
        "INSERT INTO memory_gates (name, source_type, importance_threshold, ttl_days, retention_policy, created_at) "
        "VALUES (?,?,?,?,?,?)",
        [(g[0], g[1], g[2], g[3], g[4], now) for g in gates],
    )
    entries = [
        ("竞品A新药获批对晚期肺癌市场的冲击分析",
         "竞品A的XX新药获得NMPA批准上市，适应症为晚期肺癌。该产品在III期临床中ORR达到58%，显著优于现有标准治疗。预计将在未来6个月内对我们在肺癌领域的产品造成15%-20%的市场份额冲击。建议加强学术推广力度，加速我们同类管线的临床进度。",
         "insight", "insight", "", 0.85,
         _json.dumps(["竞品分析", "肺癌", "市场冲击", "学术推广"], ensure_ascii=False)),
        ("集采政策下创新药转型的必要性与路径分析",
         "根据多轮MDT辩论的共识，集采政策已覆盖65%以上公立医院市场，平均降价52%。企业必须加速创新药管线布局，降低对仿制药依赖。建议优先布局未集采治疗领域的高价值产品，通过学术推广建立品牌护城河，并探索医联体渠道。",
         "insight", "insight", "", 0.92,
         _json.dumps(["集采政策", "创新转型", "品牌建设", "医联体"], ensure_ascii=False)),
        ("竞品A新药上市应对策略效果复盘",
         "针对竞品A新药上市采取差异化产品定位和学术推广组合策略，处方量增长率从-5%回升至+8%，但市场份额仍未完全恢复。关键成功因素：提前准备竞品对比数据；关键失败因素：响应速度偏慢，启动滞后2个月。",
         "case", "case", "", 0.75,
         _json.dumps(["竞品应对", "策略复盘", "成功因素", "失败教训"], ensure_ascii=False)),
        ("集采政策应对复盘：关键教训与改进方向",
         "集采应对案例总结：由于未提前准备产品线组合方案，且政策响应延迟超过2个月，导致肿瘤产品在集采中丢失关键市场份额。核心教训：必须建立政策预警机制，提前6个月准备替代方案，保持产品线深度。",
         "case", "case", "", 0.88,
         _json.dumps(["集采应对", "失败复盘", "政策预警", "产品线深度"], ensure_ascii=False)),
        ("合规审查高频违规项：绝对化用语与对比声明",
         "根据近期合规审计数据分析，绝对化用语（如'根治''最佳'）和疗效对比声明是最常见违规类型，占全部违规记录的65%。建议所有市场材料发布前强制执行合规预审流程，并加强一线销售代表的合规培训频次至每月一次。",
         "compliance", "compliance", "", 0.82,
         _json.dumps(["合规审查", "绝对化用语", "对比声明", "培训"], ensure_ascii=False)),
    ]
    conn.executemany(
        "INSERT INTO memory_entries (title, content, memory_type, source_type, source_id, "
        "importance, context_tags, access_count, created_by, created_at, updated_at) "
        "VALUES (?,?,?,?,?,?,?,0,1,?,?)",
        [(e[0], e[1], e[2], e[3], e[4], e[5], e[6], now, now) for e in entries],
    )
    conn.commit()
