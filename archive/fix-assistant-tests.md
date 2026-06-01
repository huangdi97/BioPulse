# 修复 Assistant 端测试

## 问题

`assistant/app/tests/test_assistant.py` 中的测试失败，原因：

1. **visit_crud_flow**: `visit_record` 表没有 `outcome` 列（列白名单在 `shared/columns.py`）
2. **knowledge_crud**: 可能用了不存在的列名
3. **knowledge_search**: 可能端点路径错误
4. **auth_checks**: 可能 conftest 中的 `auth_token` fixture 创建的用户在 DB 中不存在

## 要求

### 1. 修复 visit 测试

文件：`assistant/app/tests/test_assistant.py`

找到 `test_visit_crud_flow` 中的 `outcome` 字段，改为有效的列名（如 `summary`、`detail`、`feedback` 等）。

先查看 `shared/columns.py` 或 `assistant/app/database.py` 中的 SCHEMA 确认 `visit_record` 表有哪些列。

### 2. 修复 knowledge 测试

文件：`assistant/app/tests/test_assistant.py`

找到 `test_knowledge_crud` 和 `test_knowledge_search`，检查：
- 使用的列名是否在列白名单中
- 端点路径是否正确（`/knowledge/...`）
- 请求数据格式是否匹配

### 3. 修复 auth_checks 测试

文件：`assistant/app/tests/test_assistant.py`

找到 `test_unauthorized_returns_401`、`test_invalid_token_returns_401`、`test_health_does_not_require_auth`，检查失败原因。

可能的修复：确保 `auth_token` fixture 在 `conftest.py` 中正确创建了用户（register + login），而不是直接创建 token。

### 4. 验证

跑通所有 assistant 测试：
```
cd /home/hermes/one-cloud-four-ends && rm -f data/test_assistant.db && python -m pytest assistant/app/tests/ -v --tb=short
```

## 注意

- 先查列白名单：`grep 'visit_record' shared/columns.py` 
- 先查 SCHEMA：`grep -A20 'CREATE TABLE visit_record' assistant/app/database.py`
- 所有改动都要遵守列名校验（validate_columns）规则
