# Flutter 移动端 — 新增管理 Tab

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

## 现有结构参考

Flutter 项目在 `/home/hermes/one-cloud-four-ends/mobile_app/`
已有 38 个 dart 文件，5 模式切换，MultiBackendApiClient。

现有导航在 `lib/main.dart` 或 `lib/app.dart` 中用 BottomNavigationBar + 模式切换。
设计 Token 在 `/home/hermes/one-cloud-four-ends/design-tokens/tokens.dart`

## 任务

### 任务1: 创建管理 Tab 页面

在 `mobile_app/lib/screens/management/` 目录下创建：

**1. management_dashboard_screen.dart** — 管理首页（员工级）：
- 顶部：欢迎语 + 当前角色标识（"药代" / "科研销售"）
- 统计卡片行（横向滚动）：本月拜访数、合规率%、任务完成数
- 最近合规记录列表（5条，带状态色标识：绿色通过/琥珀警告/红色违规）
- 通知列表（最近3条）
- 使用 tokens.dart 中的 DesignTokens 颜色和样式

**2. compliance_record_screen.dart** — 合规记录列表：
- 筛选 Tab：全部 / 通过 / 警告 / 违规
- 列表项：日期 + 拜访对象 + 检查项 + 状态标签（Badge）
- 点击展开详情（底部弹出 Sheet）
- 空状态提示

**3. notification_screen.dart** — 通知中心：
- 列表：时间 + 标题 + 内容摘要 + 已读/未读标识
- 全部标记已读按钮
- 空状态提示

### 任务2: 管理 Tab 入口 + 路由

在现有 App 底部导航栏（BottomNavigationBar）中加一个"管理"图标 Tab：
- 图标：Settings / Dashboard / BarChart 选一个
- 标签："管理"
- 选中时显示 management_dashboard_screen

路由配置（在 app.dart 或 router 文件中）：
- `/management` → ManagementDashboardScreen
- `/management/compliance` → ComplianceRecordScreen  
- `/management/notifications` → NotificationScreen

### 任务3: 集成设计 Token

新页面使用 `/home/hermes/one-cloud-four-ends/design-tokens/tokens.dart` 中的：
- 颜色（DesignTokens 静态常量）
- 间距（DesignTokens.spaceXs 等）
- 圆角（DesignTokens.radiusSm 等）
- 字体（DesignTokens.body 等 TextStyles）

## 文件清单

```
mobile_app/lib/screens/management/
├── management_dashboard_screen.dart
├── compliance_record_screen.dart
└── notification_screen.dart
```

修改文件：
- `mobile_app/lib/app.dart` 或路由文件（新增路由）
- 底部导航所在的文件（新增管理 Tab）

## 验收标准

1. ✅ App 底部导航多了一个"管理"Tab
2. ✅ 管理首页显示统计卡片 + 合规记录 + 通知
3. ✅ 合规记录页面支持 Tab 筛选
4. ✅ 通知中心有已读/未读状态
5. ✅ 所有页面使用 DesignTokens 样式
6. ✅ 文件不超过 300 行
7. ✅ flutter analyze 无新增错误
