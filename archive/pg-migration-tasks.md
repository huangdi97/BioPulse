# PostgreSQL 迁移

## 背景

当前使用 SQLite，生产需要 PostgreSQL。项目是同步 Python（sqlite3），迁移策略：

1. 使用 `psycopg2`（同步驱动），不改 async/await
2. 安装 PostgreSQL 16
3. 为5端创建5个数据库
4. 更新所有 database.py 和 shared/repository.py
5. 测试也使用 PG（保持一致性）

## 编码准则（完整版）

18条准则...（此处省略，实际执行时补全）

---

## Task 1: 安装 PostgreSQL 并创建数据库

```bash
sudo apt-get update -qq && sudo apt-get install -y -qq postgresql postgresql-client
sudo pg_ctlcluster 16 main start
```

为5端创建数据库和用户：
- 数据库：cloud_db, assistant_db, opportunity_db, sales_coach_db, sales_assistant_db
- 用户：hermes（密码：hermes_pg_2026）
- 所有数据库归 hermes 用户所有

验证：`psql -U hermes -d cloud_db -c "SELECT 1"`

## Task 2: 更新 shared/repository.py（BaseRepository）

文件：`shared/repository.py`

改动：
- `?` 占位符 → `%s`
- `execute` 方法：psycopg2 使用 `cursor.execute(sql, params)` 的 `%s` 语法
- `paginate` 方法：`LIMIT ? OFFSET ?` → `LIMIT %s OFFSET %s`
- `soft_delete`：`UPDATE ... SET is_active=0, updated_at=? WHERE id=?` → `UPDATE ... SET is_active=0, updated_at=%s WHERE id=%s`
- 导入：`sqlite3` → `psycopg2`（仅在需要的地方）
- `self.db.execute()` 不需要改——psycopg2 的 connection 和 sqlite3 的 connection 都有 `.execute()` 方法

## Task 3: 更新5个 database.py

每个端：

### cloud/app/database.py

```python
import psycopg2
from psycopg2.extras import RealDictCursor

DB_CONFIG = {
    "dbname": "cloud_db",
    "user": "hermes",
    "password": "hermes_pg_2026",
    "host": "localhost",
    "port": 5432,
}

def get_db():
    conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.executescript(SCHEMA_SQL)  # psycopg2 支持 executescript
    conn.commit()
    conn.close()
```

### Schema 语法适配

SCHEMA_SQL 中的改动：
- `INTEGER PRIMARY KEY AUTOINCREMENT` → `SERIAL PRIMARY KEY`
- 删掉 `PRAGMA foreign_keys = ON` 等 SQLite pragma
- `TEXT` 保持不变
- `INTEGER` 保持不变
- `BOOLEAN` 保持不变

对 `cloud/app/schema.py` 执行同样的语法适配。

### 其他4端同理：
- assistant/app/database.py（数据库：assistant_db）
- opportunity/app/database.py（数据库：opportunity_db）
- sales-coach/app/database.py（数据库：sales_coach_db）
- sales-assistant/app/database.py（数据库：sales_assistant_db）

---

## 验收标准

- [ ] PostgreSQL 16 安装并运行
- [ ] 5个数据库创建成功
- [ ] `shared/repository.py` 使用 `%s` 占位符
- [ ] 5个 database.py 使用 psycopg2
- [ ] 5个 schema 定义适配 PG 语法
- [ ] 全项目编译通过
- [ ] 所有71个测试通过
