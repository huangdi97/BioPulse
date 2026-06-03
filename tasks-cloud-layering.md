# Cloud 分层：11 个 Router → Service 改造

## 分层原则

Router 层：接收请求 → 调 Service → 返回响应
Service 层：业务逻辑编排 → 调 Repository → 异常处理
Repository 层：SQL 执行 → 返回数据（已有，不改）

## Group A — 已有 Service，改造 Router

### 1. mdt_agent_router.py ✅ 已有 MdtAgentService

当前：`get_db` 传参给 `_get_svc(db)` → 直接用 Service
改动：将 `_get_svc(db)` 改为 `service: MdtAgentService = Depends()`，删除 `get_db` 依赖

### 2. token_budget_router.py ✅ 已有 TokenBudgetService

当前：方法调用已通过 service 注入，但 `list_alerts` 有 1 处裸 SQL
```python
row = service.db.execute(
    "SELECT COUNT(*) as count FROM token_usage_alerts WHERE alerted = 0",
).fetchone()
```
改动：将此裸 SQL 封装为 `TokenBudgetService.count_pending_alerts()` 方法

### 3. route_router.py ✅ 已有 RouteService

当前：`create_rule` 和 `update_rule` 中有裸 SQL（`.execute()`）
改动：将裸 SQL 逻辑移到 `RouteService` 中

### 4. mdt_engine_router.py 🆕 需新建 MdtEngineService

当前：202 行，包含 `_call_ai`, `_parse_json`, `_now` 等工具函数 + 6 个端点，直接使用 Repository
改动：
- 新建 `cloud/app/services/mdt_engine_service.py`
- 将工具函数 (`_call_ai`, `_parse_json`, `_now`) 移入 Service
- 将 6 个端点的业务逻辑移入 Service 方法
- Router 只保留 `Depends()` 调用

## Group B — 无 Service，需新建

### 5. agent_execution_router.py 🆕 新建 AgentExecutionService

当前：149 行，直接使用 `AgentExecutionTasksRepository`, `AgentSkillsRepository`
端点：submit_task, list_tasks, get_task, retry_task, cancel_task, get_queue
改动：
- 新建 `cloud/app/services/agent_execution_service.py`
- 每个端点的业务逻辑 → Service 方法
- Router 改为 `service: AgentExecutionService = Depends()`

### 6. agent_pipeline_router.py 🆕 新建 AgentPipelineService

当前：使用 `AgentPipelinesRepository`, `AgentPipelineStepsRepository` + 裸SQL
端点：pipeline CRUD + run pipeline
改动：
- 新建 `cloud/app/services/agent_pipeline_service.py`
- 迁移所有逻辑，包括 LangGraph pipeline_graph 调用
- 裸 SQL 移入 Service

### 7. agent_role_router.py 🆕 新建 AgentRoleService

当前：161 行，直接使用 `AgentRolesRepository`
端点：CRUD + list active
改动：
- 新建 `cloud/app/services/agent_role_service.py`
- 简单 CRUD 委托 → 路由直接调用

### 8. compliance_v2_router.py 🆕 新建 ComplianceV2Service

当前：283 行（Cloud 最复杂），混合 repository + compliance_strategy_service + AI 调用
改动：
- 新建 `cloud/app/services/compliance_v2_service.py`
- 端点多、逻辑杂，拆分为多个 Service 方法
- `ComplianceStrategyService` 保持独立，作为注入依赖

### 9. mcp_router.py 🆕 新建 McpToolService

当前：使用 `McpToolsRepository` + `McpGuardService`
改动：
- 新建 `cloud/app/services/mcp_tool_service.py`
- CRUD 逻辑移入 Service
- `McpGuardService` 保持独立

### 10. settings_router.py 🆕 新建 SettingsService

当前：自己创建 DB 连接 `get_db_direct()` + `ConfigService`
改动：
- 新建 `cloud/app/services/settings_service.py`
- 将 `get_db_direct()` 和 settings CRUD 移入

### 11. visit_router.py 🆕 新建 VisitService

当前：91 行，裸 SQL（自己管理表 + 直接 SQL 查询）
改动：
- 新建 `cloud/app/services/visit_service.py`
- 建表逻辑移到 service 的初始化方法
- CRUD 逻辑封装

## 通用规则

1. 已有 Repository 的 router → 新建 Service 封装 Repository 调用
2. 裸 SQL → Service 方法封装
3. Router 参数 `db=Depends(get_db)` → 改为 `service: XxxService = Depends()`
4. Service 类构造参数统一 `def __init__(self, db: sqlite3.Connection = Depends(get_db))`
5. 不改变任何 API 签名（HTTP path、参数、返回格式）
6. 不改变 Pydantic model 定义
7. 每个文件修改后 ast.parse 验证语法
8. 全修改完后运行 153 个 Cloud 测试

## 验收

1. 以上 11 个 router 文件不再 `import get_db`（或极少例外）
2. 无裸 SQL 残留
3. Cloud 153 个测试全部通过
4. 语法检查通过
