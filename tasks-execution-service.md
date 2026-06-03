# Layer: agent_execution_router.py

## 编码准则

1-15. 保持一致
16. 必须用opencode ✅
17. 启动规则 ✅ 已确认
18. 完整准则 ✅

## 任务

将 `cloud/app/agent_execution_router.py` 直接操作 Repository 的逻辑新建 Service 封装。

### 当前状态
- 使用 `AgentExecutionTasksRepository`, `AgentSkillsRepository`
- 依赖 `db=Depends(get_db)`
- 6 个端点：submit_task, list_tasks, get_task, retry_task, cancel_task, get_queue
- `_row(r)` 辅助函数

### Step 1：新建 Service

创建 `cloud/app/services/agent_execution_service.py`：
- 类名 `AgentExecutionService`
- `__init__(self, db=Depends(get_db))`
- 方法对应每个端点逻辑

### Step 2：修改 Router

- 删除 `get_db` 和 Repository 导入
- 改为 `service: AgentExecutionService = Depends()`

### 验收

1. ast.parse 通过
2. pytest 153 passed
