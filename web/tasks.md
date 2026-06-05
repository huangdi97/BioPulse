# React Web 管理端 — 脚手架搭建

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

## 任务

### 任务1: 创建 React 项目 + 安装依赖

在 `/home/hermes/one-cloud-four-ends/web/` 目录下：

1. 用 Vite 创建 React + TypeScript 项目（项目名 `web`，在 `one-cloud-four-ends/` 下）
2. 安装依赖：
   - `react-router-dom` (路由)
   - `tailwindcss @tailwindcss/vite` (原子CSS)
   - `@radix-ui/react-dialog @radix-ui/react-dropdown-menu @radix-ui/react-select @radix-ui/react-tabs @radix-ui/react-toast` (Radix UI 基础组件)
   - `lucide-react` (图标)
   - `zustand` (状态管理)
   - `@tanstack/react-table` (数据表格)
   - `recharts` (图表)
   - `class-variance-authority clsx tailwind-merge` (className 工具)
3. 配置 TailwindCSS + CSS Variables（设计Token集成）

### 任务2: 配置设计系统

1. 复制 `/home/hermes/one-cloud-four-ends/design-tokens/tokens.css` 到 `web/src/styles/tokens.css`
2. 在 `web/src/index.css` 中 `@import` tokens.css
3. 在 `web/src/lib/utils.ts` 中创建 cn() 工具函数（用 clsx + tailwind-merge）
4. 在 `tailwind.config.js` 或 `tailwind.config.ts` 中添加自定义颜色和间距，与 CSS Variables 对齐

### 任务3: 创建基础布局

创建 `web/src/components/layout/` 目录，包含：

1. **Sidebar** — 左侧导航栏（暗色背景 #161616）：
   - Logo/项目名称顶部
   - 导航分组：管理看板、合规监控、销售教练、制药情报、系统设置
   - 每个导航项带 lucide 图标
   - 当前激活项高亮（蓝色标识）
   - 底部用户信息 + 登出按钮
   - 宽度 240px，暗色

2. **TopNav** — 顶部导航栏（白色背景）：
   - 左侧：页面标题
   - 右侧：搜索框、通知图标、用户头像
   - 高度 56px，底部阴影 border (shadow-border token)

3. **MainLayout** — 组合 Sidebar + TopNav + 内容区：
   - 内容区根据路由渲染子页面
   - 响应式：小屏时 Sidebar 折叠为 Drawer

### 任务4: 创建路由骨架

在 `web/src/pages/` 下创建以下页面骨架（每个页面只显示标题和占位内容）：

1. `dashboard/pharma.tsx` — 医药看板
2. `dashboard/research.tsx` — 科研看板
3. `compliance/overview.tsx` — 合规全景
4. `coach/training.tsx` — 销售教练
5. `intel/analysis.tsx` — 制药情报
6. `settings/system.tsx` — 系统设置

在 `App.tsx` 中配置路由：
```
/pharma          -> 医药看板
/research        -> 科研看板
/compliance      -> 合规全景
/coach           -> 销售教练
/intel           -> 制药情报
/settings        -> 系统设置
/                -> 重定向到 /pharma
```

### 任务5: 配置 shadcn/ui 组件

创建 shadcn/ui 风格的 Button, Card, Input, Badge 组件（在 `web/src/components/ui/` 下）：

1. **Button** — 支持 variant: default(蓝底白字), outline(边框), ghost(无框), danger(红底)
   - 默认 variant 使用 0px border-radius（Carbon 风格）
   - 高度 40px
   - 支持 size: default, sm, lg

2. **Card** — 白色背景 + shadow-border + 8px border-radius
   - CardHeader, CardTitle, CardContent, CardFooter

3. **Input** — Carbon 底部边框风格
   - 灰色背景 (#f4f4f4)，底部 2px 边框
   - Focus 时底部边框变蓝 (#0f62fe)
   - Error 时底部边框变红 (#da1e28)
   - 高度 40px

4. **Badge** — 药丸形（9999px 圆角）
   - 支持 variant: default, success, warning, error
   - 字号 12px，500字重

## 文件结构（最终结果）

```
web/
├── src/
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Sidebar.tsx
│   │   │   ├── TopNav.tsx
│   │   │   └── MainLayout.tsx
│   │   └── ui/
│   │       ├── Button.tsx
│   │       ├── Card.tsx
│   │       ├── Input.tsx
│   │       └── Badge.tsx
│   ├── pages/
│   │   ├── dashboard/
│   │   │   ├── pharma.tsx
│   │   │   └── research.tsx
│   │   ├── compliance/
│   │   │   └── overview.tsx
│   │   ├── coach/
│   │   │   └── training.tsx
│   │   ├── intel/
│   │   │   └── analysis.tsx
│   │   └── settings/
│   │       └── system.tsx
│   ├── lib/
│   │   └── utils.ts
│   ├── styles/
│   │   ├── tokens.css
│   │   └── index.css
│   ├── App.tsx
│   ├── main.tsx
│   └── vite-env.d.ts
├── package.json
├── vite.config.ts
├── tailwind.config.ts (或 PostCSS)
└── tsconfig.json
```

## 验收标准

1. ✅ `npm run dev` 启动后浏览器可访问，显示登录/管理界面
2. ✅ 左侧 Sidebar 固定 240px，暗色背景，导航项点击切换路由
3. ✅ 顶部 TopNav 显示当前页面标题
4. ✅ 所有设计 Token（颜色/间距/圆角/阴影/字体）通过 CSS Variables 全局可用
5. ✅ Button/Card/Input/Badge 四个基础组件可用，样式符合设计规范
6. ✅ 6个路由页面可正常切换，每个页面显示对应标题
7. ✅ 文件不超过300行
8. ✅ `/` 根路径重定向到 `/pharma`
