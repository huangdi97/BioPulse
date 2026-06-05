# 任务：React 前端 — demo API 混合接入

## 编码准则（18条）
1. Think Before Coding 2. Simplicity First 3. Surgical Changes 4. Goal-Driven Execution 5. 架构优先拒绝补丁 6. 面向组件构建 7. 显式优于隐式 8. 代码整洁自文档化 9. 单一职责 10. 组合优于委托 11. 单一状态源 12. 避免语法糖 13. 命名一致性 14. 文件不超过300行 15. 低耦合(模块间只传ID) 16. 必须用opencode写代码 17. 启动规则(write→TG→confirm→opencode) 18. 完整准则写入每个tasks.md不可省略

## 操作

修改 `web/src/api/client.ts`：

当前：所有 getXxx() 函数直接返回 mockData 的静态数据

改为：
- `getPharmaKpis()`：调用 `/api/demo/dashboard` 获取 real 数据，映射为 KpiCard[]。user_count→"活跃代表"，compliance_rate→"合规率"，不存在的返回 mock 数据降级。
- `getComplianceKpis()`：调用 `/api/demo/dashboard/compliance` 获取 real 数据，映射为 KpiCard[]。total→"本月检查"，pass_rate→"通过率"，failed→"违规"
- 其余函数（getVisitTrends, getTeamRanks, getViolations, getResearchKpis, getPiSources, getProductMatchStats）继续用 mock 数据（后端暂无对应数据）

API 地址 `baseURL` 保持为 `http://localhost:8000`

验证：`npm run build` 通过
