# B3: Flutter 数据同步 — 从后端拉取到本地 SQLite

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
- 数据流向：Screens → `DatabaseService`（本地SQLite）→ 离线数据
- `ApiClient` + `MultiBackendApiClient` — HTTP客户端基础设施已就位（Dio + JWT）
- `SyncService` — 仅推送本地→服务器（push），无拉取服务器→本地（pull）
- 后端数据在 Assistant(8003) 和 Sales-Assistant(8004) 端，有 HCP/Visit/Surgery/Precall API
- `BackendConfig` 已在 `settings_screen.dart` 中定义，支持5后端的URL配置

## 任务

### 任务1: 扩展 SyncService — 添加数据拉取方法

修改 `mobile_app/lib/services/sync_service.dart`，添加以下方法：

**1a. `pullHcps(String baseUrl)`**
- GET `$baseUrl/hcp` 获取HCP列表
- 解析返回数据为 HCP 模型
- 逐个 upsert（先查是否存在，存在则更新，不存在则插入）到本地 SQLite
- 返回拉取数量

**1b. `pullVisits(String baseUrl)`**
- GET `$baseUrl/visit` 获取拜访记录列表
- 解析为 Visit 模型
- upsert 到本地 SQLite
- 返回拉取数量

**1c. `pullSurgeries(String baseUrl)`**
- GET `$baseUrl/surgery` 获取手术列表
- 解析为 Surgery 模型
- upsert 到本地 SQLite
- 返回拉取数量

**1d. `pullAll(Map<String, String> backendUrls)`**
- 根据 backendUrls 中的 `assistant` 后端拉取 HCP/Visit/Surgery
- 根据 `sales_assistant` 后端拉取 precall 数据
- 返回 `{hcp: n, visits: n, surgeries: n}` 汇总

所有方法应：
- 使用 ApiClient 或 Dio 实例（从 MultiBackendApiClient 获取或新建）
- 添加错误处理（网络异常时静默失败，不影响现有本地数据）
- 设置超时 10 秒
- 文件不超过 300 行

### 任务2: 初始化时自动拉取

修改 `mobile_app/lib/main.dart`：
- 在应用启动后，用户登录成功后
- 调用 `syncService.pullAll()` 从已配置的后端拉取数据
- 异步执行，不阻塞 UI 渲染
- 如果后端不可用（服务未启动），静默跳过

或者在 `mobile_app/lib/providers/` 中创建同步状态Provider，由各页面在 `initState` 时触发拉取。

### 任务3: 在各页面添加 Pull-to-Refresh + 同步触发

以下页面添加下拉刷新（RefreshIndicator），触发对应数据拉取：
- `lib/screens/pharma/hcp_list_screen.dart` → 拉取HCP
- `lib/screens/pharma/visit_list_screen.dart` → 拉取拜访
- `lib/screens/surgery/surgery_list_screen.dart` → 拉取手术
- `lib/screens/surgery/scan_screen.dart` → 拉取手术（备用）

下拉刷新时：
1. 显示加载指示器
2. 调用对应 pull 方法
3. 刷新页面列表
4. 如果后端不可用，SnackBar提示"同步服务暂不可用"

## 文件清单

**修改文件：**
```
mobile_app/lib/services/sync_service.dart（扩展）
mobile_app/lib/main.dart（添加启动同步）
mobile_app/lib/screens/pharma/hcp_list_screen.dart（加下拉刷新）
mobile_app/lib/screens/pharma/visit_list_screen.dart（加下拉刷新）
mobile_app/lib/screens/surgery/surgery_list_screen.dart（加下拉刷新）
mobile_app/lib/screens/surgery/scan_screen.dart（加下拉刷新）
```

## 验收标准

1. ✅ `SyncService.pullHcps()` 可从 Assistant API 拉取HCP数据到本地SQLite
2. ✅ `SyncService.pullAll()` 支持从多个后端拉取不同数据类型
3. ✅ 启动时自动尝试拉取（静默失败，不阻塞UI）
4. ✅ HCP列表页下拉刷新触发数据拉取
5. ✅ 拜访列表页下拉刷新触发数据拉取
6. ✅ 手术列表页下拉刷新触发数据拉取
7. ✅ 后端不可用时 SnackBar 提示
8. ✅ 所有文件不超过 300 行
