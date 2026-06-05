# React 销售教练页面

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
- 已有布局组件（Sidebar/TopNav/MainLayout）、UI 组件（Button/Card/Input/Badge）
- 已有 KpiCard、DataTable、TrendChart 等业务组件可复用
- 设计 Token: `src/styles/tokens.css`（CSS Variables）
- 依赖已有：recharts, lucide-react, @tanstack/react-table
- `/coach` 路由已配置，当前为骨架占位

## 任务

### 任务1: Mock 数据

在 `src/api/mockCoach.ts` 中创建教练相关 mock 数据：

**场景库（5个场景）：**
```
- id, name, description, difficulty (初级/中级/高级), category (拜访/异议/合规/谈判/产品介绍)
- completed: boolean, score: number (0-100), duration: number (训练时长分钟)
- scenarios: string[] (场景标签)
```

5个具体场景：
1. "初访破冰" — 初级 / 拜访 / 第一次拜访陌生HCP
2. "异议处理" — 中级 / 异议 / HCP质疑药品疗效
3. "合规红线" — 高级 / 合规 / 代表面临统方诱惑
4. "价格谈判" — 中级 / 谈判 / 院长要求降价
5. "产品介绍" — 初级 / 产品介绍 / 向科室主任介绍新药

**训练记录（10条）：**
```
- id, scenario_name, date, score, duration, weakness (薄弱环节), strength (亮点)
```

**能力评估数据：**
```
- 5个维度：产品知识/沟通技巧/异议处理/合规意识/谈判能力
- 每个维度 score: 0-100
- 总体评分: average
- 改进建议: string[] (3-5条)
```

### 任务2: 场景库 Tab

修改 `web/src/pages/coach/TrainingPage.tsx`：

**顶部**：
- 页面标题"销售教练"
- 3个 KpiCard：总训练次数 / 平均分 / 待练习场景数
- 3个 Tab：场景库 / 训练记录 / 能力评估

**场景库 Tab**：
- 5个场景卡片网格（lg:3col, md:2col, sm:1col）
- 每张卡片：
  - 场景名称（20px, weight 600）
  - 描述文字（14px, #525252）
  - 难度 Badge（初级=绿 / 中级=琥珀 / 高级=红）
  - 完成状态（已完成=绿色✓ / 未开始=灰色○ / 进行中=蓝色⟳）
  - 评分（如果已完成，显示分数 + 小星星图标）
  - "开始训练"按钮（如果未完成）/ "重新训练"按钮（如果已完成）

### 任务3: 训练记录 Tab

第二 Tab：
- 筛选：全部 / 近期（本周）/ 按场景
- 训练记录列表（DataTable 或自定义列表）
  - 列：日期 / 场景 / 得分 / 时长 / 薄弱环节 / 亮点
  - 得分用 Badge 色标（>90=绿, >70=琥珀, <70=红）
- 最近5条加粗/置顶

### 任务4: 能力评估 Tab

第三 Tab：
- **雷达图**：使用 Recharts RadarChart
  - 5个维度（五边形）
  - 实际分数（蓝色填充半透明）
  - 目标分数（灰色虚线轮廓）
  - 每个维度标注数值
- **下方**：
  - 总体评分（大号数字，居中）
  - 改进建议列表（带序号 + 箭头图标）
  - "开始新训练"按钮

## 文件清单

**新增文件：**
```
web/src/api/mockCoach.ts
```

**修改文件：**
```
web/src/pages/coach/TrainingPage.tsx (替换当前骨架)
```

如果 TrainingPage.tsx 超过 300 行，拆出子组件到 `web/src/components/coach/`：
- `ScenarioCard.tsx` — 场景卡片
- `TrainingRecordTable.tsx` — 训练记录表
- `AbilityRadar.tsx` — 能力雷达图

## 验收标准

1. ✅ /coach 页面显示三个 Tab 完整内容
2. ✅ 场景库 Tab：5个场景卡片网格，难度色标，完成状态，开始按钮
3. ✅ 训练记录 Tab：10条记录列表，得分色标，筛选
4. ✅ 能力评估 Tab：五维雷达图（含目标线）+ 总体评分 + 改进建议
5. ✅ 所有组件使用 tokens.css CSS Variables
6. ✅ 文件不超 300 行
7. ✅ TypeScript 构建通过（tsc -b 无错误）
8. ✅ Vite build 通过
