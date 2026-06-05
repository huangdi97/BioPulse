# React 情报分析页面

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
- 已搭建：布局组件（Sidebar/TopNav/MainLayout）、UI 组件（Button/Card/Input/Badge）
- 已完成页面：医药看板、科研看板、合规全景（均使用 mock 数据）
- 设计 Token: `src/styles/tokens.css`（CSS Variables）
- 依赖已有：recharts, lucide-react, zustand, @tanstack/react-table
- 路由已有：/pharma, /research, /compliance, /coach, /intel, /settings

## 任务

### 任务1: 情报类型定义 + Mock 数据

在 `src/api/mockIntel.ts` 中添加情报相关 mock 数据：

**论文搜索数据（15条）：**
```
每篇论文：
- id: number
- title: string (中文标题，真实感：如"基于单细胞测序的肿瘤微环境异质性研究")
- authors: string[] (2-3个作者名)
- journal: string (期刊名：Nature Medicine, Cell, Lancet Oncology 等)
- year: number (2024-2026)
- citations: number (引用数)
- keywords: string[] (3-5个关键词)
- pmid: string (PubMed ID格式)
- abstract: string (80-150字摘要)
- relevance: number (0-100 相关度评分)
```

**PI 画像数据（6个PI）：**
```
- id: number
- name: string (中文姓名)
- institution: string (医院/大学名)
- title: string (职称：主任医师/教授/研究员)
- department: string (科室)
- h_index: number (H-index)
- papers: number (论文总数)
- grants: string[] (基金：国自然/省重点等)
- research_areas: string[] (研究方向)
- activity_score: number (0-100 活跃度)
```

**靶点热度数据（10个靶点）：**
```
- id: number
- name: string (如 PD-1, HER2, EGFR, CTLA-4, KRAS G12C 等)
- category: string (靶点类别：免疫检查点/激酶/GPCR 等)
- paper_count: number (年度论文数)
- trial_count: number (临床试验数)
- growth: number (年度增长率%)
- trend_data: {month: string, count: number}[] (最近12个月趋势)
```

### 任务2: 论文搜索页面

修改 `web/src/pages/intel/IntelPage.tsx`：

**顶部**：页面标题"制药情报" + 三个 Tab 切换（论文搜索 / PI画像 / 靶点热度）

**论文搜索 Tab**：
- 搜索框（Input 组件，placeholder: "搜索论文、关键词、作者..."）
- 搜索按钮（蓝色 Button）
- 搜索结果列表（卡片样式）：
  - 每张卡片：标题（蓝色可点击）+ 作者行 + 期刊名（斜体）+ 年份 + 引用数
  - 关键词标签（Badge 组件）
  - 相关度评分条（进度条样式）
  - 点击展开摘要（toggle）
- 分页（简单上一页/下一页，每页5条）
- 空结果提示

### 任务3: PI 画像 Tab

在 IntelPage 中第二 Tab：

- **搜索行**：输入 PI 名称 + 搜索按钮
- **搜索结果**：PI 卡片网格（lg:3col, md:2col, sm:1col）
  - 每张卡片：姓名 + 机构 + 职称
  - H-index 分值（大号字体突出显示）
  - 研究方向标签（Badge）
  - 基金列表
  - 活跃度指示条
- 点击卡片展开详情（底部弹出或右侧面板）

### 任务4: 靶点热度 Tab

在 IntelPage 中第三 Tab：

- **顶部筛选**：靶点类别下拉 + 时间范围选择
- **趋势图**：Recharts LineChart，多线（每个靶点一条线，12个月趋势）
  - X轴：月份
  - Y轴：论文数
  - 颜色区分不同靶点
- **数据表格**：TanStack Table
  - 列：靶点名称/类别/年论文数/临床试验数/增长率
  - 增长率绿色(正)红色(负)显示
  - 可排序
- **靶点详情弹窗**：点击行弹出，显示完整趋势图 + 相关论文数

## 文件清单

**新增文件：**
```
web/src/api/mockIntel.ts
```

**修改文件：**
```
web/src/pages/intel/IntelPage.tsx (替换当前骨架)
```

## 验收标准

1. ✅ /intel 页面显示三个 Tab：论文搜索 / PI画像 / 靶点热度
2. ✅ 论文搜索 Tab：搜索框 + 15条结果卡片 + 分页 + 展开摘要
3. ✅ PI画像 Tab：PI卡片网格 + H-index突出显示 + 研究方向标签
4. ✅ 靶点热度 Tab：多线趋势图 + 数据表格 + 排序
5. ✅ 所有组件使用 tokens.css CSS Variables 样式
6. ✅ 文件不超 300 行（超了拆子组件到 src/components/intel/）
7. ✅ TypeScript 构建通过（tsc -b 无错误）
8. ✅ Vite build 通过
