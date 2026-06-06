# Exec-017 · Sprint B · 设计缺口补齐

## 目标
1. Flutter 移动端编译运行
2. 四端医药线路由加 scope 守卫

## 编码准则（完整18条）
1. Think Before Coding 2. Simplicity First 3. Surgical Changes 4. Goal-Driven Execution 5. 架构优先拒绝补丁 6. 面向组件构建 7. 显式优于隐式 8. 代码整洁自文档化 9. 单一职责 10. 组合优于委托 11. 单一状态源 12. 避免语法糖 13. 命名一致性 14. 文件不超过300行 15. 低耦合(模块间只传ID) 16. 必须用opencode写代码 17. 启动规则(write→TG→confirm→opencode) 18. 完整准则写入每个tasks.md不可省略

---

## Batch B1: Flutter 编译

### 现状
- 51 个 Dart 文件，完整的 Flutter 项目结构（android/ios/web/linux/macos/windows）
- Flutter SDK 未安装
- 有 `pubspec.yaml`、`mode_provider.dart`、`auth_service.dart` 等

### 操作
1. 安装 Flutter SDK（使用 `snap` 或 `git clone`）
2. `cd mobile_app && flutter pub get`
3. 检查编译错误，修复问题（如有）
4. `flutter build web`（最轻量，不需要安卓/iOS 工具链）
5. 验证构建产物存在

### 验收标准
- `flutter build web` 成功
- `build/web/` 目录存在且有 index.html

---

## Batch B2: 四端医药线路由加 scope 守卫

### 现状
38 个路由文件使用 `get_current_user` 而非 `require_scope("visit")`。替换规则：

| 端 | 路由文件数 | 关键文件 |
|:---|:---:|:---|
| assistant | 12 | hcp_router.py, visit_router.py, task_router.py 等 |
| opportunity | 10 | opportunity_router.py, bidding_router.py 等 |
| sales-assistant | 10 | hcp_router.py, schedule_router.py 等 |
| sales-coach | 7 | scenario_router.py, assessment_router.py 等 |

### 操作（全局替换模式）
每个文件的替换：
1. 添加 import: `from shared.auth_scope import require_scope`
2. 将 `current_user: dict = Depends(get_current_user)` 改为 `current_user: dict = Depends(require_scope("visit"))`
3. 如果文件不再引用 `get_current_user`，移除 `from shared.auth import get_current_user`

### 验收标准
- 四端所有路由使用 `require_scope("visit")` 而非 `get_current_user`
- `grep "get_current_user" assistant/app/ opportunity/app/ sales-assistant/app/ sales-coach/app/` 仅剩 test/conftest 中的
- 四端 import 无断链

---

## 执行顺序

| 顺序 | Batch | 依赖 | 预估耗时 |
|:---|:---|:---|:---:|
| 1 | B1: Flutter 安装+编译 | Flutter SDK 需下载 | 20-30 min |
| 2 | B2: 四端scope守卫 | 无 | 15 min |
