# Layer: mcp_router.py

## 编码准则

1-15. 保持一致
16. 必须用opencode ✅
17. 启动规则 ✅ 已确认
18. 完整准则 ✅

## 任务

将 `cloud/app/mcp_router.py` 中直接操作 Repository 的逻辑新建 Service 封装。

### 当前状态
- 使用 `McpToolsRepository` + `McpGuardService`
- 依赖 `db=Depends(get_db)`
- 3 个端点：register_tool, list_tools, call_tool
- `_row(r)` 辅助函数

### Step 1：新建 Service

创建 `cloud/app/services/mcp_tool_service.py`：
- 类名 `McpToolService`
- `__init__(self, db=Depends(get_db))`
- 方法 `register_tool(body, uid) -> dict`
- 方法 `list_tools(is_active, page, page_size) -> dict`
- 方法 `call_tool(tool_name, params, user_id) -> dict`
- 保留 `McpGuardService` 作为注入依赖

### Step 2：修改 Router

- 删除 `get_db` 导入，改为 `from cloud.app.services.mcp_tool_service import McpToolService`
- 删除 `_row(r)` 辅助函数
- 端点改为 `service: McpToolService = Depends()`

### 验收

1. ast.parse 通过
2. pytest 153 passed
