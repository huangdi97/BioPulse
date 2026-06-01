import json
import sqlite3


def seed_market_intel(conn: sqlite3.Connection) -> None:
    """Insert default market intel sources and items if tables are empty."""
    count = conn.execute("SELECT COUNT(*) FROM market_intel_sources").fetchone()[0]
    if count > 0:
        return
    sources = [
        ("竞品A动态监控", "competitor", '["竞品A","产品X","市场份额","药品注册"]'),
        ("医药政策法规追踪", "policy", '["医保","集采","DRG","DIP","医药政策","药品审批"]'),
        ("前沿学术进展", "academic", '["新药","临床研究","期刊","学术会议","靶点"]'),
        ("行业市场趋势", "industry", '["市场报告","行业分析","投融资","趋势","份额"]'),
        ("竞品B情报追踪", "competitor", '["竞品B","产品Y","销售策略","渠道"]'),
    ]
    conn.executemany(
        "INSERT INTO market_intel_sources (name, source_type, target_keywords) VALUES (?, ?, ?)",
        sources,
    )
    now = "2026-05-15 09:00:00"
    items = [
        (1, "competitor", "竞品A新药获批上市", "竞品A的XX新药获得NMPA批准上市，适应症为晚期肺癌", "https://example.com/news1", "medium", now),
        (1, "competitor", "竞品A扩大销售团队", "竞品A宣布在全国新增200名销售代表", "https://example.com/news2", "low", "2026-05-16 10:00:00"),
        (2, "policy", "国家医保目录调整方案征求意见", "国家医保局发布2026年医保目录调整方案征求意见稿，新增谈判药品目录", "https://example.com/news3", "critical", "2026-05-17 08:00:00"),
        (2, "policy", "DRG/DIP支付改革全面推行", "国家卫健委要求2026年底前全国三级医院全面实施DRG/DIP付费", "https://example.com/news4", "high", "2026-05-18 14:00:00"),
        (3, "academic", "PD-1联合疗法III期临床数据公布", "某期刊发表PD-1联合化疗一线治疗胃癌III期临床阳性结果", "https://example.com/news5", "high", "2026-05-19 11:00:00"),
        (3, "academic", "新型ADC药物前临床研究发表", "某团队在Nature发表新型ADC药物的前临床研究数据", "https://example.com/news6", "low", "2026-05-20 16:00:00"),
        (4, "industry", "2026中国医药市场年度报告发布", "报告显示中国医药市场总规模突破2.5万亿元，创新药占比提升至35%", "https://example.com/news7", "medium", "2026-05-21 09:00:00"),
        (4, "industry", "医药行业Q2投融资数据", "Q2医药行业投融资总额320亿元，同比增长18%，集中在生物技术和创新药领域", "https://example.com/news8", "low", "2026-05-22 10:00:00"),
        (5, "competitor", "竞品B获重点医院独家供应", "竞品B与全国50家三甲医院签订独家供应协议", "https://example.com/news9", "high", "2026-05-23 13:00:00"),
        (5, "competitor", "竞品B开展数字化营销", "竞品B上线AI辅助医生教育平台，覆盖超万名医生", "https://example.com/news10", "medium", "2026-05-24 15:00:00"),
    ]
    conn.executemany(
        "INSERT INTO market_intel_items (source_id, item_type, title, summary, url, impact_level, collected_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        items,
    )
    conn.commit()
