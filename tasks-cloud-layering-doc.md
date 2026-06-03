# Cloud 分层执行文档

## 概述

将 Cloud 服务中 11 个 router 的业务逻辑从 router 层迁移到 service 层，实现 Router→Service→Repository 三层架构。

## 当前状态

| Router | 行数 | 当前模式 | 操作 |
|:---|:---:|:---|:---|
| mdt_agent_router | 58 | 已有 MdtAgentService | 改造为 Depends 注入 |
| token_budget_router | 91 | 已有 TokenBudgetService | 1 处裸 SQL 移入 Service |
| route_router | 98 | 已有 RouteService | 2 处裸 SQL 移入 Service |
| mdt_engine_router | 202 | Repository 直用 | **新建 MdtEngineService** |
| agent_execution_router | 149 | Repository 直用 | **新建 AgentExecutionService** |
| agent_pipeline_router | — | Repository + 裸SQL | **新建 AgentPipelineService** |
| agent_role_router | 161 | Repository 直用 | **新建 AgentRoleService** |
| compliance_v2_router | 283 | 混合模式 | **新建 ComplianceV2Service** |
| mcp_router | — | Repository + Guard | **新建 McpToolService** |
| settings_router | 51 | 自建DB连接 | **新建 SettingsService** |
| visit_router | 91 | 裸SQL | **新建 VisitService** |

## 改动要求

每个 Service 类统一使用依赖注入：

```python
class XxxService:
    def __init__(self, db: sqlite3.Connection = Depends(get_db)):
        self.db = db
```

Router 层改为：

```python
# 改前
def list_items(db=Depends(get_db)):
    repo = XxxRepository(db)
    return repo.get_all()

# 改后
def list_items(service: XxxService = Depends()):
    return service.list_all()
```

## 分组执行顺序

1. **快速改造** (Group A，4 个已有 Service) — mdt_agent、token_budget、route、mdt_engine
2. **新建 Service** (Group B, 7 个新建) — 从简单的开始：visit → settings → agent_role → mcp → agent_execution → agent_pipeline → compliance_v2

## 验收标准

- 11 个 router 不再导入 get_db
- 无裸 SQL 残留
- 153 个 Cloud 测试全部通过
- API 行为和返回格式不变

## 风险控制

- 每次修改一个文件后立即 ast.parse 验证
- compliance_v2_router.py（283行）最复杂，放到最后
- 每个 Group 完成后跑一次测试
