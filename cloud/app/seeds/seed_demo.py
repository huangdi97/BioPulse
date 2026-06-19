"""Demo 种子数据：3 个代表用户 + 5 个 HCP + 10 条拜访记录 + 3 条合规案例。

Usage:
    python -m cloud.app.seeds.seed_demo          # 填充数据
    python -m cloud.app.seeds.seed_demo --reset  # 清空后重建
"""

import argparse
import sqlite3
from datetime import datetime, timedelta

DB_PATH = "data/cloud.db"


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def seed_demo(conn: sqlite3.Connection | None = None, reset: bool = False) -> None:
    own_conn = conn is None
    if own_conn:
        conn = _get_conn()
    try:
        if reset:
            for tbl in ("visit_records", "compliance_cases", "hcp_profiles"):
                conn.execute(f"DELETE FROM {tbl}")
            conn.execute("DELETE FROM users WHERE email LIKE 'rep%@demo.com'")
            conn.commit()

        existing = conn.execute("SELECT COUNT(*) FROM users WHERE email LIKE 'rep%@demo.com'").fetchone()[0]
        if existing > 0 and not reset:
            return

        now = datetime.now()
        users = [
            ("张明", "rep_a@demo.com", "rep_a", "代表A-华东区"),
            ("李芳", "rep_b@demo.com", "rep_b", "代表B-华南区"),
            ("王强", "rep_c@demo.com", "rep_c", "代表C-华北区"),
        ]
        for name, email, username, title in users:
            conn.execute(
                "INSERT OR IGNORE INTO users (name, email, username, title, created_at) VALUES (?, ?, ?, ?, ?)",
                (name, email, username, title, now.isoformat()),
            )
        conn.commit()

        hcps = [
            ("赵主任", "三甲医院心内科", "主任医师", 4.8),
            ("钱医生", "市人民医院呼吸科", "副主任医师", 4.2),
            ("孙教授", "医科大学附属医院", "教授/主任医师", 4.9),
            ("李医师", "区中心医院骨科", "主治医师", 3.9),
            ("周博士", "专科医院肿瘤科", "副主任医师", 4.5),
        ]
        for name, hospital, title, score in hcps:
            conn.execute(
                "INSERT OR IGNORE INTO hcp_profiles (name, hospital, title, influence_score, created_at) VALUES (?, ?, ?, ?, ?)",
                (name, hospital, title, score, now.isoformat()),
            )
        conn.commit()

        hcp_rows = conn.execute("SELECT id, name FROM hcp_profiles").fetchall()
        user_rows = conn.execute("SELECT id, username FROM users WHERE email LIKE 'rep%@demo.com'").fetchall()

        visit_templates = [
            ("新产品介绍", "介绍公司新上市的心血管药物", "completed", True),
            ("学术拜访", "讨论最新临床研究数据", "completed", True),
            ("合规回访", "确认合规材料送达", "completed", True),
            ("季度回顾", "回顾季度合作情况", "completed", True),
            ("产品培训", "新产品使用培训", "completed", True),
            ("会议邀请", "邀请参加学术会议", "completed", True),
            ("样品派发", "派发药品样品", "completed", True),
            ("科室会", "科室学术会议", "scheduled", True),
            ("随访", "术后患者随访沟通", "scheduled", True),
            ("签约拜访", "年度合作签约", "cancelled", False),
        ]

        for i, (title, content, status, compliant) in enumerate(visit_templates):
            hcp = hcp_rows[i % len(hcp_rows)]
            user = user_rows[i % len(user_rows)]
            visit_time = now - timedelta(days=30 - i * 3)
            conn.execute(
                "INSERT INTO visit_records (user_id, hcp_id, title, content, status, is_compliant, visit_time, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (user["id"], hcp["id"], title, content, status, 1 if compliant else 0, visit_time.isoformat(), visit_time.isoformat()),
            )
        conn.commit()

        compliance_cases = [
            ("费用异常", f"代表 {user_rows[0]['username']} 报销金额超出月预算 150%", "high", "open"),
            ("拜访次数超限", f"{hcp_rows[1]['name']} 月拜访次数超过合规上限", "medium", "investigating"),
            ("利益冲突", f"代表 {user_rows[2]['username']} 与 {hcp_rows[2]['name']} 存在未申报亲属关系", "critical", "resolved"),
        ]
        for title, detail, severity, status in compliance_cases:
            conn.execute(
                "INSERT INTO compliance_cases (title, detail, severity, status, created_at) VALUES (?, ?, ?, ?, ?)",
                (title, detail, severity, status, now.isoformat()),
            )
        conn.commit()

        print(f"Demo 数据填充完成: {len(users)} 用户, {len(hcps)} HCP, {len(visit_templates)} 拜访记录, {len(compliance_cases)} 合规案例")
    finally:
        if own_conn:
            conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="填充 Demo 数据")
    parser.add_argument("--reset", action="store_true", help="清空后重建")
    args = parser.parse_args()
    seed_demo(reset=args.reset)
