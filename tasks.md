# 任务：修复孤立路由 + 清除重复文件

## 编码准则（18条）
1. Think Before Coding 2. Simplicity First 3. Surgical Changes 4. Goal-Driven Execution 5. 架构优先拒绝补丁 6. 面向组件构建 7. 显式优于隐式 8. 代码整洁自文档化 9. 单一职责 10. 组合优于委托 11. 单一状态源 12. 避免语法糖 13. 命名一致性 14. 文件不超过300行 15. 低耦合(模块间只传ID) 16. 必须用opencode写代码 17. 启动规则(write→TG→confirm→opencode) 18. 完整准则写入每个tasks.md不可省略

## 子任务 1：注册 Cloud 的 10 个孤立路由

**文件：** `cloud/app/main.py`

**新增 import（放在 `from cloud.app.routers.switch_router import router as switch_router` 之后）：**

```python
# === 孤立路由注册 ===
from cloud.app.a2a_registry_router import router as a2a_registry_router
from cloud.app.agent_framework_router import router as agent_framework_router
from cloud.app.brain_orchestrator_router import router as brain_orchestrator_router
from cloud.app.causal_attribution_router import router as causal_attribution_router
from cloud.app.federated_node_router import router as federated_node_router
from cloud.app.mdt_agent_router import router as mdt_agent_router
from cloud.app.rl_routing_router import router as rl_routing_router
from cloud.app.routers.trust_audit_router import router as trust_audit_router
from cloud.app.routers.content_factory_router import router as content_factory_router
from cloud.app.routers.cell_network_router import router as cell_network_router
```

**新增 `app.include_router()`（放在 `app.include_router(token_budget_router)` 之后、startup 函数之前）：**

```python
app.include_router(a2a_registry_router)
app.include_router(agent_framework_router)
app.include_router(brain_orchestrator_router)
app.include_router(causal_attribution_router)
app.include_router(federated_node_router)
app.include_router(mdt_agent_router)
app.include_router(rl_routing_router)
app.include_router(trust_audit_router)
app.include_router(content_factory_router)
app.include_router(cell_network_router)
```

## 子任务 2：删除 Cloud 的重复文件

**文件：** `cloud/app/model_compression_router.py`
**操作：** 删除此文件（已存在更新版本在 `cloud/app/routers/model_compression_router.py`，已在 main.py 中注册）

## 子任务 3：注册 Assistant 的 offline_router

**文件：** `assistant/app/main.py`

**新增 import（放在 `from assistant.app.ws_router import router as ws_router` 之后）：**

```python
from assistant.app.offline_router import router as offline_router
```

**新增 include（放在 `app.include_router(media_router)` 之后）：**

```python
app.include_router(offline_router)
```

## 子任务 4：注册 Sales-Coach 的 digital_human_router

**文件：** `sales-coach/app/main.py`

**新增 import（放在 `from sales_coach.app.reflection_router import router as reflection_router` 之后）：**

```python
from sales_coach.app.digital_human_router import router as digital_human_router
```

**新增 include（放在 `app.include_router(reflection_router)` 之后）：**

```python
app.include_router(digital_human_router)
```

## 子任务 5：验证

1. 启动 Cloud 服务测试路由注册成功
2. 确保 `ruff check` 通过
