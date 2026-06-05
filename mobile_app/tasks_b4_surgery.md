# B4: 跟台助手独立入口

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

Flutter 项目在 `/home/hermes/one-cloud-four-ends/mobile_app/`
- 已有 surgery 相关页面：`surgery_list_screen.dart`, `surgery_form_screen.dart`, `surgery_detail_screen.dart`, `scan_screen.dart`
- 现有模式切换：5模式（Pharma/Surgery/Opportunity/SalesCoach/Research）通过 ModeProvider 切换
- 底部导航在 `home_screen.dart` 中，每种模式有各自的导航项
- SyncService 已有 `pullSurgeries()` 方法
- 后端：Assistant(8003) 有 surgery_router.py + surgery_service.py

## 任务

### 任务1: 跟台专用首页

创建 `mobile_app/lib/screens/surgery/surgery_home_screen.dart` — 跟台助手首页：

**顶部**：欢迎语 + 当前日期 + 待同步数量（从SyncService获取）
**操作卡片行**（横向滚动）：
- 「扫码」— 跳转 scan_screen
- 「新建手术」— 跳转 surgery_form_screen
- 「查看日程」— 跳转 surgery_list_screen（选中当日Tab）
- 「离线缓存」— 显示已缓存手术数量

**今日手术列表**（5条）：
- 从本地 DatabaseService 查询当日手术
- 卡片显示：患者名、手术类型、医院、状态色标、时间
- 点击跳转 detail

**底部操作区**：
- 同步状态指示条（显示待同步条数，点击触发同步）
- 快速回到顶部的按钮

使用 `design-tokens/tokens.dart` 中的 DesignTokens 样式。

### 任务2: 添加独立路由

在 `mobile_app/lib/app.dart` 中添加路由：
- `/surgery_home` → SurgeryHomeScreen
- 同时保留现有 `/home` 路由

### 任务3: 设置页面加"启动模式"选项

在 `mobile_app/lib/screens/settings_screen.dart` 中添加：
- 「启动模式」下拉选择器
- 选项：标准模式（模式切换页）/ 跟台模式（直接进入跟台首页）
- 保存到 SharedPreferences，key: `launch_mode`
- 选项值：`standard` / `surgery`

### 任务4: 修改启动逻辑

修改 `mobile_app/lib/screens/splash_screen.dart`：
- 登录成功后，检查 `launch_mode`
- 如果为 `surgery`，导航到 `/surgery_home`
- 如果为 `standard`，导航到 `/home`

修改 `mobile_app/lib/screens/login_screen.dart`：
- 同样逻辑：登录成功后检查 launch_mode 决定导航目标

## 文件清单

**新增文件：**
```
mobile_app/lib/screens/surgery/surgery_home_screen.dart
```

**修改文件：**
```
mobile_app/lib/app.dart（添加路由）
mobile_app/lib/screens/settings_screen.dart（添加启动模式选择器）
mobile_app/lib/screens/splash_screen.dart（根据launch_mode导航）
mobile_app/lib/screens/login_screen.dart（根据launch_mode导航）
```

## 验收标准

1. ✅ `/surgery_home` 显示跟台专用首页：欢迎语 + 操作卡片 + 今日手术列表 + 同步状态
2. ✅ 操作卡片点击跳转到对应页面
3. ✅ 今日手术列表从本地 SQLite 加载
4. ✅ 设置页有"启动模式"选项（标准/跟台）
5. ✅ 选择"跟台模式"后，下次启动直接进入跟台首页
6. ✅ 所有文件不超过 300 行
