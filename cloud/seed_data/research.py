import json
import sqlite3


def seed_research_pis(conn: sqlite3.Connection) -> None:
    names = ["陈院士", "张教授", "李研究员", "王教授", "刘研究员", "赵教授", "孙研究员", "周教授", "吴研究员", "郑教授"]
    existing = {
        row["name"]
        for row in conn.execute(
            "SELECT name FROM research_pi_profiles WHERE name IN ({})".format(",".join("?" for _ in names)),
            names,
        ).fetchall()
    }
    pis = [
        ("陈院士", "中科院上海生命科学院", "分子生物学", 380, 42, 68),
        ("张教授", "北京大学医学部", "肿瘤免疫", 215, 28, 52),
        ("李研究员", "清华大学生命学院", "基因编辑", 178, 35, 47),
        ("王教授", "复旦大学医学院", "神经科学", 156, 22, 44),
        ("刘研究员", "浙江大学医学院", "干细胞研究", 134, 18, 38),
        ("赵教授", "上海交通大学医学院", "心血管疾病", 112, 15, 35),
        ("孙研究员", "中山大学医学院", "代谢疾病", 98, 12, 30),
        ("周教授", "华中科技大学同济医学院", "感染与免疫", 87, 10, 28),
        ("吴研究员", "四川大学华西医学中心", "再生医学", 72, 8, 24),
        ("郑教授", "天津医科大学", "肿瘤药理", 65, 6, 22),
    ]
    for pi in pis:
        if pi[0] in existing:
            continue
        conn.execute(
            "INSERT INTO research_pi_profiles (name, institution, research_areas, total_papers, total_grants, h_index) VALUES (?, ?, ?, ?, ?, ?)",
            (pi[0], pi[1], json.dumps([pi[2]], ensure_ascii=False), pi[3], pi[4], pi[5]),
        )
    conn.commit()


def seed_research_products(conn: sqlite3.Connection) -> None:
    names = [
        "Q5 热启动超保真DNA聚合酶",
        "RNeasy 迷你纯化试剂盒",
        "DMEM 高糖培养基",
        "胎牛血清 FBS",
        "PVDF 转印膜 0.45μm",
        "75cm² 细胞培养瓶",
        "15mL 锥形离心管",
        "2mL 冻存管",
        "兔抗人GAPDH 抗体",
        "BCA 蛋白定量试剂盒",
        "TRIzol 总RNA提取试剂",
        "SYBR Green qPCR 预混液",
        "琼脂糖 标准级",
        "DAPI 封片剂",
        "Protease Inhibitor Cocktail",
        "CO₂ 培养箱",
        "生物安全柜 Class II",
        "微量离心机",
        "Nanodrop 分光光度计",
        "-80℃ 超低温冰箱",
    ]
    existing = {
        row["name"]
        for row in conn.execute(
            "SELECT name FROM research_products WHERE name IN ({})".format(",".join("?" for _ in names)),
            names,
        ).fetchall()
    }
    products = [
        ("Q5 热启动超保真DNA聚合酶", "分子试剂", "NEB", "M0493S", "200U", 1280.0, "['PCR', '高保真', '热启动']"),
        ("RNeasy 迷你纯化试剂盒", "纯化试剂盒", "Qiagen", "74104", "50次", 3680.0, "['RNA', '纯化', '提取']"),
        ("DMEM 高糖培养基", "细胞培养试剂", "Gibco", "11965092", "500ml", 420.0, "['细胞培养', '培养基']"),
        ("胎牛血清 FBS", "细胞培养试剂", "Gibco", "10099141", "500ml", 7200.0, "['血清', 'FBS', '细胞']"),
        ("PVDF 转印膜 0.45μm", "耗材", "Millipore", "IPVH00010", "26.5cm*3.75m", 1580.0, "['WB', '转印', '膜']"),
        ("75cm² 细胞培养瓶", "耗材", "Corning", "430720", "20个/包", 380.0, "['细胞培养', '培养瓶']"),
        ("15mL 锥形离心管", "耗材", "Corning", "430791", "50个/包", 220.0, "['离心管', '耗材']"),
        ("2mL 冻存管", "耗材", "Thermo", "377267", "500个/包", 650.0, "['冻存', '管']"),
        ("兔抗人GAPDH 抗体", "抗体", "CST", "5174S", "100μl", 3200.0, "['抗体', 'GAPDH', '内参']"),
        ("BCA 蛋白定量试剂盒", "分子试剂", "Thermo", "23225", "500次", 2450.0, "['蛋白定量', 'BCA']"),
        ("TRIzol 总RNA提取试剂", "分子试剂", "Invitrogen", "15596026", "100ml", 1800.0, "['RNA提取', 'TRIzol']"),
        ("SYBR Green qPCR 预混液", "分子试剂", "Roche", "4887352001", "5ml", 2100.0, "['qPCR', 'SYBR']"),
        ("琼脂糖 标准级", "分子试剂", "Biowest", "BY-R0100", "100g", 320.0, "['琼脂糖', '凝胶']"),
        ("DAPI 封片剂", "染色试剂", "Vector", "H-1200", "10ml", 980.0, "['DAPI', '封片', '荧光']"),
        ("Protease Inhibitor Cocktail", "抑制剂", "Roche", "11873580001", "1片/30ml", 1520.0, "['蛋白酶抑制剂', 'PIC']"),
        ("CO₂ 培养箱", "仪器", "Thermo", "371", "165L", 98500.0, "['培养箱', 'CO2', '细胞']"),
        ("生物安全柜 Class II", "仪器", "ESCO", "AC2-4S1", "4英尺", 62000.0, "['安全柜', '生物']"),
        ("微量离心机", "仪器", "Eppendorf", "5424R", "冷冻型", 38000.0, "['离心机', '微量']"),
        ("Nanodrop 分光光度计", "仪器", "Thermo", "ND-2000c", "全光谱", 72000.0, "['分光光度计', '核酸定量']"),
        ("-80℃ 超低温冰箱", "仪器", "Thermo", "907", "立式", 55000.0, "['冰箱', '超低温']"),
    ]
    for p in products:
        if p[0] in existing:
            continue
        conn.execute(
            "INSERT INTO research_products (name, category, brand, model, spec, unit_price, keywords) VALUES (?, ?, ?, ?, ?, ?, ?)",
            p,
        )
    conn.commit()


def seed_research_visits(conn: sqlite3.Connection, cloud_conn: sqlite3.Connection) -> None:
    if conn.execute("SELECT COUNT(*) FROM research_visits").fetchone()[0] > 0:
        return
    pi_ids = [row["pi_id"] for row in conn.execute("SELECT pi_id FROM research_pi_profiles ORDER BY pi_id ASC LIMIT 5").fetchall()]
    rep_ids = [row["id"] for row in cloud_conn.execute("SELECT id FROM users WHERE role = 'researcher' LIMIT 2").fetchall()]
    if not pi_ids or not rep_ids:
        return
    visits = [
        (pi_ids[0], rep_ids[0], "2026-05-10", "讨论单细胞测序平台合作，确认设备采购意向", "completed"),
        (pi_ids[1], rep_ids[0], "2026-05-12", "提交最新靶向药物研究进度，申请科研基金支持", "completed"),
        (pi_ids[2], rep_ids[1], "2026-05-15", "演示新型基因编辑检测试剂盒，获取使用反馈", "completed"),
        (pi_ids[3], rep_ids[1], "2026-05-18", "跟进神经退行性疾病的生物标志物合作项目", "planned"),
        (pi_ids[0], rep_ids[0], "2026-05-20", "安排肿瘤免疫研究联合实验室挂牌仪式", "planned"),
    ]
    for v in visits:
        conn.execute(
            "INSERT INTO research_visits (pi_id, rep_id, visit_date, notes, status) VALUES (?, ?, ?, ?, ?)",
            v,
        )
    conn.commit()
