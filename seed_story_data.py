"""一云四端演示数据 — 完整业务故事线
故事线贯穿：医药拜访 → 合规拦截 → 科研PI → 跟台手术 → 管理看板
"""

import os
import random
import sqlite3
from datetime import datetime, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))

# ============================================================
# PART 1: Cloud DB — 用户 / HCP / 拜访 / 内容 / 审计
# ============================================================


def seed_cloud():
    db_path = os.path.join(BASE, "data", "cloud.db")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    base = datetime(2026, 4, 15)

    # --- 1.1 用户 ---
    cur.execute("DELETE FROM users WHERE id > 1")
    users_data = [
        ("zhang_san", "$2b$12$demo", "rep", 1, (base + timedelta(days=0)).isoformat()),
        ("li_si", "$2b$12$demo", "rep", 1, (base + timedelta(days=5)).isoformat()),
        ("wang_wu", "$2b$12$demo", "rep", 1, (base + timedelta(days=15)).isoformat()),
        ("zhao_liu", "$2b$12$demo", "rep", 1, (base + timedelta(days=20)).isoformat()),
        ("sun_qi", "$2b$12$demo", "rep", 1, (base + timedelta(days=25)).isoformat()),
        ("manager_liu", "$2b$12$demo", "manager", 1, (base - timedelta(days=90)).isoformat()),
    ]
    for u in users_data:
        cur.execute("INSERT INTO users (username, hashed_password, role, is_active, created_at) VALUES (?, ?, ?, ?, ?)", u)
    cur.execute("SELECT id, username FROM users")
    user_map = {r[1]: r[0] for r in cur.fetchall()}
    zhang_id = user_map["zhang_san"]
    li_id = user_map["li_si"]
    wang_id = user_map["wang_wu"]
    liu_mgr_id = user_map["manager_liu"]
    print("  用户: 7")

    # --- 1.2 HCP ---
    cur.execute("DELETE FROM hcp_profiles")
    hcp_data = [
        ("张教授", "主任医师", "协和医院", "心内科", "心血管,高血压", "北京", "A", "{}", 5000, 0.85, 0.7, 1, 2),
        ("李教授", "教授", "北大医学部", "肿瘤科", "免疫治疗,PD-1", "北京", "A", "{}", 3000, 0.9, 0.6, 1, 4),
        ("王主任", "主任医师", "上海中山医院", "心外科", "搭桥手术,瓣膜", "上海", "A", "{}", 4000, 0.8, 0.5, 1, 3),
    ]
    for h in hcp_data:
        cur.execute(
            "INSERT INTO hcp_profiles (name, title, hospital, department, specialty, city, tier, traits, prescription_volume, influence_score, digital_engagement, is_active, created_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            h,
        )
    cur.execute("SELECT id FROM hcp_profiles")
    hcp_ids = [r[0] for r in cur.fetchall()]
    print(f"  HCP: {len(hcp_data)}")

    # --- 1.3 拜访记录 ---
    cur.execute("DELETE FROM hcp_interactions")
    visits = [
        (
            hcp_ids[0],
            "初访",
            "首次拜访张教授，介绍公司新产品线。张教授对降压药A表示兴趣。",
            "张教授表示愿意试用",
            "positive",
            "",
            zhang_id,
            (base + timedelta(days=5)).isoformat(),
        ),
        (
            hcp_ids[0],
            "常规拜访",
            "提交产品资料，合规检查发现资料未备案，拦截后修改重提。",
            "资料已修正",
            "neutral",
            "",
            zhang_id,
            (base + timedelta(days=12)).isoformat(),
        ),
        (
            hcp_ids[0],
            "学术拜访",
            "邀请张教授参加下月学术会议，提交会议申请。",
            "张教授同意参加",
            "positive",
            "",
            zhang_id,
            (base + timedelta(days=25)).isoformat(),
        ),
        (hcp_ids[2], "术前沟通", "确认明日搭桥手术方案，检查器械清单。", "器械齐全", "positive", "", li_id, (base + timedelta(days=28)).isoformat()),
        (
            hcp_ids[1],
            "科研拜访",
            "介绍新型PD-1检测试剂，李教授表示愿意试用。",
            "愿意试用",
            "positive",
            "",
            wang_id,
            (base + timedelta(days=20)).isoformat(),
        ),
        (
            hcp_ids[0],
            "回访",
            "确认张教授对降压药A的试用反馈，效果好，建议正式采购。",
            "效果良好",
            "positive",
            "",
            zhang_id,
            (base + timedelta(days=35)).isoformat(),
        ),
    ]
    for v in visits:
        cur.execute(
            "INSERT INTO hcp_interactions (hcp_id, interaction_type, content, response, outcome, strategy_used, conducted_by, conducted_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            v,
        )
    print(f"  拜访: {len(visits)}")

    # --- 1.4 内容/合规记录 ---
    cur.execute("DELETE FROM contents")
    contents_data = []
    # 张三提交的合规内容
    contents_data.append(
        ("降压药A产品资料", "降压药A最新临床研究数据及产品说明", "产品介绍", 1.0, "active", (base + timedelta(days=5)).isoformat(), zhang_id)
    )
    contents_data.append(("降压药A备案文件", "产品备案证明文件扫描件", "合规文件", 0.45, "active", (base + timedelta(days=12)).isoformat(), zhang_id))
    contents_data.append(("降压药A备案文件-修正版", "修正后的备案文件", "合规文件", 1.0, "active", (base + timedelta(days=12)).isoformat(), zhang_id))
    contents_data.append(
        (
            "学术会议申请-6月北京心血管论坛",
            "张教授参会申请，预算¥8,000",
            "会议纪要",
            0.55,
            "active",
            (base + timedelta(days=25)).isoformat(),
            zhang_id,
        )
    )
    contents_data.append(
        ("学术会议申请-修正版", "修改后的会议申请，预算¥5,000", "会议纪要", 1.0, "active", (base + timedelta(days=26)).isoformat(), zhang_id)
    )
    contents_data.append(
        ("降压药A拜访报告-4月", "4月拜访张教授的完整报告", "拜访报告", 1.0, "active", (base + timedelta(days=6)).isoformat(), zhang_id)
    )
    # 王五的科研内容
    contents_data.append(
        ("PD-1检测试剂产品说明书", "新型PD-1检测试剂技术参数", "产品介绍", 1.0, "active", (base + timedelta(days=18)).isoformat(), wang_id)
    )
    contents_data.append(
        ("李教授PI画像报告", "李教授学术背景及研究方向分析", "拜访报告", 1.0, "active", (base + timedelta(days=19)).isoformat(), wang_id)
    )
    # 更多随机内容（填充数字）
    for i in range(30):
        d = random.randint(0, 35)
        cat = random.choice(["拜访报告", "学术材料", "产品介绍", "会议纪要"])
        score = 1.0 if random.random() > 0.12 else round(random.uniform(0.3, 0.68), 2)
        contents_data.append(
            (
                f"内容-{i + 10}",
                f"这是内容{i + 10}的正文",
                cat,
                score,
                "active" if random.random() > 0.15 else "archived",
                (base + timedelta(days=d)).isoformat(),
                random.randint(2, 7),
            )
        )
    for c in contents_data:
        cur.execute("INSERT INTO contents (title, body, category, compliance_score, status, created_at, created_by) VALUES (?, ?, ?, ?, ?, ?, ?)", c)
    total_contents = len(contents_data)
    passed = sum(1 for c in contents_data if c[3] >= 1.0)
    print(f"  内容: {total_contents}条 (通过{passed}/{total_contents})")

    # --- 1.5 审计日志 ---
    cur.execute("DELETE FROM audit_logs")
    audit_events = [
        (zhang_id, "create", "content", 1, "上传产品资料", (base + timedelta(days=5)).isoformat()),
        (zhang_id, "compliance_check", "content", 2, "备案文件未通过合规检查", (base + timedelta(days=12)).isoformat()),
        (zhang_id, "update", "content", 3, "修正备案文件后重新提交", (base + timedelta(days=12)).isoformat()),
        (zhang_id, "compliance_check", "content", 4, "会议费用超标警告", (base + timedelta(days=25)).isoformat()),
        (liu_mgr_id, "view", "compliance", 1, "查看团队合规记录", (base + timedelta(days=25)).isoformat()),
        (zhang_id, "update", "content", 5, "修改会议预算后重新提交", (base + timedelta(days=26)).isoformat()),
        (wang_id, "create", "content", 7, "上传PD-1检测试剂资料", (base + timedelta(days=18)).isoformat()),
        (wang_id, "view", "report", 1, "查看李教授PI画像", (base + timedelta(days=19)).isoformat()),
        (li_id, "create", "content", 6, "提交手术准备清单", (base + timedelta(days=28)).isoformat()),
        (zhang_id, "create", "content", 6, "提交回访报告", (base + timedelta(days=35)).isoformat()),
    ]
    for a in audit_events:
        # a = (user_id, action, entity_type, entity_id, detail, created_at)
        cur.execute(
            "INSERT INTO audit_logs (user_id, action, entity_type, entity_id, detail, source_end, ip_address, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (a[0], a[1], a[2], a[3], a[4], "mobile_app", "192.168.1.100", a[5]),
        )
    print(f"  审计日志: {len(audit_events)}")

    conn.commit()
    conn.close()
    return user_map, hcp_ids


# ============================================================
# PART 2: Research DB — PI / 产品 / 报价
# ============================================================


def seed_research():
    db_path = os.path.join(BASE, "data", "research.db")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    base = datetime(2026, 4, 15)

    # PI
    cur.execute("DELETE FROM research_pi_profiles")
    pis = [
        ("李教授", 0, "北大医学部", "肿瘤科", "教授", "免疫治疗,PD-1,肿瘤微环境", 45, 12, 32, (base + timedelta(days=15)).isoformat()),
        ("陈教授", 0, "复旦医学院", "免疫学", "教授", "CAR-T,细胞治疗,肿瘤免疫", 38, 8, 28, (base + timedelta(days=10)).isoformat()),
        ("刘教授", 0, "中科院上海生命科学院", "分子生物学", "研究员", "基因编辑,CRISPR,靶向治疗", 52, 15, 42, (base + timedelta(days=5)).isoformat()),
    ]
    for p in pis:
        cur.execute(
            "INSERT INTO research_pi_profiles (name, hcp_id, institution, department, title, research_areas, total_papers, total_grants, h_index, last_updated) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            p,
        )
    cur.execute("SELECT pi_id, name FROM research_pi_profiles")
    pi_map = {r[1]: r[0] for r in cur.fetchall()}
    print(f"  PI: {len(pis)}")

    # 产品
    cur.execute("DELETE FROM research_products")
    products = [
        (
            "PD-1检测试剂盒",
            "试剂",
            "BioTech",
            "PD-1-ELISA",
            "96孔板",
            3800.0,
            "PD-1,免疫检查点,ELISA",
            '{"灵敏度":"0.1ng/mL","特异性":">99%"}',
            "有效",
        ),
        ("Anti-PD-1抗体", "试剂", "BioTech", "aPD-1-100", "100μg", 2600.0, "PD-1,抗体,免疫组化", '{"克隆":"兔单抗","应用":"WB/IHC"}', "有效"),
        ("细胞培养基RPMI-1640", "试剂", "Gibco", "RPMI-1640", "500mL", 180.0, "细胞培养,培养基", '{"内毒素":"<0.1EU/mL"}', "有效"),
        ("重组人IL-2", "试剂", "PeproTech", "rhIL-2", "10μg", 950.0, "细胞因子,IL-2,T细胞", '{"纯度":">98%","活性":">5×10⁶U/mg"}', "有效"),
    ]
    for p in products:
        cur.execute(
            "INSERT INTO research_products (name, category, brand, model, spec, unit_price, keywords, tech_params, cert_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            p,
        )
    print(f"  产品: {len(products)}")

    # 报价
    cur.execute("DELETE FROM research_quotations")
    quotes = [
        (
            "QT-PD1-001",
            "PD-1检测试剂采购报价",
            "李教授",
            '[{"name":"PD-1检测试剂盒","qty":2,"price":3800},{"name":"Anti-PD-1抗体","qty":1,"price":2600}]',
            10200.0,
            "pending",
            "王五",
            (base + timedelta(days=22)).isoformat(),
        ),
        (
            "QT-CAR-002",
            "细胞培养试剂报价",
            "陈教授",
            '[{"name":"细胞培养基RPMI-1640","qty":10,"price":180},{"name":"重组人IL-2","qty":5,"price":950}]',
            6550.0,
            "approved",
            "王五",
            (base + timedelta(days=25)).isoformat(),
        ),
    ]
    for q in quotes:
        cur.execute(
            "INSERT INTO research_quotations (template_id, title, customer_name, items_json, total_amount, status, created_by, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            q,
        )
    print(f"  报价: {len(quotes)}")

    conn.commit()
    conn.close()


# ============================================================
# PART 3: Assistant DB — 手术 / 拜访 (Flutter同步用)
# ============================================================


def seed_assistant():
    db_path = os.path.join(BASE, "data", "assistant.db")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    base = datetime(2026, 4, 15)

    # Check if tables exist, create if not
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing = {r[0] for r in cur.fetchall()}

    if "hcp_profiles" not in existing:
        cur.execute("CREATE TABLE hcp_profiles (id INTEGER PRIMARY KEY, name TEXT, hospital TEXT, department TEXT, title TEXT, phone TEXT)")
    if "visits" not in existing:
        cur.execute(
            "CREATE TABLE visits (id INTEGER PRIMARY KEY, hcp_name TEXT, hospital TEXT, visit_date TEXT, visit_type TEXT, status TEXT, notes TEXT)"
        )
    if "surgeries" not in existing:
        cur.execute(
            "CREATE TABLE surgeries (id INTEGER PRIMARY KEY, patient_name TEXT, hospital TEXT, surgery_type TEXT, scheduled_date TEXT, status TEXT, notes TEXT, doctor TEXT)"
        )

    cur.execute("DELETE FROM hcp_profiles")
    cur.execute("DELETE FROM visits")
    cur.execute("DELETE FROM surgeries")

    # HCP
    hcp = [
        ("张教授", "协和医院", "心内科", "主任医师", "13800138001"),
        ("李教授", "北大医学部", "肿瘤科", "教授", "13800138002"),
        ("王主任", "上海中山医院", "心外科", "主任医师", "13800138003"),
        ("赵医生", "北京人民医院", "神经内科", "副主任医师", "13800138004"),
    ]
    for h in hcp:
        cur.execute("INSERT INTO hcp_profiles (name, hospital, department, title, phone) VALUES (?, ?, ?, ?, ?)", h)
    print(f"  HCP: {len(hcp)}")

    # Visits
    visits = [
        ("张教授", "协和医院", (base + timedelta(days=5)).isoformat()[:10], "初访", "completed", "首次拜访，介绍降压药A"),
        ("张教授", "协和医院", (base + timedelta(days=12)).isoformat()[:10], "常规拜访", "completed", "提交产品资料，合规拦截后修改"),
        ("张教授", "协和医院", (base + timedelta(days=25)).isoformat()[:10], "学术拜访", "completed", "邀请参加学术会议"),
        ("王主任", "上海中山医院", (base + timedelta(days=28)).isoformat()[:10], "术前沟通", "completed", "确认手术方案"),
        ("李教授", "北大医学部", (base + timedelta(days=20)).isoformat()[:10], "科研拜访", "completed", "推荐PD-1检测试剂"),
        ("张教授", "协和医院", (base + timedelta(days=35)).isoformat()[:10], "回访", "completed", "确认用药反馈"),
        ("赵医生", "北京人民医院", (base + timedelta(days=30)).isoformat()[:10], "初访", "scheduled", "计划拜访"),
    ]
    for v in visits:
        cur.execute("INSERT INTO visits (hcp_name, hospital, visit_date, visit_type, status, notes) VALUES (?, ?, ?, ?, ?, ?)", v)
    print(f"  拜访: {len(visits)}")

    # Surgeries
    surgeries = [
        ("王建国", "协和医院", "冠状动脉搭桥术", (base + timedelta(days=28)).isoformat()[:10], "completed", "术前备货完成，手术顺利", "王主任"),
        ("李明", "上海中山医院", "心脏瓣膜置换术", (base + timedelta(days=32)).isoformat()[:10], "scheduled", "术前准备中", "王主任"),
        ("张伟", "北京人民医院", "PCI介入手术", (base + timedelta(days=35)).isoformat()[:10], "pre_op", "器械已清点", "赵医生"),
    ]
    for s in surgeries:
        cur.execute(
            "INSERT INTO surgeries (patient_name, hospital, surgery_type, scheduled_date, status, notes, doctor) VALUES (?, ?, ?, ?, ?, ?, ?)", s
        )
    print(f"  手术: {len(surgeries)}")

    conn.commit()
    conn.close()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("=== 灌入演示数据 ===")
    print("[Cloud]")
    seed_cloud()
    print("[Research]")
    seed_research()
    print("[Assistant]")
    seed_assistant()
    print("\n✅ 全部完成！")
    print("\n故事线可演示场景：")
    print("  1. 张三拜访张教授 → 合规拦截 → 修正通过 → 管理端可见")
    print("  2. 王五挖掘PI线索 → 推荐产品 → 生成报价单")
    print("  3. 李四跟台手术 → 术前扫码 → 术后报告")
    print("  4. 刘经理看板 → 团队KPI → 违规记录 → 排行")
