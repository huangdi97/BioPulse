# PostgreSQL 迁移执行计划

## 策略

**同步迁移：** 使用 psycopg2（同步驱动），保持所有路由/service/repository 的同步代码不变。
只改：
1. 数据库连接层（database.py）
2. SQL 语法适配（AUTOINCREMENT→SERIAL, `?`→`%s`, 日期函数）
3. Schema 定义
4. 测试 conftest 的 DB setup

**不动：** 路由、Service、Repository 的业务逻辑——都保持同步。

## SQLite → PostgreSQL 语法映射

| SQLite | PostgreSQL |
|--------|------------|
| `INTEGER PRIMARY KEY AUTOINCREMENT` | `SERIAL PRIMARY KEY` |
| `?` 占位符 | `%s` 占位符 |
| `datetime('now')` | `NOW()` |
| `strftime(...)` | `TO_CHAR(...)` |
| `IF NOT EXISTS` | `IF NOT EXISTS`（兼容） |
| `TEXT` | `TEXT`（兼容） |
| `INTEGER` | `INTEGER`（兼容） |
| `BOOLEAN` | `BOOLEAN` |
| `PRAGMA foreign_keys = ON` |（不需要）|
| `sqlite3.connect()` | `psycopg2.connect()` |
| `conn.row_factory = sqlite3.Row` | 不需要（psycopg2 默认返回 dict-like） |
| `.fetchone()["col"]` | `.fetchone()["col"]`（psycopg2 的 RealDictCursor） |

## 任务清单

### Task 1: 安装依赖 + 创建数据库
- `pip install psycopg2-binary`
- 检查 PG 是否运行（`pg_isready`）
- 为5端创建5个独立数据库（如不可行则用同一库不同schema）

### Task 2: 更新 shared 层
- `shared/base.py`：不需要改（不直接操作DB）
- `shared/repository.py`（BaseRepository）：`?`→`%s`，`execute` 适配
- `shared/columns.py`：不需要改（只存列名）

### Task 3: 更新5个 database.py
每个端都需要改 `database.py`：
- `sqlite3.connect()` → `psycopg2.connect()`
- `get_db` 函数改为 PG 连接
- `init_db` 函数
- SQL schema 中 `AUTOINCREMENT` → `SERIAL`

**涉及文件：**
- cloud/app/database.py
- assistant/app/database.py
- opportunity/app/database.py
- sales-coach/app/database.py
- sales-assistant/app/database.py

### Task 4: 更新5个 schema 定义
每个端的 database.py 中嵌入了 CREATE TABLE 语句。需要：
- `INTEGER PRIMARY KEY AUTOINCREMENT` → `SERIAL PRIMARY KEY`
- 检查所有 `TEXT`、`INTEGER`、`BOOLEAN` 类型兼容性
- 删除 SQLite 特有的 pragma 和函数

### Task 5: 更新 shared/repository.py
BaseRepository 中的 `?` 占位符改为 `%s`：
- `update` 方法
- `paginate` 方法
- `list_all` 方法
- `count` 方法
- `soft_delete` 方法

### Task 6: 更新5个 conftest.py（测试）
- 测试中使用 `sqlite3` 创建临时数据库的改为使用 psycopg2
- 或者保持测试用 SQLite（更简单——SQLite 和 PG 的唯一差异在 schema 定义上）
- 推荐方案：测试继续用 SQLite，生产用 PG。这需要测试 conftest 使用不同的 DB 路径

### Task 7: 验证全项目编译 + 测试
- 所有5端 import 通过
- 所有71个测试通过

## 工作顺序

1. 先 Task 1（环境准备）
2. 再 Task 5（shared/repository.py — 核心改动）
3. 再 Task 2+3+4（5端 database.py + schema）
4. Task 6（测试适配）
5. Task 7（验证）
