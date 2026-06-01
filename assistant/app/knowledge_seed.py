import sqlite3
from datetime import datetime, timezone

from assistant.app.database import DB_PATH

SEED_DATA = [
    {"title": "ACEI类降压药", "category": "药品知识", "content": "ACEI（血管紧张素转化酶抑制剂）通过抑制RAAS系统降低血压，代表药物：卡托普利、依那普利、雷米普利。适用于高血压、心力衰竭、糖尿病肾病。", "tags": "降压药,ACEI,RAAS", "difficulty": "medium"},
    {"title": "ARB类降压药", "category": "药品知识", "content": "ARB（血管紧张素II受体拮抗剂）通过阻断AT1受体发挥降压作用，代表药物：氯沙坦、缬沙坦、厄贝沙坦。副作用较ACEI少，尤其咳嗽发生率低。", "tags": "降压药,ARB,RAAS", "difficulty": "medium"},
    {"title": "他汀类药物", "category": "药品知识", "content": "他汀类（HMG-CoA还原酶抑制剂）降低LDL-C，稳定斑块。代表药物：阿托伐他汀、瑞舒伐他汀、辛伐他汀。主要不良反应为肝酶升高和肌痛。", "tags": "降脂药,他汀,LDL-C", "difficulty": "medium"},
    {"title": "PPI质子泵抑制剂", "category": "药品知识", "content": "PPI通过抑制胃壁细胞H+/K+-ATP酶，强效抑制胃酸分泌。代表药物：奥美拉唑、兰索拉唑、泮托拉唑、埃索美拉唑。长期使用需注意骨质疏松和感染风险。", "tags": "抑酸药,PPI,胃病", "difficulty": "easy"},
    {"title": "术前准备规范", "category": "手术规范", "content": "术前准备包括：①完善术前检查（血常规、凝血功能、心电图等）；②评估手术风险（ASA分级）；③术前禁食8小时、禁水4小时；④预防性抗生素使用；⑤签署知情同意书。", "tags": "术前准备,手术规范,ASA", "difficulty": "medium"},
    {"title": "无菌操作原则", "category": "手术规范", "content": "无菌操作核心原则：①所有接触手术区域的物品必须灭菌；②手术人员需严格刷手、穿无菌衣、戴无菌手套；③手术区铺巾至少两层；④保持无菌屏障完整；⑤减少手术间人员流动。", "tags": "无菌,感染控制,手术规范", "difficulty": "hard"},
    {"title": "吻合器使用指南", "category": "器械使用", "content": "吻合器用于消化道重建和血管吻合。使用要点：①根据组织厚度选择合适钉仓；②击发前确认组织对合良好；③击发后检查切割线和出血点；④常见品牌有强生ECHELON和美敦力SIGNIA。", "tags": "吻合器,器械,消化道", "difficulty": "hard"},
    {"title": "超声刀操作要点", "category": "器械使用", "content": "超声刀通过机械振动产生热量，同时切割和凝血。使用要点：①选择合适的功率档位；②抓持组织后等待刀头充分激活；③避免长时间连续激发；④定期清洁刀头；⑤注意防烫伤。", "tags": "超声刀,器械,腔镜", "difficulty": "hard"},
    {"title": "腹腔镜胆囊切除术", "category": "手术规范", "content": "LC术标准流程：①建立气腹（压力12-14mmHg）；②四孔法置入trocar；③辨认Calot三角；④夹闭并切断胆囊动脉和胆囊管；⑤顺行或逆行剥离胆囊；⑥标本袋取出胆囊。", "tags": "腹腔镜,胆囊切除,LC", "difficulty": "hard"},
    {"title": "围手术期抗生素使用", "category": "药品知识", "content": "预防性抗生素使用原则：①I类切口一般不需使用；②II类切口术前30-60分钟单次给药；③III类切口治疗性使用；④选择覆盖最常见病原菌的药物，如头孢唑林、头孢呋辛。", "tags": "抗生素,围手术期,预防感染", "difficulty": "medium"},
]


def seed_knowledge() -> None:
    conn = sqlite3.connect(DB_PATH)
    try:
        count = conn.execute("SELECT COUNT(*) FROM knowledge_base").fetchone()[0]
        if count > 0:
            return
        now = datetime.now(timezone.utc).isoformat()
        for item in SEED_DATA:
            conn.execute(
                """INSERT INTO knowledge_base (title, category, content, tags, difficulty, created_by, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, 1, ?, ?)""",
                (item["title"], item["category"], item["content"], item["tags"], item["difficulty"], now, now),
            )
        conn.commit()
    finally:
        conn.close()
