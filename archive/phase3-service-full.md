# Phase 3: Service 层全量铺开 — Cloud 端剩余路由

## 编码准则（完整版）

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
15. 低耦合(模块间只传ID)
16. 必须用opencode写代码
17. 启动规则(write→TG→confirm→opencode)
18. 完整准则写入每个tasks.md不可省略

---

## 模式（已验证通过）

**模式1 — 简单 CRUD Service：**
```python
# services/xxx_service.py
from fastapi import Depends, HTTPException
from starlette import status
from cloud.app.database import get_db
from cloud.app.repositories import XxxRepository
from cloud.app.services.base import BaseService
from shared.base import success, PaginatedResponse
from shared.auth import get_current_user
import math

class XxxService(BaseService):
    def __init__(self, db=Depends(get_db)):
        self.repo = XxxRepository(db)

    def create(self, data: dict) -> int:
        return self.repo.create(data)

    def get(self, record_id: int) -> dict:
        row = self.repo.get_by_id(record_id)
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
        return dict(row)

    def update(self, record_id: int, data: dict) -> dict:
        row = self.repo.get_by_id(record_id)
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
        self.repo.update(record_id, data)
        return dict(self.repo.get_by_id(record_id))

    def delete(self, record_id: int) -> None:
        row = self.repo.get_by_id(record_id)
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
        self.repo.soft_delete(record_id)

    def list(self, page=1, page_size=20, **filters) -> PaginatedResponse:
        total, total_pages, rows = self.repo.paginate(page=page, page_size=page_size)
        return PaginatedResponse(items=[dict(r) for r in rows], total=total, page=page, page_size=page_size, total_pages=total_pages)
```

**模式2 — 改造后的路由：**
```python
# xxx_router.py
from cloud.app.services.xxx_service import XxxService

@router.get("", ...)
def list_x(page=Query(1), page_size=Query(20), service: XxxService = Depends()):
    return success(data=service.list(page=page, page_size=page_size))

@router.post("")
def create_x(body: XxxCreate, service: XxxService = Depends()):
    record_id = service.create(body.model_dump())
    return success(data={"id": record_id})
```

---

## 任务

为以下 Cloud 端路由文件创建对应的 Service 类并改造路由：

### Batch 1: Audit + Notification + Board + Team + Compliance

| 路由文件 | Service 类 | 特殊逻辑 |
|:---------|:-----------|:---------|
| audit_router.py | AuditService | 统计数据（stats需要自定义） |
| notification_router.py | NotificationService | 模板渲染+发送+read标记 |
| board_router.py | BoardService | 看板视图+任务CRUD |
| teams_router.py | TeamService | 成员管理 |
| compliance_router.py | ComplianceService | 合规检查逻辑 |

### Batch 2: Content 补充 + Dashboard + Config + Export + API Tokens

| 路由文件 | Service 类 | 特殊逻辑 |
|:---------|:-----------|:---------|
| dashboard_router.py | DashboardService | 聚合查询无需repo |
| config_router.py | ConfigService | 简单CRUD |
| export_router.py | ExportService | 简单CRUD |
| api_tokens.py | ApiTokenService | 简单CRUD |
| ai_gateway.py | AiGatewayService | LLM调用（业务逻辑复杂） |

### Batch 3: EventBus + Edge + Interaction + Customer + Compute

同样的模式——每个路由文件对应一个Service类。

### 所有Batch

继续为剩余所有 Cloud 端路由文件（约40个）创建 Service 类并改造。

**完整路由列表（已完成3个，剩余42个）：**
agent_execution_router.py, agent_pipeline_router.py, agent_role_router.py, ai_gateway.py, api_tokens.py, audit_router.py, board_router.py, brain_memory_router.py, causal_router.py, collaboration_router.py, compliance_router.py, compliance_v2_router.py, compute_router.py, config_router.py, customer_router.py, dashboard_router.py, decision_intel_router.py, edge_router.py, event_bus_router.py, export_router.py, hcp_sandbox_router.py, identity_router.py, interaction_router.py, kg_router.py, market_intel_router.py, marketplace_router.py, mcp_router.py, mdt_engine_router.py, memory_consolidation_router.py, memory_gate_router.py, memory_utility_router.py, nmpa_router.py, notification_router.py, opportunity_router.py, orchestrate_router.py, privacy_router.py, recommend_router.py, route_router.py, soap_decision_router.py, task_router.py, teams_router.py, training_coach_router.py, training_scripts_router.py, world_tree_router.py

## 验收标准

- [ ] 每个路由文件对应的 Service 类存在于 `cloud/app/services/` 中
- [ ] 所有路由文件已改造为使用 Service 层
- [ ] 全项目编译通过
- [ ] Cloud 端 42 个测试通过
- [ ] 其他4端测试不受影响
