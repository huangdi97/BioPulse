# PostgreSQL 迁移 — 代码层适配

## 策略

让代码完全 PG-ready，但开发/测试继续用 SQLite。两者通过环境变量 `DATABASE_URL` 切换。

**核心思路：** 用一个兼容层处理 SQLite 和 PG 的差异——`shared/repository.py` 中使用 `%s` 占位符（PG 标准），当连接是 SQLite 时自动转换为 `?`。

**部署流程：** 设置 `DATABASE_URL=postgresql://hermes:pass@localhost/dbname` 即切换到 PG。

## 编码准则（完整版）

1. Think Before Coding
2. Simplicity First
3. Surgical Changes
4. Goal-Driven Execution
5. 架构优先拒绝补丁
6. 面向组件构建
7. 显式优于隐式
8. 代码整洁自文档化
9. 单一职责
10. 组合优于委托
11. 单一状态源
12. 避免语法糖
13. 命名一致性
14. 文件不超过300行
15. 低耦合(模块间只传ID)
16. 必须用opencode写代码
17. 启动规则(write→TG→confirm→opencode)
18. 完整准则写入每个tasks.md不可省略

---

## 任务

### Task 1: 更新 shared/base.py 添加 DB 类型检测

在 `shared/base.py` 或新建 `shared/db.py` 中添加：

```python
import os
import sqlite3

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/cloud.db")

def is_sqlite() -> bool:
    return DATABASE_URL.startswith("sqlite://")

def get_db_type() -> str:
    return "sqlite" if is_sqlite() else "postgresql"
```

### Task 2: 更新 shared/repository.py（核心改动）

文件：`shared/repository.py`

改动：
1. 所有 SQL 中的 `?` → `%s`
2. 在 `execute` 方法中添加 SQLite 兼容：
```python
def execute(self, sql, params=None):
    if self._is_sqlite and params:
        sql = sql.replace('%s', '?')
    return self.db.execute(sql, params)
```
3. `_is_sqlite` 在 `BaseRepository.__init__` 中根据连接类型判断：
```python
self._is_sqlite = hasattr(self.db, 'execute') and 'sqlite3' in type(self.db).__module__
```
或者更简单的：检查 `db` 的类型：
```python
self._is_sqlite = isinstance(self.db, sqlite3.Connection)
```

4. `paginate` 方法中的 `LIMIT ? OFFSET ?` → `LIMIT %s OFFSET %s`
5. `soft_delete` 中的 `updated_at=?` → `updated_at=%s`
6. 其他所有 `?` 占位符 → `%s`

### Task 3: 更新 5 个 database.py 支持 PG

每个端都新增 PG 连接支持：

```python
import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///data/{DB_FILE}")

def get_db():
    if DATABASE_URL.startswith("sqlite://"):
        db_path = DATABASE_URL.replace("sqlite:///", "")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    else:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        try:
            yield conn
        finally:
            conn.close()
```

**注意：** 不要移除 SQLite 支持——它是默认的 dev 模式。

**涉及文件（5个）：**
- cloud/app/database.py
- assistant/app/database.py
- opportunity/app/database.py
- sales-coach/app/database.py
- sales-assistant/app/database.py

### Task 4: 更新 shared/repository.py 中的 BaseRepository.__init__

在初始化时检测 DB 类型并设置 `_is_sqlite` 标志。

### Task 5: 验证

```bash
# 默认模式（SQLite）— 所有测试应通过
cd /home/hermes/one-cloud-four-ends
rm -f data/*.db
python -m pytest cloud/app/tests/ -q --tb=line 2>&1 | tail -1
python -m pytest assistant/app/tests/ -q --tb=line 2>&1 | tail -1
python -m pytest opportunity/app/tests/ -q --tb=line 2>&1 | tail -1
python -m pytest sales-coach/app/tests/ -q --tb=line 2>&1 | tail -1
python -m pytest sales-assistant/app/tests/ -q --tb=line 2>&1 | tail -1
```

期望：所有71个测试通过。

---

## 验收标准

- [ ] `shared/repository.py` 中所有 SQL 使用 `%s` 占位符
- [ ] 自动兼容 SQLite（`%s` 自动转 `?`）
- [ ] 5个 database.py 支持通过 `DATABASE_URL` 环境变量切换
- [ ] 默认模式（SQLite）下 71 个测试全部通过
- [ ] 所有5端 import 通过
