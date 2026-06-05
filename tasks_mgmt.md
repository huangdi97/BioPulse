# Batch 1：管理端独立前端（8012）

## 编码准则（18条）
1. Think Before Coding 2. Simplicity First 3. Surgical Changes 4. Goal-Driven Execution 5. 架构优先拒绝补丁 6. 面向组件构建 7. 显式优于隐式 8. 代码整洁自文档化 9. 单一职责 10. 组合优于委托 11. 单一状态源 12. 避免语法糖 13. 命名一致性 14. 文件不超过300行 15. 低耦合(模块间只传ID) 16. 必须用opencode写代码 17. 启动规则(write→TG→confirm→opencode) 18. 完整准则写入每个tasks.md不可省略

## 架构设计

管理端 8012 是一个独立的 FastAPI 服务，职责：
1. **数据聚合层**：调用 Cloud:8000 的 demo API（真实数据），聚合后输出给前端
2. **静态文件服务**：提供 React SPA 前端
3. **角色视图**：按总裁/经理/员工展示不同数据和权限

MVP 先做后端骨架 + 前端静态文件服务，前端页面复用现有的 `web/dist/` 构建产物。

## 文件结构

```
management/
├── app/
│   ├── __init__.py
│   ├── main.py                # FastAPI 入口，端口8012
│   ├── database.py            # 本地数据库（视图配置/角色缓存）
│   ├── health_router.py       # 健康检查
│   ├── dashboard_router.py    # 数据聚合 API（调 Cloud:8000）
│   └── static/                # 软链到 web/dist/ 或直接引用
├── requirements.txt
└── .gitignore
```

## 子任务 1：创建 management/ 目录结构

创建所有目录和 __init__.py。

## 子任务 2：main.py

FastAPI 应用，端口 8012，包含：
- 中间件：RequestID、CORS（允许前端所在域）、静态文件挂载
- 路由注册：health_router、dashboard_router
- 全局异常处理
- 启动时初始化本地数据库

## 子任务 3：database.py

本地 SQLite 数据库，存视图配置和角色缓存：
```
management_config (key TEXT PRIMARY KEY, value TEXT)
view_preferences (user_id TEXT, view_type TEXT, config TEXT)
role_cache (user_id TEXT PRIMARY KEY, role TEXT, permissions TEXT, updated_at TEXT)
```

## 子任务 4：health_router.py

```
GET /health → {"status": "ok", "service": "management", "version": "1.0.0"}
```

## 子任务 5：dashboard_router.py

数据聚合层，调用 Cloud:8000 的 demo API。包含：

```
GET /api/management/dashboard
→ 调用 Cloud:8000 的 /api/demo/dashboard 获取聚合数据
→ 返回格式化看板数据（用户数、合规率、内容数）

GET /api/management/dashboard/users
→ 调用 Cloud:8000 的 /api/demo/dashboard/users
→ 返回用户分布

GET /api/management/dashboard/compliance
→ 调用 Cloud:8000 的 /api/demo/dashboard/compliance
→ 返回合规统计

GET /api/management/dashboard/overview
→ 调用多个 Cloud API 聚合
→ 返回总裁视图数据（聚合所有业务线）
```

所有 API 用 httpx 异步调用 Cloud:8000。如果 Cloud 不可用，返回缓存的最近一次数据 + 降级标记。

## 子任务 6：静态文件服务 + 重启 React 构建

- 将 `web/dist/` 用软链或复制到 `management/app/static/`
- 或者直接挂载 `../web/dist` 作为静态文件目录
- 重新构建 `web/` 前端：`cd web && npm run build`

## 子任务 7：验证

1. `python -c 'from management.app.main import app; print("OK")'` 导入成功
2. `uvicorn management.app.main:app --port 8012` 启动成功
3. `curl localhost:8012/health` → 200
4. `curl localhost:8012/api/management/dashboard` → 返回数据
5. 浏览器访问 `http://localhost:8012/` → React SPA 可访问
