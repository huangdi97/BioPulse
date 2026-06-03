# Layer: settings_router.py + agent_role_router.py

## 编码准则

1-15. 保持一致
16. 必须用opencode写代码 ✅
17. 启动规则 ✅ 已确认
18. 完整准则 ✅

## 任务1：settings_router.py（51行）

### 当前状态
- 自己创建 sqlite3 连接（`get_db_direct()`）
- 直接操作 `DB_PATH`
- 2 个端点：`get_all`, `update`
- 已有 `ConfigService`

### 操作
新建 `cloud/app/services/settings_service.py`：
- 类名 `SettingsService`
- `__init__(self, db=Depends(get_db))`
- 方法 `get_all() -> dict` — 读 settings 表全部记录
- 方法 `update(body) -> dict` — 更新 settings 记录

修改 `cloud/app/settings_router.py`：
- 删除 `get_db_direct()` 和 `import sqlite3`
- 改为 `service: SettingsService = Depends()`

## 任务2：agent_role_router.py（161行）

### 当前状态
- 直接使用 `AgentRolesRepository`
- 依赖 `db=Depends(get_db)`
- 4 个端点：CRUD + list active
- 已有 `rd(row)` 和 `_404(repo, rid)` 辅助函数

### 操作
新建 `cloud/app/services/agent_role_service.py`：
- 类名 `AgentRoleService`
- `__init__(self, db=Depends(get_db))`
- 方法：`create_role(body, uid)`, `list_roles(page, page_size, active_only)`, `get_role(role_id)`, `update_role(role_id, body)`, `delete_role(role_id)`
- 每个方法封装对应的 Repository 调用

修改 `cloud/app/agent_role_router.py`：
- 删除 `get_db` 导入和 `db` 参数
- 删除辅助函数 `rd()` 和 `_404()`
- 改为 `service: AgentRoleService = Depends()`

## 验收

1. ast.parse 所有修改文件通过
2. `python -m pytest cloud/app/tests/ -x -q --no-cov` 153 passed
