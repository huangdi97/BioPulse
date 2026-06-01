# 任务：Repository 层 PG 兼容 —— PGCompatConnection 包装器

## 编码准则（完整18条）
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

## 目标
Repository 层一直依赖 `sqlite3.Connection.execute()`（直连对象上的快捷方法），但 psycopg2 连接没有 `.execute()`。需要创建一个 PG 连接包装器，让 Repository 层在 PG 模式下也能工作。

## 根因
```
AttributeError: 'psycopg2.extensions.connection' object has no attribute 'execute'
```
psycopg2 需要 `conn.cursor().execute(sql, params)`，而 sqlite3 允许 `conn.execute(sql, params)`。
两个 BaseRepository（`cloud/shared/repository.py` + `shared/repository.py`）的 `execute()` 方法都调用 `self.db.execute(sql, params)`。
所有 86+ 子类 Repository 也直接调 `self.db.execute()`。
还有 `cursor.lastrowid` 在 PG 中不存在（需要用 `RETURNING id` + `fetchone()[0]`）。

## 具体步骤

### 步骤1：修改 `shared/db.py` — 添加 PG 包装类

新增三个类：

#### `PGRow(dict)`
继承 dict，支持整数索引访问（因为 `fetchone()[0]` 到处在用）：
- `__getitem__`：如果 key 是 int 或 slice，用 `list(self.values())[key]` 返回
- `__getattr__`：支持 `row.column_name` 访问

```python
class PGRow(dict):
    def __getitem__(self, key):
        if isinstance(key, (int, slice)):
            return list(self.values())[key]
        return dict.__getitem__(self, key)
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)
```

#### `PGCompatCursor`
包装 psycopg2 cursor，模拟 sqlite3 cursor 行为：
- `execute(sql, params)` — 执行 SQL，返回 self
- `fetchone()` — 返回 PGRow 或 None
- `fetchall()` — 返回 [PGRow, ...]
- `rowcount` — 属性代理
- `lastrowid` — 属性（初始 None，由外部设置）
- `close()`

注意：`execute()` 直接把 sql 和 params 传给 `self._cur.execute()`。不修改 SQL。
`fetchone()` 和 `fetchall()` 返回的每行都包成 `PGRow`。

#### `PGCompatConnection`
包装 psycopg2 connection，提供 `.execute()` 方法：
- `execute(sql, params=None)` — 创建 cursor，执行，返回 PGCompatCursor
- `commit()` — 委托给原始 conn
- `cursor()` — 返回原始 psycopg2 cursor（给需要原生 cursor 的地方用）
- `close()` — 关闭连接

### 步骤2：修改双 BaseRepository 的 `create()` 方法

#### `cloud/shared/repository.py` line 40-43
原代码：
```python
cursor = self.execute(query, values)
self.db.commit()
return cursor.lastrowid
```
改为 PG 兼容：
```python
cursor = self.execute(query, values)
self.db.commit()
if self._is_sqlite:
    return cursor.lastrowid
else:
    # PG 需要显式获取插入 ID
    return self.execute(f"SELECT currval(pg_get_serial_sequence('{self.table_name}', 'id'))").fetchone()[0]
```

或者更安全的做法——在每个 create 方法后面加 RETURNING id 判断：
```python
if not self._is_sqlite:
    query += " RETURNING id"
cursor = self.execute(query, values)
self.db.commit()
if self._is_sqlite:
    return cursor.lastrowid
else:
    return cursor.fetchone()[0]
```

使用第二种方案（RETURNING id）。这样更精确，不依赖 PG 内部序列函数。

#### `shared/repository.py` line 46-51
同样的修改模式。`shared/repository.py` 的 `create()` ：
```python
def create(self, data, extra=None):
    ...
    cols = ", ".join(data.keys())
    vals = ", ".join("%s" for _ in data)
    query = f"INSERT INTO {self.table} ({cols}) VALUES ({vals})"
    if not self._is_sqlite:
        query += " RETURNING id"
    cur = self.execute(query, list(data.values()))
    self.db.commit()
    if self._is_sqlite:
        return cur.lastrowid
    else:
        return cur.fetchone()[0]
```

### 步骤3：修改各端 `database.py` 的 `get_db()` PG 分支

共 5 个文件，每个的 PG 分支从：
```python
from psycopg2.extras import RealDictCursor
conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
```
改为：
```python
from shared.db import PGCompatConnection
conn = PGCompatConnection(psycopg2.connect(DATABASE_URL))
```

文件列表：
1. `cloud/app/database.py` — line 29-34
2. `assistant/app/database.py` — line 179-184
3. `opportunity/app/database.py` — line 152-157
4. `sales-assistant/app/database.py` — line 183-188
5. `sales-coach/app/database.py` — line 73-78

注意：`RealDictCursor` 不再需要——PGCompatCursor 已经通过 PGRow 实现了 dict-like 访问。

注意：对于 `cloud/app/database.py`，`get_db()` 行数是 28-42（与其它端略有不同，因为多了 `row.row_factory` 设置）。用搜索定位 `psycopg2.connect` 行后替换。

### 步骤4：检查 `cloud/shared/repository.py` 的类型提示

该文件 line 7: `self.db: sqlite3.Connection` — 改为 `self.db`（不写类型，或者改成 `Any`）
line 18: `def get_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:` — 这个已经返回 dict，没问题。
其他方法同理。但类型标注只影响 IDE 提示，不影响运行。为了清晰，可以不改。

### 步骤5：检查各端子类 Repository 中的 `self.db.execute()` 直调

在各端子类 Repository 中（如 cloud/app/repositories.py），如果有方法直接调用 `self.db.execute(...)` 而不是 `self.execute(...)`，这些调用在 wrapper 模式下也能工作因为 PGCompatConnection 提供了 `.execute()`。

但注意：子类中 `self.db.execute(sql, params)` 如果使用 `?` 占位符（SQLite 格式），需要改为 `%s`。但之前 PG 适配时已经改过了（shared/repository.py 的 execute() 会做 `?`→`%s` 转换）。

云查一下各端子类中是否还有 `?` 占位符的使用。

## 验收标准
1. 不设 `DATABASE_URL` 时，全端 SQLite 测试通过（71/71）
2. 设 `DATABASE_URL=postgresql://hermes:hermes_pg_2026@localhost:15432/cloud_db` 时，Cloud 端测试全部通过（使用 PG 后 42 个都应该 OK）
3. 所有 `.db.execute()` 调用在 PG 模式下正常工作
4. `create()` 后 `lastrowid` 返回正确值
5. `fetchone()[0]` 索引访问在 PG 模式下正常工作
6. `row["column_name"]` 字典访问在 PG 模式下正常工作
