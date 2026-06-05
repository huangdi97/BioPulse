# Batch 3：Token 成本监控

## 编码准则（18条）
1. Think Before Coding 2. Simplicity First 3. Surgical Changes 4. Goal-Driven Execution 5. 架构优先拒绝补丁 6. 面向组件构建 7. 显式优于隐式 8. 代码整洁自文档化 9. 单一职责 10. 组合优于委托 11. 单一状态源 12. 避免语法糖 13. 命名一致性 14. 文件不超过300行 15. 低耦合(模块间只传ID) 16. 必须用opencode写代码 17. 启动规则(write→TG→confirm→opencode) 18. 完整准则写入每个tasks.md不可省略

## 背景

Token 监控系统的基础设施已存在：
- `token_budget` 和 `token_usage` 表 ✅（database.py）
- `TokenBudgetService` ✅（含 record_usage / check_budget / get_usage_report）
- `token_budget_router.py` ✅（已在 Cloud 注册）
- `token_budget_rules.json` ✅（默认配置）
- 断链：`AiGatewayService.chat()` 拿到 usage 数据后不写入数据库

## 操作

### 1. 修改 `cloud/app/services/ai_gateway_service.py`

在 `chat()` 方法中，在成功获取 API 响应后，调用 `TokenBudgetService.record_usage()`：
- 从 `payload["usage"]` 中提取 `total_tokens`
- 估算 cost（按 deepseek-chat 价格：¥0.5/1M input tokens, ¥2/1M output tokens）
- 调用 `TokenBudgetService` 的 `record_usage()`
- 需要注入 `TokenBudgetService` 或在 chat() 中创建实例

修改要点：
- 在文件顶部 import TokenBudgetService
- 在 chat() 方法中，在 `payload = json.loads(raw)` 之后，调用 `record_usage()`
- 需要从请求的 `current_user` 中获取 user_id，但 chat() 当前不接收 user_id
- 修改 chat() 签名增加 user_id 参数，或从已有的 `current_user` 中获取

### 2. 修改 `cloud/app/ai_gateway.py`（router）

将 `current_user` 中的 user_id 传递给 service.chat()：
- 当前：`result = service.chat(body.messages, body.temperature, body.max_tokens)`
- 改为：`result = service.chat(body.messages, body.temperature, body.max_tokens, current_user.get("id"))`

### 3. React 前端：新增 Token 用量页面

在 `web/src/pages/settings/SettingsPage.tsx` 中增加一个 Tab：
- Tab 名 "Token 用量"
- 调用 `GET /admin/tokens/usage/{user_id}?days=30` 获取 Token 使用报告
- 用折线图显示每日用量（日期 vs token数）
- 显示预算配置和告警阈值

### 4. 验证

- `python -c 'from cloud.app.services.ai_gateway_service import AiGatewayService; print("OK")'`
- `npm run build` 通过
- `curl localhost:8000/admin/tokens/usage/1` 能访问
