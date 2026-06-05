# React 管理看板 — 医药/科研/合规 三页面

## 编码准则（必须遵守）
1. Think Before Coding — 先想清楚再写
2. Simplicity First — 简单优先，不过度设计
3. Surgical Changes — 精准改动，不多改
4. Goal-Driven Execution — 目标驱动，不跑偏
5. 架构优先，拒绝补丁 — 先定架构再写代码
6. 面向组件构建 — 组件化开发
7. 显式优于隐式 — 代码清晰可读
8. 代码整洁，自文档化 — 不写多余注释
9. 单一职责 — 一个文件只做一件事
10. 组合优于委托 — 组件组合优先
11. 单一状态源 — 状态不分散
12. 避免语法糖 — 简单直接
13. 命名一致性 — 统一命名风格
14. **文件不超过300行** — 超了必须拆分
15. **低耦合** — 模块间只传ID，不传对象
16. **必须用opencode写代码** — 所有代码通过opencode生成
17. **启动规则: write→TG→confirm→opencode**
18. **完整准则写入每个tasks.md，不可省略**

## 现有上下文

React 项目在 `/home/hermes/one-cloud-four-ends/web/`
- Vite + React + TypeScript + TailwindCSS v4
- 布局组件: Sidebar (240px暗色), TopNav (56px白), MainLayout
- UI 组件: Button, Card, Input, Badge (在 components/ui/)
- 路由: /pharma, /research, /compliance, /coach, /intel, /settings
- 设计 Token: src/styles/tokens.css (CSS Variables)
- 依赖: recharts, @tanstack/react-table, lucide-react, zustand 已装

设计系统参考（查看 `design-tokens/tokens.json` 和 `src/styles/tokens.css`）：
- 品牌蓝 #0f62fe, 医药蓝 #0f62fe, 科研紫 #8b5cf6
- 白色背景, 卡片用 shadow-border (0 0 0 1px rgba(0,0,0,0.08))
- Carbon 风格 0px 圆角按钮, 8px 圆角卡片
- 字体: Inter (主), JetBrains Mono (等宽)

## 任务

### 任务1: 类型定义 + Mock 数据 + API 客户端

创建 `web/src/types/dashboard.ts`：
```typescript
// KPI 卡片
export interface KpiCard {
  title: string
  value: string | number
  change: number // 百分比变化, 正数=上升
  icon: string   // lucide icon name
  trend: 'up' | 'down' | 'neutral'
}

// 拜访统计
export interface VisitStat {
  date: string
  count: number
  passRate: number
}

// 团队排行
export interface TeamRank {
  name: string
  visits: number
  complianceRate: number
  deals: number
}

// 合规违规
export interface ViolationItem {
  id: number
  repName: string
  type: string
  detail: string
  severity: 'high' | 'medium' | 'low'
  date: string
  status: 'pending' | 'resolved'
}

// 科研看板
export interface ResearchKpi {
  title: string
  value: string | number
  change: number
  icon: string
}

export interface PiSource {
  name: string
  institution: string
  matches: number
  lastActivity: string
}

export interface ProductMatchStat {
  category: string
  total: number
  matched: number
  rate: number
}
```

创建 `web/src/api/mockData.ts` — 包含所有 mock 数据（医药/科研/合规），数据要真实感强：
- 医药 KPI: 本月拜访(128次, +12%), 合规率(94.2%, +3.1%), 活跃代表(42人, -2%), 成单率(38%, +5%)
- 拜访趋势（最近30天的日数据，用 Date 生成）
- 团队排行（8个代表名字+数据）
- 科研 KPI: PI线索(86个, +23%), 产品匹配率(72%, +8%), 报价中(34个, -5%), 成单额(286万, +15%)
- 违规数据（10条不同类型，高/中/低严重度）
- PI来源表（6个PI+机构+匹配数）
- 产品匹配统计（4个品类）

创建 `web/src/api/client.ts` — API 客户端骨架：
- baseURL 可配置，默认 'http://localhost:8000'
- `fetchApi(path, options)` 通用函数
- `getDashboardOverview()` 等方法（先用 mock 数据，结构保留）
- 预留 JWT token 注入（Authorization header）

### 任务2: KPI 卡片组件

创建 `web/src/components/dashboard/KpiCard.tsx`：
- 白色卡片，shadow-border 边框, 8px 圆角
- 左侧：lucide 图标（圆形背景，淡蓝底 #edf5ff）
- 中间：标题（14px, #525252）+ 数值（32px, weight 600, #161616）
- 右侧：变化百分比（绿色▲ 红色▼）
- 点击整张卡片可交互（cursor pointer, hover 效果）
- 不超过 80 行

### 任务3: 趋势图组件

创建 `web/src/components/dashboard/TrendChart.tsx`：
- 使用 recharts LineChart
- X轴：日期（简化显示）
- Y轴：数量
- 双线：拜访数（蓝色 #0f62fe）+ 合规率（绿色 #24a148, 次Y轴）
- 网格虚线，圆角数据点
- 响应式宽度
- 白色卡片 + shadow-border
- 不超过 120 行

### 任务4: 数据表格组件

创建 `web/src/components/dashboard/DataTable.tsx`：
- 使用 @tanstack/react-table
- 通用 props: columns, data
- 带排序（点击表头）
- 行 hover 高亮
- 无分页（小数据量）
- 不超过 100 行

### 任务5: 医药看板页面

修改 `web/src/pages/dashboard/PharmaPage.tsx`（替换骨架）：
- **顶部**：页面标题 + 日期范围选择器（简单 Tabs: 今日/本周/本月）
- **KPI 行**：4个 KpiCard 横向排列（lg:4col, md:2col, sm:1col）
- **中段左**：拜访趋势图 (TrendChart, 宽 2/3)
- **中段右**：合规率环形图（Recharts PieChart, 宽 1/3）
  - 绿色通过 + 琥珀警告 + 红色违规
  - 中间显示总合规率
- **下段左**：团队排行表（DataTable, 宽 2/3）
  - 列：排名/代表/拜访数/合规率/成单数
- **下段右**：最近违规列表（自定义组件, 宽 1/3）
  - 3条最近违规，带严重度色标
  - 点击"查看全部"跳转到 /compliance
- 不超过 290 行（超了拆子组件）

### 任务6: 科研看板页面

修改 `web/src/pages/research/ResearchPage.tsx`（替换骨架）：
- **顶部**：页面标题 + 模式切换 Tabs（标准版/高级版）
- **KPI 行**：4个 KpiCard（与医药风格一致，紫色调图标）
- **中段左**：PI线索来源表（DataTable, 2/3）
  - 列：PI姓名/机构/匹配数/最近活跃
- **中段右**：产品匹配率饼图（PieChart, 1/3）
  - 4个品类各自的匹配率
- **下段**：报价管线（简易 Kanban 三列：报价中/审批中/已成交）
  - 每列显示数量 + 简要列表
- 不超过 290 行

### 任务7: 合规全景页面

修改 `web/src/pages/compliance/CompliancePage.tsx`（替换骨架）：
- **顶部**：页面标题 + 筛选（严重度:全部/高/中/低 + 状态:全部/待处理/已解决）
- **KPI 行**：4个合规 KPI 卡片
  - 本月检查(842次), 通过率(94.2%), 违规(49次, -8%), 待处理(12件)
- **中段**：违规列表（完整数据表格, TanStack Table）
  - 列：日期/代表/违规类型/详情/严重度/状态/操作
  - 严重度用 Badge 组件（高=红色, 中=琥珀, 低=灰色）
  - 操作列：标记已处理按钮
- **下段**：违规分类柱状图（BarChart）
  - X轴：违规类型（统方/利益输送/备案异常/场所异常等）
  - Y轴：次数
  - 每个柱子按严重度分色堆叠
- 不超过 290 行

### 任务8: 集成到 Sidebar 导航（可选）

确保 Sidebar 已有对应导航项且高亮正确。

## 文件清单

**新增文件：**
```
web/src/types/dashboard.ts
web/src/api/mockData.ts
web/src/api/client.ts
web/src/components/dashboard/KpiCard.tsx
web/src/components/dashboard/TrendChart.tsx
web/src/components/dashboard/DataTable.tsx
```

**修改文件：**
```
web/src/pages/dashboard/PharmaPage.tsx
web/src/pages/research/ResearchPage.tsx
web/src/pages/compliance/CompliancePage.tsx
```

## 验收标准

1. ✅ `npm run dev` 启动后 /pharma 显示医药看板（KPI + 趋势图 + 团队排行 + 违规列表）
2. ✅ /research 显示科研看板（KPI + PI线索表 + 匹配率饼图 + 报价管线）
3. ✅ /compliance 显示合规全景（KPI + 违规列表 + 分类柱状图 + 筛选）
4. ✅ 所有页面适配响应式（lg:4col → md:2col → sm:1col）
5. ✅ 所有组件使用 tokens.css 中的 CSS Variables 样式
6. ✅ 所有文件不超300行
7. ✅ TypeScript 构建通过（tsc -b 无错误）
8. ✅ Vite build 通过
