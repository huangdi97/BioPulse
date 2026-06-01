# 修复 Assistant 端 visit 测试

## 问题

`visit_record` 表的列白名单（`shared/columns.py`）和 schema（`assistant/app/database.py`）都不包含 `outcome` 列。

但 `assistant/app/visit_router.py` 中的 `VisitCreate` Pydantic 模型定义了 `outcome: Optional[str]` 字段。

当 `repo.create(body.model_dump())` 被调用时，`body.model_dump()` 包含 `outcome` 键，`validate_columns` 在校验时拒绝了它。

## 要求

### 方案

从 `VisitCreate` 模型中移除 `outcome` 字段。

### 涉及文件

`assistant/app/visit_router.py`

### 修改

删除或注释掉第22行的 `outcome: Optional[str] = Field(None, max_length=500)`

### 验证

```bash
cd /home/hermes/one-cloud-four-ends && rm -f data/test_assistant.db && python -m pytest assistant/app/tests/ -v --tb=line
```

期望：8/8 全部通过。
