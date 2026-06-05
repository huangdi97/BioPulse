"""一云四端演示数据种子脚本
用法: python seed_demo_data.py
运行前确保 Cloud:8000 在运行（或至少 database.py 可导入）
"""

import os
import random
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "cloud.db")


def seed():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # === Users ===
    existing = cur.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if existing <= 1:
        users = [
            ("zhang_san", "rep", 1, "2026-04-15"),
            ("li_si", "rep", 1, "2026-04-20"),
            ("wang_wu", "rep", 1, "2026-05-01"),
            ("zhao_liu", "rep", 1, "2026-05-10"),
            ("sun_qi", "rep", 1, "2026-03-01"),
            ("manager_liu", "manager", 1, "2026-01-15"),
        ]
        for u in users:
            cur.execute(
                "INSERT INTO users (username, hashed_password, role, is_active, created_at) VALUES (?, ?, ?, ?, ?)",
                (u[0], "$2b$12$demo", u[1], u[2], u[3]),
            )
        print(f"✅ Added {len(users)} users")
    else:
        print(f"users: {existing} rows (skip)")

    # === Contents ===
    existing = cur.execute("SELECT COUNT(*) FROM contents").fetchone()[0]
    if existing == 0:
        categories = ["拜访报告", "学术材料", "产品介绍", "会议纪要"]
        batch = []
        for i in range(40):
            score = round(random.uniform(0.75, 1.0), 2)
            if random.random() < 0.12:
                score = round(random.uniform(0.3, 0.65), 2)
            month = 4 + random.randint(0, 2)
            day = random.randint(1, 28)
            batch.append(
                (
                    f"内容-{i + 1}",
                    f"这是第{i + 1}条演示演示内容的正文，包含合规检查所需的完整信息。",
                    random.choice(categories),
                    score,
                    "active" if random.random() > 0.15 else "archived",
                    f"2026-{month:02d}-{day:02d}",
                )
            )
        for c in batch:
            cur.execute("INSERT INTO contents (title, body, category, compliance_score, status, created_at) VALUES (?, ?, ?, ?, ?, ?)", c)
        print(f"✅ Added {len(batch)} contents")
    else:
        print(f"contents: {existing} rows (skip)")

    # === Audit Logs ===
    existing = cur.execute("SELECT COUNT(*) FROM audit_logs").fetchone()[0]
    if existing == 0:
        actions = ["create", "update", "compliance_check", "export", "view"]
        entities = ["visit", "content", "compliance", "report", "hcp"]
        for i in range(30):
            d = random.randint(0, 20)
            cur.execute(
                "INSERT INTO audit_logs "
                "(user_id, action, entity_type, entity_id, detail, "
                "source_end, ip_address, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now', ?))",
                (
                    random.randint(2, 7),
                    random.choice(actions),
                    random.choice(entities),
                    random.randint(1, 100),
                    "demo",
                    "mobile",
                    "127.0.0.1",
                    f"-{d} days",
                ),
            )
        print("✅ Added 30 audit logs")
    else:
        print(f"audit_logs: {existing} rows (skip)")

    conn.commit()

    # === Verify ===
    print("\n=== 数据验证 ===")
    for t in ["users", "contents", "audit_logs"]:
        c = cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t}: {c} rows")

    # Test dashboard queries
    total = cur.execute("SELECT COUNT(*) FROM contents WHERE compliance_score IS NOT NULL").fetchone()[0]
    passed = cur.execute("SELECT COUNT(*) FROM contents WHERE compliance_score IS NOT NULL AND compliance_score >= 1.0").fetchone()[0]
    print(f"\n  合规率: {passed}/{total} ({round(passed / total * 100, 1) if total > 0 else 0}%)")

    by_cat = cur.execute(
        "SELECT category, COUNT(*) as cnt FROM contents "
        "WHERE compliance_score IS NOT NULL "
        "AND compliance_score < 1.0 GROUP BY category ORDER BY cnt DESC"
    ).fetchall()
    print(f"  违规分类: {dict(by_cat)}")

    users_by_role = cur.execute("SELECT role, COUNT(*) FROM users WHERE is_active=1 GROUP BY role").fetchall()
    print(f"  用户分布: {dict(users_by_role)}")

    conn.close()
    print("\n✅ 演示数据就绪！")
    return True


if __name__ == "__main__":
    seed()
