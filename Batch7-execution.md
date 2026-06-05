# Batch 7：React 前端全面切换真实 API

## 编码准则（完整18条）
1. Think Before Coding
2. Simplicity First
3. Surgical Changes
4. Goal-Driven Execution
5. 架构优先拒绝补丁
6. 面向组件构建
7. 显式优于隐式
8. 代码整洁自文档化
9. 单一职责
10. 组合优于委托
11. 单一状态源
12. 避免语法糖
13. 命名一致性
14. 文件不超过300行
15. 低耦合（模块间只传ID）
16. 必须用opencode写代码
17. 启动规则(write→TG→confirm→opencode)
18. 完整准则写入每个tasks.md不可省略

## 现状
6 个 API 调用仍是纯 mock，页面直接从 `mockData.ts` 导入静态数据：

| 函数 | 使用页面 | 后端端点 |
|:----|:---------|:---------|
| `visitTrends` | PharmaPage.tsx (折线图) | ❌ 无 |
| `teamRanks` | PharmaPage.tsx (表格) | ❌ 无 |
| `violations` | PharmaPage.tsx + CompliancePage.tsx (违规列表) | ❌ 无 |
| `researchKpis` | ResearchPage.tsx (KPI卡片) | ❌ 无 |
| `piSources` | ResearchPage.tsx (表格) | ❌ 无 |
| `productMatchStats` | ResearchPage.tsx (饼图) | ❌ 无 |

已实时的：`pharmaKpis` 和 `complianceKpis` 走 `/api/demo/*`，Intel 全走 8006。

## 方案

### 1. 后端（Cloud:8000 demo_router 加 6 个端点）
在已有的 `demo_router.py` + `dashboard_service.py` 中新增 6 个 GET 端点：
- `GET /api/demo/visit-trends` → `{"dates": [...], "counts": [...], "passRates": [...]}` (30天)
- `GET /api/demo/team-ranks` → `[{"name": "...", "visits": N, "complianceRate": N, "deals": N}]`
- `GET /api/demo/violations` → `[{"id": N, "repName": "...", "type": "...", ...}]`
- `GET /api/demo/research-kpis` → `[{"title": "...", "value": ..., "change": N, "icon": "..."}]`
- `GET /api/demo/pi-sources` → `[{"name": "...", "institution": "...", "matches": N, "lastActivity": "..."}]`
- `GET /api/demo/product-match-stats` → `[{"category": "...", "total": N, "matched": N, "rate": N}]`

数据结构与 mockData.ts 保持一致。数据用逻辑生成（非随机，保证可预测），如 visitTrends 返回近30天数据。

### 2. 前端 client.ts
6 个函数改为 try { fetchApi → 返回真实数据 } catch { 降级到 mockData 导入 }

### 3. 前端页面（PharmaPage / CompliancePage / ResearchPage）
每页加 `useEffect` + `useState` 异步加载数据：
- 首次渲染时调用 client.ts 函数 loading
- 加载完成后替换静态 mock 导入
- 维持 fallback：API 失败时仍显示 mock 数据

## 验收标准
1. 6 个后端端点全部返回 200，数据结构与 mockData.ts 一致
2. 启动 Cloud:8000 后，前端页面加载时调用这些端点
3. API 不可用时降级到 mock 数据（不白屏）
4. CP 和 Pharma 页面布局不变

## 执行顺序
Step 1: 后端加 6 个端点（demo_router.py + dashboard_service.py）
Step 2: 前端 client.ts 加 API 调用 + fallback
Step 3: 前端页面加 useEffect 异步加载
