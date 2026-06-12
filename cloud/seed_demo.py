"""
一云四端 · 种子数据脚本

创建演示数据，覆盖通用拜访、科研模式和跟台助手三大场景。
直接通过数据库连接写入，不走 HTTP API。
幂等设计：重复运行不报错、不产生重复数据。
"""

import json
import logging
import os
import sqlite3
from pathlib import Path

from shared.auth import hash_password

logger = logging.getLogger(__name__)

_root = str(Path(__file__).resolve().parent.parent)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CLOUD_DB = os.path.join(BASE_DIR, "data", "cloud.db")
RESEARCH_DB = os.path.join(BASE_DIR, "data", "research.db")
ASSISTANT_DB = os.path.join(BASE_DIR, "data", "assistant.db")


# ========== 通用数据 ==========


def _get_conn(db_path: str) -> sqlite3.Connection:
    """获取数据库连接（自动创建目录并启用 WAL）。"""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def seed_users(conn: sqlite3.Connection) -> None:
    """创建通用用户：3 个拜访模式用户 + 2 个科研用户 + 2 个器械用户。"""
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


def seed_hcps(conn: sqlite3.Connection) -> None:
    """创建 20 条 HCP 档案。"""
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


def _visit_data(hcp_ids):
    """生成 10 条拜访记录元组列表。"""
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


def seed_visits(conn: sqlite3.Connection) -> None:
    """创建 10 条拜访记录。"""
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
    """创建 5 个普通药品。"""
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


# ========== 科研模式 ==========


def seed_research_pis(conn: sqlite3.Connection) -> None:
    """创建 10 条 PI 档案（科研模式）。"""
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
    """创建 20 个科研产品（试剂/耗材/仪器）。"""
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
    """创建 5 条科研拜访记录。"""
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


# ========== 跟台助手 ==========


def seed_surgery_reminders(conn: sqlite3.Connection) -> None:
    """创建 10 场手术预约（跟台助手）。"""
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
    """创建 5 个高值耗材/器械产品（写入 cloud.db products 表）。"""
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


def main() -> None:
    """主入口：依次写入通用、科研和跟台助手演示数据。"""
    logger.info("→ 通用数据 ...")
    conn = _get_conn(CLOUD_DB)
    try:
        seed_users(conn)
        seed_hcps(conn)
        seed_visits(conn)
        seed_products(conn)
        seed_device_products(conn)
    finally:
        conn.close()

    logger.info("→ 科研模式数据 ...")
    conn = _get_conn(RESEARCH_DB)
    cloud_conn = _get_conn(CLOUD_DB)
    try:
        seed_research_pis(conn)
        seed_research_products(conn)
        seed_research_visits(conn, cloud_conn)
    finally:
        conn.close()
        cloud_conn.close()

    logger.info("→ 跟台助手数据 ...")
    conn = _get_conn(ASSISTANT_DB)
    try:
        seed_surgery_reminders(conn)
    finally:
        conn.close()

    logger.info("种子数据写入完成。")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
