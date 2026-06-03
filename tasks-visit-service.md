# Layer: visit_router.py

## 编码准则

1-15. 见前文，保持一致
16. 必须用opencode写代码 ✅
17. 启动规则(write→TG→confirm) ✅ 已确认
18. 完整准则写入每个tasks.md ✅

## 任务

将 `cloud/app/visit_router.py` 中的裸 SQL 逻辑迁移到新建的 Service 文件中。

### 当前状态

`cloud/app/visit_router.py` 91行，包含：
- `get_direct_db()` — 自己创建 sqlite3 连接
- `init_visits_table(db)` — 创建 visits 表
- `VisitCreate` Pydantic model
- 2 个端点：`create_visit`, `get_visit`
- 全部使用裸 SQL（`db.execute(...)）

### Step 1：新建 Service

创建 `cloud/app/services/visit_service.py`，内容：

- 类名 `VisitService`
- `__init__(self, db=Depends(get_db)): self.db = db`
- 方法 `init_table()` — 创建 visits 表的 SQL（从 router 搬过来）
- 方法 `create_visit(body, user_id) -> dict` — 插入 + 回查，返回完整记录
- 方法 `get_visit(visit_id) -> dict` — 按 ID 查询，不存在则 404

### Step 2：修改 Router

- 删除 `import sqlite3`, `from cloud.app.database import DB_PATH`, `get_direct_db()`, `init_visits_table()`
- 添加 `from cloud.app.services.visit_service import VisitService`
- 端点参数 `user` 改为注入 `service: VisitService = Depends()`
- 端点体内逻辑改为调用 `service.xxx()`

### 验收

1. ast.parse 两个文件通过
2. `python -m pytest cloud/app/tests/ -x -q --no-cov` 153 passed
