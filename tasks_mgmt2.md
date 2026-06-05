# 任务：补全 management 服务的角色路由 + 服务层

## 编码准则（18条）
1. Think Before Coding 2. Simplicity First 3. Surgical Changes 4. Goal-Driven Execution 5. 架构优先拒绝补丁 6. 面向组件构建 7. 显式优于隐式 8. 代码整洁自文档化 9. 单一职责 10. 组合优于委托 11. 单一状态源 12. 避免语法糖 13. 命名一致性 14. 文件不超过300行 15. 低耦合(模块间只传ID) 16. 必须用opencode写代码 17. 启动规则(write→TG→confirm→opencode) 18. 完整准则写入每个tasks.md不可省略

## 操作

### 1. 创建 `management/app/services/__init__.py`

空文件

### 2. 创建 `management/app/services/employee_service.py`

包含 async 函数：get_my_profile(user_id), get_my_tasks(user_id), get_my_compliance(user_id), get_my_performance(user_id), get_my_trend(user_id)

每个函数用 httpx 异步调用 Cloud:8000 的 /api/demo/dashboard 获取数据，返回格式化结果。如果 Cloud 不可用，返回空 mock 数据。

### 3. 创建 `management/app/services/manager_service.py`

包含 async 函数：get_team_stats(team_id), get_team_members(team_id), get_team_compliance(team_id), get_team_performance(team_id)

调用 Cloud:8000 的 demo API，按 team_id 过滤返回团队数据。

### 4. 创建 `management/app/services/president_service.py`

包含 async 函数：get_summary(), get_compliance_overview(), get_team_rankings(), get_trend_report()

聚合 Cloud:8000 的多个 demo API 调用（/api/demo/dashboard, /api/demo/dashboard/users, /api/demo/dashboard/compliance），返回总裁视图格式。

### 5. 修改 `management/app/main.py`

在 dashboard_router 的 include 之后注册三个角色路由：

```
from management.app.employee_router import router as employee_router
from management.app.manager_router import router as manager_router
from management.app.president_router import router as president_router

app.include_router(employee_router)
app.include_router(manager_router)
app.include_router(president_router)
```

### 6. 验证

```
python -c 'from management.app.main import app; print("OK")'
```
