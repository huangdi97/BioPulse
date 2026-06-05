# Batch 3：Token 成本监控 — 修补 AiGatewayService -> TokenBudgetService 断链

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
16. ~~必须用opencode写代码~~（**本次正在用 OpenCode 执行**）
17. 启动规则（write→TG→confirm→opencode）
18. 完整准则写入每个tasks.md不可省略

## 任务说明
修补 Token 成本监控的数据流断链：
- `AiGatewayService.chat()` 从 DeepSeek API 获取了 `usage` 数据但从未写入数据库
- `TokenBudgetService.record_usage()` 方法已存在但从未被调用
- 需要建立调用链：chat() 结束后 → 调用 record_usage() 持久化

## 修改范围

### 1. `cloud/app/services/ai_gateway_service.py`
- `chat()` 方法签名增加 `user_id: int` 参数
- 在 `payload = json.loads(raw)` 和 `reply = self._extract_reply(payload)` 之后、`return` 之前：
  - 从 `payload["usage"]` 获取 `prompt_tokens`, `completion_tokens`, `total_tokens`
  - 实例化 `TokenBudgetService()` 并调用 `record_usage(user_id, "deepseek-chat", total_tokens, cost)`
  - cost 计算：DeepSeek V3 定价 ≈ $0.14/M input tokens, $0.28/M output tokens
  - import 添加：`from cloud.app.services.token_budget_service import TokenBudgetService`

### 2. `cloud/app/ai_gateway.py`（路由文件）
- `chat()` 端点调用 `service.chat()` 时，传入 `current_user.get("id")` 作为第一个参数
- 即：`service.chat(user_id=current_user.get("id"), messages=body.messages, ...)`

## 验收标准
1. `AiGatewayService.chat()` 接受 `user_id` 参数并调用 `record_usage()`
2. `record_usage()` 成功将 token 用量写入数据库
3. 现有 API 响应不变（`reply` 和 `usage` 字段不受影响）
4. 代码风格保持原有一致（urllib，非 httpx/requests）
5. 文件不超过300行

## 依赖
- 不需要新建表（`TokenBudgetService` 已存在且可写入）
- 不需要新增路由（只是已有端点的内部逻辑补全）
