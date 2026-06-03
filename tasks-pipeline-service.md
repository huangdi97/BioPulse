# Layer: agent_pipeline_router.py

## 编码准则

1-15. 保持一致
16. 必须用opencode ✅
17. 启动规则 ✅ 已确认
18. 完整准则 ✅

## 任务

将 `cloud/app/agent_pipeline_router.py` 逻辑新建 Service 封装。

### 当前状态
- 使用 `AgentPipelinesRepository`, `AgentPipelineStepsRepository`
- 依赖 `db=Depends(get_db)`
- 含 `from cloud.langgraph.pipeline_graph import get_pipeline_graph`

### Step 1：新建 Service

创建 `cloud/app/services/agent_pipeline_service.py`：
- 类名 `AgentPipelineService`
- `__init__(self, db=Depends(get_db))`
- 方法对应每个端点逻辑
- `get_pipeline_graph` 保留在 router 中或在 service 中直接 import

### Step 2：修改 Router

- 删除 `get_db` 和 Repository 导入
- 改为 `service: AgentPipelineService = Depends()`

### 验收

1. ast.parse 通过
2. pytest 153 passed
