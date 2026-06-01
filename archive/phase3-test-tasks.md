# Phase 3: 单元测试补充

## 编码准则（完整版）

1. Think Before Coding — 先想清楚再动
2. Simplicity First — 最简单的方案优先
3. Surgical Changes — 最小化改动范围
4. Goal-Driven Execution — 每个改动有明确目标
5. 架构优先拒绝补丁 — 不改架构只打补丁的不接受
6. 面向组件构建 — 模块化，低耦合
7. 显式优于隐式 — 代码自说明
8. 代码整洁自文档化 — 好代码不需要注释解释
9. 单一职责 — 每个函数/类只做一件事
10. 组合优于委托 — 多用组合，少用继承
11. 单一状态源 — 数据状态有唯一来源
12. 避免语法糖 — 清晰比花哨重要
13. 命名一致性 — 同名同义，名符其实
14. 文件不超过300行 — 超行必拆分
15. 低耦合(模块间只传ID) — 模块不直接引用对方对象
16. 必须用opencode写代码 — 若衡不写一行代码
17. 启动规则(write→TG→confirm→opencode) — 先写文档，发TG，确认，再opencode
18. 完整准则写入每个tasks.md不可省略

---

## 背景

当前只有 cloud 端有测试（14个集成测试，44%覆盖率），其他4端完全无测试。目标是为所有5端建立测试基础设施，使 cloud 端覆盖率达到 60%+，其他端达到 40%+。

## 任务

### Task 1: Cloud 端 Repository 层单元测试

**新建文件：** `cloud/app/tests/test_repositories.py`

**要求：** 为 Cloud 端的核心 Repository 类编写单元测试，mock 掉数据库连接。

测试以下 Repository 类（选择最重要的5个）：
1. `UsersRepository` — create, get_by_id, update, soft_delete, list_all
2. `ContentsRepository` — create, get_by_id, paginate
3. `AuditLogsRepository` — create, paginate, stats
4. `NotificationsRepository` — create 通知, get_by_id, paginate, mark_read, unread_count
5. `TaskBoardsRepository` — create, get_by_id, paginate, create_task, delete_task

**Mock 策略：** 使用 `unittest.mock.MagicMock` 替代真实的 sqlite3 连接
```python
from unittest.mock import MagicMock, patch

@pytest.fixture
def mock_db():
    return MagicMock()
```

每个测试验证：
- SQL 查询被正确调用（用 `mock_db.execute.assert_called_once_with(...)`）
- 参数传递正确
- 返回值处理正确

不要真的连接数据库，全部 mock。

---

### Task 2: Cloud 端更多集成测试

**修改文件：** `cloud/app/tests/test_cloud.py`

**追加以下测试用例（现有14个的基础上）：**

1. **内容更新测试** — POST /contents/ 创建 → PATCH /contents/{id} 更新 → GET 确认更新
2. **内容删除测试** — POST /contents/ 创建 → DELETE /contents/{id} → GET 确认软删除
3. **合规规则测试** — POST /compliance/rules 创建 → GET 列表 → PATCH 更新 → DELETE
4. **通知模板 CRUD** — POST /notifications/templates 创建 → PATCH /notifications/templates/{id} → GET 确认
5. **看板更新测试** — POST /boards/ 创建 → PATCH /boards/{id} 更新名称 → GET 确认
6. **团队更新测试** — POST /teams 创建 → PATCH /teams/{id} 更新描述 → GET 确认
7. **审计日志过滤测试** — GET /audit/logs?page=1&page_size=5 带分页参数
8. **健康检查增强测试** — GET /health 返回正确的 db/uptime/version 字段

**注意事项：**
- 每个测试都独立、可重复运行
- 使用 `_clean_tables` 在测试后清理
- 不要依赖特定的 user_id 或数据顺序

---

### Task 3: Assistant 端集成测试

**新建目录和文件：**
```
assistant/app/tests/
  __init__.py
  conftest.py
  test_assistant.py
```

**conftest.py 要求（参考 cloud 端的模式）：**
- 使用 FastAPI TestClient
- 从 `assistant.app.main` import app
- 独立的测试数据库文件 `test_assistant.db`
- auth_token 和 admin_token fixture
- _clean_tables fixture
- _disable_rate_limiter fixture（使用 monkeypatch）

**test_assistant.py 要求（5个核心测试类）：**

1. **HCP CRUD** — 创建 HCP 档案 → GET 详情 → 更新 → 列表（需要 auth）
2. **预约/日程** — 创建日程 → GET 列表 → 更新状态
3. **笔记系统** — 创建访问笔记 → GET → 更新
4. **知识库查询** — POST /knowledge/query（或搜索端点）
5. **认证检查** — 未认证返回 401，无效 token 返回 401

---

### Task 4: Opportunity 端集成测试

**新建目录和文件：**
```
opportunity/app/tests/
  __init__.py
  conftest.py
  test_opportunity.py
```

**要求（参考 cloud 端模式，5个测试类）：**

1. **商机 CRUD** — 创建商机 → GET → 更新 → 列表
2. **联系人 CRUD** — 创建联系人 → Get → 列表
3. **投标管理** — 创建投标记录 → 更新状态
4. **PubPeer 引用** — GET pubpeer 列表
5. **认证检查** — 401/403

---

### Task 5: Sales-Coach 端集成测试

**新建目录和文件：**
```
sales-coach/app/tests/
  __init__.py
  conftest.py
  test_sales_coach.py
```

**要求（5个测试类）：**
1. **模块 CRUD** — 创建培训模块 → GET → 列表
2. **场景管理** — 创建场景 → GET
3. **会话管理** — 创建会话 → GET → 更新
4. **评估 CRUD** — 创建评估 → GET
5. **认证检查**

---

### Task 6: Sales-Assistant 端集成测试

**新建目录和文件：**
```
sales-assistant/app/tests/
  __init__.py
  conftest.py
  test_sales_assistant.py
```

**要求（5个测试类）：**
1. **日程管理** — 创建日程 → GET → 列表 → 更新状态
2. **HCP 管理** — 创建 HCP → GET
3. **内容 CRUD** — 创建内容 → GET
4. **策略管理** — 创建策略 → GET
5. **认证检查**

---

### Task 7: pytest 覆盖率配置

**修改文件：** `pyproject.toml`

**追加 pytest 覆盖率配置：**
```toml
[tool.pytest.ini_options]
testpaths = [
    "cloud/app/tests",
    "assistant/app/tests",
    "opportunity/app/tests",
    "sales-coach/app/tests",
    "sales-assistant/app/tests",
]
addopts = "--cov=cloud/app --cov=assistant/app --cov=opportunity/app --cov=sales_coach/app --cov=sales_assistant/app --cov-report=term --cov-report=html:coverage_html"

[tool.coverage.run]
branch = true
omit = [
    "*/venv/*",
    "*/tests/*",
    "**/__init__.py",
    "**/seeds/*",
    "**/migrations/*",
]
```

---

## 验收标准

- [ ] 所有5端测试编译通过
- [ ] Cloud 端现有14个测试通过 + 新增8个测试 = 22+个测试通过
- [ ] Assistant 端5个测试通过
- [ ] Opportunity 端5个测试通过
- [ ] Sales-Coach 端5个测试通过
- [ ] Sales-Assistant 端5个测试通过
- [ ] 覆盖率报告显示 Cloud 端 ≥ 60%
- [ ] 全项目编译通过
