# 任务：修复 Token 成本监控断链

## 子任务 1：修改 ai_gateway_service.py

在 `cloud/app/services/ai_gateway_service.py`：
- 增加 import：`from cloud.app.services.token_budget_service import TokenBudgetService`
- 修改 `chat()` 签名：增加 `user_id: int = None` 参数
- 在 `usage = payload.get("usage", {})` 之后插入：
  - 如果 user_id 存在且 usage 有内容
  - 提取 total_tokens = usage.get("total_tokens", 0)
  - 估算 cost = total_tokens * 0.001 / 1000
  - 创建 TokenBudgetService 实例并调用 record_usage()

## 子任务 2：修改 ai_gateway.py

在 `cloud/app/ai_gateway.py`：
- 将 `current_user.get("id")` 传递给 service.chat() 调用

## 子任务 3：验证

```bash
python -c 'from cloud.app.services.ai_gateway_service import AiGatewayService; print("OK")'
```
