import os
import sqlite3

from shared.auth import hash_password


def _get_conn(db_path: str) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def seed_users(conn: sqlite3.Connection) -> None:
    users = [
        ("admin", hash_password("password"), "admin"),
        ("rep_zhang", hash_password("password"), "rep"),
        ("rep_li", hash_password("password"), "rep"),
        ("sci_li", hash_password("password"), "researcher"),
        ("sci_wang", hash_password("password"), "researcher"),
        ("device_li", hash_password("password"), "device_rep"),
        ("device_wang", hash_password("password"), "device_rep"),
    ]
    existing = {
        row["username"]
        for row in conn.execute(
            "SELECT username FROM users WHERE username IN ({})".format(",".join("?" for _ in users)),
            [u[0] for u in users],
        ).fetchall()
    }
    for username, hashed, role in users:
        if username not in existing:
            conn.execute(
                "INSERT INTO users (username, hashed_password, role) VALUES (?, ?, ?)",
                (username, hashed, role),
            )
    conn.commit()


def _visit_data(hcp_ids):
    return [
        (hcp_ids[0], "张建国", "介绍新型抗凝药物，讨论临床研究合作", "学术拜访", "passed"),
        (hcp_ids[1], "李明华", "跟进产品试用反馈，解答不良反应疑问", "售后回访", "passed"),
        (hcp_ids[2], "王芳", "邀请参加全国肿瘤学术会议，递交资料", "会议邀请", "passed"),
        (hcp_ids[3], "刘伟", "新药信息传递，提供最新临床数据", "学术拜访", "flagged"),
        (hcp_ids[4], "陈静", "收集产品使用意见，安排科室会", "市场调研", "passed"),
        (hcp_ids[5], "赵强", "演示手术器械操作流程，培训使用", "产品演示", "passed"),
        (hcp_ids[6], "孙丽", "跟进学术资助申请进展，确认材料", "行政拜访", "passed"),
        (hcp_ids[7], "周涛", "定期拜访维护客情，赠送学术期刊", "客情维护", "passed"),
        (hcp_ids[8], "吴敏", "介绍儿童剂型产品优势，解答安全性问题", "学术拜访", "flagged"),
        (hcp_ids[9], "郑浩", "科室会：前列腺疾病诊疗方案更新", "科室会", "passed"),
    ]


def seed_hcps(conn: sqlite3.Connection) -> None:
    names = [
        "张建国",
        "李明华",
        "王芳",
        "刘伟",
        "陈静",
        "赵强",
        "孙丽",
        "周涛",
        "吴敏",
        "郑浩",
        "黄磊",
        "林芳",
        "郭强",
        "马丽",
        "高峰",
        "宋丹",
        "秦川",
        "韩冰",
        "杨帆",
        "何琳",
    ]
    existing = {
        row["name"]
        for row in conn.execute(
            "SELECT name FROM hcp_profiles WHERE name IN ({})".format(",".join("?" for _ in names)),
            names,
        ).fetchall()
    }
    hcps = [
        ("张建国", "主任医师", "北京协和医院", "心内科", "心血管", "A", 0.92),
        ("李明华", "副主任医师", "华西医院", "神经内科", "神经", "A", 0.88),
        ("王芳", "主治医师", "中山医院", "肿瘤科", "肿瘤", "B", 0.75),
        ("刘伟", "主任医师", "瑞金医院", "内分泌科", "内分泌", "A", 0.85),
        ("陈静", "副主任医师", "同济医院", "呼吸科", "呼吸", "B", 0.72),
        ("赵强", "主治医师", "华山医院", "骨科", "骨科", "B", 0.68),
        ("孙丽", "主任医师", "湘雅医院", "妇产科", "妇科", "A", 0.90),
        ("周涛", "副主任医师", "齐鲁医院", "消化科", "消化", "B", 0.71),
        ("吴敏", "主治医师", "省人民医院", "儿科", "儿科", "C", 0.55),
        ("郑浩", "主任医师", "南方医院", "泌尿外科", "泌尿", "A", 0.87),
        ("黄磊", "副主任医师", "仁济医院", "肾内科", "肾脏", "B", 0.69),
        ("林芳", "主治医师", "长海医院", "眼科", "眼科", "C", 0.58),
        ("郭强", "主任医师", "西京医院", "普外科", "普外", "A", 0.83),
        ("马丽", "副主任医师", "南京鼓楼医院", "风湿免疫", "风湿", "B", 0.74),
        ("高峰", "主治医师", "浙大一院", "血液科", "血液", "B", 0.65),
        ("宋丹", "主任医师", "盛京医院", "皮肤科", "皮肤", "B", 0.77),
        ("秦川", "副主任医师", "武汉同济", "感染科", "感染", "C", 0.60),
        ("韩冰", "主治医师", "中日友好医院", "康复科", "康复", "C", 0.52),
        ("杨帆", "主任医师", "上海六院", "耳鼻喉科", "耳鼻喉", "A", 0.86),
        ("何琳", "副主任医师", "深圳人民医院", "急诊科", "急诊", "B", 0.70),
    ]
    for hcp in hcps:
        if hcp[0] in existing:
            continue
        conn.execute(
            "INSERT INTO hcp_profiles (name, title, hospital, department, specialty, tier, influence_score) VALUES (?, ?, ?, ?, ?, ?, ?)",
            hcp,
        )
    conn.commit()


def seed_visits(conn: sqlite3.Connection) -> None:
    visit_contents = [v[2] for v in _visit_data(list(range(10)))]
    existing = {
        row["content"]
        for row in conn.execute(
            "SELECT content FROM visits WHERE content IN ({})".format(",".join("?" for _ in visit_contents)),
            visit_contents,
        ).fetchall()
    }
    hcp_ids = [row["id"] for row in conn.execute("SELECT id FROM hcp_profiles LIMIT 10").fetchall()]
    if not hcp_ids or len(hcp_ids) < 10:
        return
    for v in _visit_data(hcp_ids):
        if v[2] in existing:
            continue
        conn.execute(
            "INSERT INTO visits (hcp_id, hcp_name, content, visit_type, compliance_status, location) VALUES (?, ?, ?, ?, ?, '医院')",
            v,
        )
    conn.commit()


def seed_products(conn: sqlite3.Connection) -> None:
    names = ["阿托伐他汀钙片", "奥美拉唑肠溶片", "甘精胰岛素注射液", "注射用头孢哌酮钠舒巴坦钠", "盐酸二甲双胍片"]
    existing = {
        row["name"]
        for row in conn.execute(
            "SELECT name FROM products WHERE name IN ({})".format(",".join("?" for _ in names)),
            names,
        ).fetchall()
    }
    products = [
        ("阿托伐他汀钙片", "化药", "辉瑞", "立普妥", "20mg*7片", 55.0, "['降脂', '他汀', '心血管']"),
        ("奥美拉唑肠溶片", "化药", "阿斯利康", "洛赛克", "20mg*14片", 38.0, "['胃药', '质子泵抑制剂']"),
        ("甘精胰岛素注射液", "生物药", "赛诺菲", "来得时", "3ml:300U", 185.0, "['胰岛素', '糖尿病', '长效']"),
        ("注射用头孢哌酮钠舒巴坦钠", "抗生素", "辉瑞", "舒普深", "1.5g/瓶", 68.0, "['抗生素', '抗感染']"),
        ("盐酸二甲双胍片", "化药", "施贵宝", "格华止", "0.5g*20片", 25.0, "['降糖', '糖尿病', '双胍']"),
    ]
    for p in products:
        if p[0] in existing:
            continue
        conn.execute(
            "INSERT INTO products (name, category, brand, model, spec, unit_price, keywords) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (*p,),
        )
    conn.commit()
