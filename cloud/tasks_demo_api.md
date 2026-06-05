# 演示数据端点（开发模式，无认证）

## 编码准则
1. Think Before Coding
2. Simplicity First
3. Surgical Changes
4. Goal-Driven Execution
5. 架构优先
6. 面向组件构建
7. 显式优于隐式
8. 代码整洁
9. 单一职责
10. 组合优于委托
11. 单一状态源
12. 避免语法糖
13. 命名一致性
14. **文件不超过300行**
15. **低耦合**
16. **必须用opencode写代码**
17. **启动规则: write→TG→confirm→opencode**
18. **完整准则写入每个tasks.md**

## 任务

创建 `/home/hermes/one-cloud-four-ends/cloud/app/routers/demo_router.py`：

- 路由前缀: `/api/demo`
- GET `/dashboard` — 返回 DashboardService 的 overview (无认证)
- GET `/dashboard/users` — 返回 DashboardService 的 user_stats
- GET `/dashboard/compliance` — 返回 DashboardService 的 compliance_stats
- GET `/compliance/summary` — 返回 ComplianceService 的 dashboard_summary

所有端点不加 `Depends(get_current_user)` 或 `Depends(require_scope())`。

在 `cloud/app/main.py` 中注册此路由。

## 验收标准
1. ✅ `curl http://localhost:8000/api/demo/dashboard` 返回数据
2. ✅ `curl http://localhost:8000/api/demo/dashboard/users` 返回用户统计
3. ✅ `curl http://localhost:8000/api/demo/dashboard/compliance` 返回合规统计
4. ✅ 文件不超过 150 行
