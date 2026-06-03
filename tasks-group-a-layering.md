# Group A：4 个 Router 分层改造

## 编码准则

1. Think Before Coding — 先理解再动手。已读取所有源文件。
2. Simplicity First — 用最简单的方式实现：Router→Service 委托，不引入新模式。
3. Surgical Changes — 精准修改：只改 router 和 service 文件，不动 repository/test/model。
4. Goal-Driven Execution — 目标：4 个 router 不导入 get_db，无裸 SQL，153 测试全过。
5. 架构优先，拒绝补丁 — 统一用 `Depends(XxxService)` 模式。
6. 面向组件构建 — 每个 service 职责单一。
7. 显式优于隐式 — 类型注解保留。
8. 代码整洁，自文档化 — 不改变现有 docstring。
9. 单一职责 — 一个 service 方法只做一件事。
10. 组合优于委托 — 不适用。
11. 单一状态源 — db 连接统一由 FastAPI Depends 管理。
12. 避免语法糖 — 不引入新语法。
13. 命名一致性 — 不改变量名/函数名。
14. 文件不超过300行 — 不改变。
15. 低耦合(模块间只传ID) — 已满足。
16. 必须用 opencode 写代码 — ✅
17. 启动规则 — write→TG→confirm→opencode ✅ 已完成。
18. 完整准则写入每个 tasks.md — ✅

## 任务1：mdt_agent_router.py ✅ 已完成

已有 MdtAgentService。已验证：
- 删除了 `from cloud.app.database import get_db`
- 删除了 `_get_svc(db)` 辅助函数
- 三个端点改为 `service: MdtAgentService = Depends()`
- 语法检查通过

## 任务2：token_budget_router.py

已有 TokenBudgetService（236 行）。

`list_alerts` 端点（行 64-75）有 1 处裸 SQL：
```python
row = service.db.execute(
    "SELECT COUNT(*) as count FROM token_usage_alerts WHERE alerted = 0",
).fetchone()
```

**操作**：TokenBudgetService 已新增 `get_daily_usage` 方法（正确但误加了——这个跟 list_alerts 无关）。

实际需要：新建方法 `count_pending_alerts(self) -> int`，router 中 `list_alerts` 调用它替换裸 SQL。

## 任务3：route_router.py

已有 RouteService（270 行）。

检查 `create_rule` 和 `update_rule` 端点是否有裸 SQL。如果有，移到 RouteService 方法中。
如果 router 已经使用 `service: RouteService = Depends()`且无裸SQL，则跳过。

## 任务4：mdt_engine_router.py — 新建 MdtEngineService

当前 202 行，包含：
- `_call_ai()` 工具函数
- `_parse_json()` 工具函数
- `_now()` 工具函数
- 6 个端点（create_session, list_sessions, get_session, debate, consensus, get_opinions, timeline, dashboard）
- 直接使用 `MdtSessionsRepository`, `MdtParticipantsRepository`, `MdtOpinionsRepository`, `AgentRolesRepository`

**操作**：
1. 新建 `cloud/app/services/mdt_engine_service.py`
2. Service 类用 `def __init__(self, db: sqlite3.Connection = Depends(get_db))`
3. 将 `_call_ai`, `_parse_json`, `_now` 移入 Service 作为静态方法或私有方法
4. 为每个端点创建对应的 Service 方法（封装 repository 调用 + 参数处理）
5. Router 改为 `service: MdtEngineService = Depends()`，去掉所有 `db` 参数

## 通用规则

- Service 类：`class XxxService: def __init__(self, db = Depends(get_db)): self.db = db`
- Router 参数：`service: XxxService = Depends()` 替代 `db=Depends(get_db)`
- 不改变任何 API 签名（path、params、response）
- 不改变 Pydantic model
- 不改变测试文件

## 验收

1. 4 个 router 不再导入 `get_db`
2. 无 `.execute()` / `.fetchone()` / `.fetchall()` 残留
3. `python3 -c "import ast; ast.parse(open('xxx').read()); print('OK')"` 都通过
4. `python -m pytest cloud/app/tests/ -x -q --no-cov` 全部 153 通过
