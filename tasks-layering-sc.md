# 分层清理：Sales-Coach (评估+反思路由)

## 修改清单

### 1. SessionService 增加 2 个方法

文件: `sales-coach/app/services/session_service.py`

**新增方法 A** `get_latest_by_trainee(trainee_name: str) -> Optional[dict]`:
```python
def get_latest_by_trainee(self, trainee_name: str) -> Optional[dict]:
    repo = SessionRepository(self.db)
    row = repo.db.execute(
        "SELECT id, dialogue_log, compliance_violations, scenario_id "
        "FROM coach_session WHERE trainee_name = ? "
        "ORDER BY id DESC LIMIT 1",
        (trainee_name,),
    ).fetchone()
    return dict(row) if row else None
```

**新增方法 B** `get_scenario(scenario_id: int) -> Optional[dict]`:
```python
def get_scenario(self, scenario_id: int) -> Optional[dict]:
    from sales_coach.app.repositories import ScenarioRepository
    repo = ScenarioRepository(self.db)
    return repo.get_active_by_id(scenario_id)
```

### 2. AssessmentService 增加 1 个方法

文件: `sales-coach/app/services/assessment_service.py`

**新增方法**: `update_weights(self, weights: WeightConfig) -> dict`:
```python
def update_weights(self, weights) -> dict:
    total = weights.product_knowledge + weights.communication + weights.compliance + weights.objection_handling
    if abs(total - 1.0) > 0.01:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Weights must sum to 1.0")
    from sales_coach.app.assessment_router import DEFAULT_WEIGHTS
    DEFAULT_WEIGHTS.update(weights.model_dump())
    return DEFAULT_WEIGHTS
```

注意：这个 `DEFAULT_WEIGHTS` 在 router 文件中定义。可行的方案：
- 把 `DEFAULT_WEIGHTS` 移到 service 文件中定义，router 从 service 导入
- 或者在 service 中直接操作 `DEFAULT_WEIGHTS`（通过延迟导入避免循环依赖）

**推荐**：把 `DEFAULT_WEIGHTS` 定义从 `assessment_router.py` 移到 `assessment_service.py`，然后 router 从 service 导入。

### 3. assessment_router.py 修改

- 删除 `from sales_coach.app.database import get_db` 导入
- 删除 `db=Depends(get_db)` 参数
- `reflect_on_assessment`: 将裸 SQL 替换为 `session_service.get_latest_by_trainee(assessment.get("trainee_name", ""))`
- `update_weights`: 将权重校验逻辑替换为 `service.update_weights(body)`
- `DEFAULT_WEIGHTS` 导入改为从 service: `from sales_coach.app.services.assessment_service import DEFAULT_WEIGHTS`

### 4. reflection_router.py 修改

- 删除 `from sales_coach.app.database import get_db` 导入
- 删除 `db=Depends(get_db)` 参数
- 将裸 SQL 替换为 `session_service.get_scenario(session["scenario_id"])`

## 规则

1. 不改变任何功能逻辑
2. 不修改 function 签名
3. 不修改 Pydantic model
4. 文件修改后运行 ast.parse 验证语法

## 验收

1. `assessment_router.py` 和 `reflection_router.py` 不再导入 `get_db`
2. 两个文件不再有裸 SQL（`.execute()`）
3. sales-coach 7 个测试全部通过
