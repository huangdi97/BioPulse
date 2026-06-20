import sqlite3


def seed_surgery_reminders(conn: sqlite3.Connection) -> None:
    patients = ["王建国", "李秀英", "赵强", "孙丽华", "周明", "吴芳", "郑伟", "黄丽", "马超", "林小红"]
    existing = {
        row["patient_name"]
        for row in conn.execute(
            "SELECT patient_name FROM surgery_reminder WHERE patient_name IN ({})".format(",".join("?" for _ in patients)),
            patients,
        ).fetchall()
    }
    surgeries = [
        ("王建国", "全膝关节置换术", "2026-06-15", "北京协和医院", "骨科", "张主任", "术前影像已确认，假体型号已备"),
        ("李秀英", "经皮冠状动脉介入治疗", "2026-06-16", "阜外医院", "心内科", "刘主任", "抗凝药物已停药，凝血功能正常"),
        ("赵强", "腹腔镜胆囊切除术", "2026-06-17", "华西医院", "普外科", "陈主任", "术前禁食12小时，已宣教"),
        ("孙丽华", "白内障超声乳化术", "2026-06-18", "中山眼科中心", "眼科", "林教授", "术前滴眼液已开具，人工晶体已选"),
        ("周明", "腰椎椎间融合术", "2026-06-19", "上海长征医院", "脊柱外科", "周主任", "术中导航已预约，椎间融合器备货"),
        ("吴芳", "子宫肌瘤剔除术", "2026-06-20", "湘雅医院", "妇产科", "王主任", "术前MRI已完成，肌瘤位置确认"),
        ("郑伟", "经尿道前列腺电切术", "2026-06-22", "长海医院", "泌尿外科", "李主任", "术前尿培养阴性，抗生素预防"),
        ("黄丽", "甲状腺次全切除术", "2026-06-23", "仁济医院", "甲乳外科", "赵主任", "甲状腺功能已复查，喉返神经监测仪备用"),
        ("马超", "髋关节置换术", "2026-06-25", "南京鼓楼医院", "关节外科", "孙主任", "生物型假体已到货，骨水泥备用"),
        ("林小红", "乳腺癌保乳术", "2026-06-26", "复旦肿瘤医院", "乳腺外科", "吴主任", "前哨淋巴结示踪剂已备，冰冻病理待命"),
    ]
    for s in surgeries:
        if s[0] in existing:
            continue
        conn.execute(
            "INSERT INTO surgery_reminder (patient_name, surgery_type, surgery_date, hospital, department, surgeon_name, pre_op_notes, status) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, 'scheduled')",
            s,
        )
    conn.commit()


def seed_device_products(conn: sqlite3.Connection) -> None:
    names = ["冠状动脉药物涂层支架", "人工髋关节假体", "可吸收螺钉", "胸腔镜手术器械套装", "超声切割止血刀"]
    existing = {
        row["name"]
        for row in conn.execute(
            "SELECT name FROM products WHERE name IN ({})".format(",".join("?" for _ in names)),
            names,
        ).fetchall()
    }
    products = [
        ("冠状动脉药物涂层支架", "高值耗材", "微创医疗", "Firebird2", "3.5x23mm", 12800.0, "['支架', '冠脉', '介入']"),
        ("人工髋关节假体", "高值耗材", "春立医疗", "CL-1801", "52mm/中号", 28500.0, "['关节', '髋', '假体']"),
        ("可吸收螺钉", "高值耗材", "大博医疗", "ABS-4015", "4.0x15mm", 3600.0, "['螺钉', '可吸收', '骨科']"),
        ("胸腔镜手术器械套装", "器械", "强生", "ENDO-201", "5件/套", 45000.0, "['胸腔镜', '微创', '器械']"),
        ("超声切割止血刀", "器械", "强生", "GEN11", "主机+手柄", 68000.0, "['超声刀', '止血', '切割']"),
    ]
    for p in products:
        if p[0] in existing:
            continue
        conn.execute(
            "INSERT INTO products (name, category, brand, model, spec, unit_price, keywords) VALUES (?, ?, ?, ?, ?, ?, ?)",
            p,
        )
    conn.commit()
