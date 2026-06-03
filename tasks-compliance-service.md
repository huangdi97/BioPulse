# Layer: compliance_v2_router.py

## 编码准则

1-15. 保持一致
16. 必须用opencode ✅
17. 启动规则 ✅ 已确认
18. 完整准则 ✅

## 任务

将 `cloud/app/compliance_v2_router.py` 逻辑新建 Service 封装。

### 当前状态
283 行，Cloud 最复杂的 router。包含：
- 5 个 Pydantic model: ScanRequest, ReviewRequest, AuditChainCreate, CorrectionUpdate, EvaluateRequest
- 使用 5 个 Repository: ComplianceRulesRepository, ComplianceAuditLogsRepository, ComplianceCorrectionsRepository, ComplianceReviewQueueRepository, ContentsRepository
- 使用 `ComplianceStrategyService`
- 使用 `check_content` 和 `haslib`, `urllib` 等工具
- 依赖 `db=Depends(get_db)`

### Step 1：新建 Service

创建 `cloud/app/services/compliance_v2_service.py`：
- 类名 `ComplianceV2Service`
- `__init__(self, db=Depends(get_db))`
- 方法对应每个端点逻辑（scan, review, audit_chain, correction, evaluate 等）
- `ComplianceStrategyService` 作为内部依赖（从 router 搬过来）

### Step 2：修改 Router

- 删除 `get_db` 和 Repository 导入
- 保留 Pydantic model 定义
- 改为 `service: ComplianceV2Service = Depends()`

### 验收

1. ast.parse 通过
2. pytest 153 passed（特别是 test_compliance.py 的 17 个测试）
