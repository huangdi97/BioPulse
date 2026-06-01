# S2 Phase 1 收尾 — 测试修复 + 代码风格配置

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

## 背景

当前已有：
- `shared/rate_limiter.py` — 基于令牌桶的速率限制中间件，已在5端 main.py 中注册
- `cloud/app/tests/conftest.py` — cloud端测试基础设施（TestClient + DB初始化）
- `cloud/app/tests/test_cloud.py` — 14个测试用例（auth/user/content/compliance/audit/notification/board/dashboard/team/auth-required）

所有代码文件均存在且编译通过。

---

## Task 1: 修复测试中的速率限制问题

**问题：** conftest.py 中有一个 `_reset_rate_limiter` fixture，尝试用 `RateLimiterMiddleware.buckets.clear()` 在测试间清除限速器状态。但这行不通，因为 `buckets` 是 `__init__` 中设置的**实例属性**，不是类属性。`RateLimiterMiddleware.buckets` 会抛 AttributeError，导致所有测试 ERROR。

**要求：** 修复 conftest.py 中的限速器 fixture，确保限速器在测试期间不干扰。注意 — `conftest.py` 在 `cloud/app/tests/conftest.py`，限速器中间件在 `shared/rate_limiter.py` 中定义。

**可选的解决方案思路（不限于此，OpendCode自行判断最优方案）：**
- 方案A：在 conftest 中使用 `monkeypatch` 让中间件的 `dispatch` 方法变成纯 passthrough
- 方案B：修改中间件暴露一个 class-level 的方法来重置所有实例的状态
- 方案C：在 conftest 中直接修改中间件实例的属性

选择优雅且可持续的方案。

**涉及文件：**
- `cloud/app/tests/conftest.py`（修改）
- `shared/rate_limiter.py`（可能需要小改）

---

## Task 2: 修复通知测试中的 user_id 问题

**问题：** `test_cloud.py` 中的 `TestNotificationSystem.test_notification_flow` 测试中，发送通知时硬编码 `"user_id": 1`，然后查询 `/notifications/` 时用的是 `auth_token`。但是 `auth_token` fixture 注册了一个新用户（user_id 不一定是 1），所以刚发送的通知不在该用户的列表中，导致 `assert len(items) >= 1` 失败。

**要求：** 修复测试逻辑，确保通知发送给正确的用户，并且列表查询能拿到该通知。

注意不在一个session/scope里的不同数据库连接看到行。

**涉及文件：**
- `cloud/app/tests/test_cloud.py`（修改）

---

## Task 3: 创建 pre-commit 配置文件

**新建文件：** `.pre-commit-config.yaml`（项目根目录）

**要求：**
- 包含以下 hooks：
  - black（line-length=100）
  - flake8（max-line-length=100, extend-ignore=E203,W503）
  - mypy（ignore-missing-imports, 带 pydantic/fastapi/sqlalchemy-stubs 额外依赖）
  - pre-commit-hooks（trailing-whitespace, end-of-file-fixer, check-yaml, check-merge-conflict, check-added-large-files with maxkb=500）
- Python版本：3.12

**涉及文件：**
- 新建：`.pre-commit-config.yaml`

---

## Task 4: 创建 pyproject.toml 工具配置

**新建文件（覆盖）：** `pyproject.toml`（项目根目录，同一个文件可能已有其他内容）

**要求：**
- `[tool.black]` 配置 line-length=100, target-version py312
- `[tool.flake8]` 配置 max-line-length=100, extend-ignore=E203/W503
- `[tool.mypy]` 配置 python_version=3.12, ignore-missing-imports=true
- 所有工具的 exclude 覆盖 .git, __pycache__, venv/
- 保留 pyproject.toml 中可能已有的其他内容（如 pytest 配置）

**注意：** 先读取 pyproject.toml 看是否已有内容，再追加或合并。如果文件不存在就创建。

**涉及文件：**
- `pyproject.toml`（修改或新建）

---

## 验收标准

- [ ] 所有14个测试全部通过（`cd /home/hermes/one-cloud-four-ends && rm -f data/test_cloud.db && python -m pytest cloud/app/tests/ -v`)
- [ ] 限速器在测试期间不产生 AttributeError
- [ ] 通知测试正确发送并断言
- [ ] `.pre-commit-config.yaml` 存在且格式正确
- [ ] `pyproject.toml` 包含 black/flake8/mypy 配置
- [ ] 全项目编译通过（`python -c "import cloud.app.main; import assistant.app.main; import opportunity.app.main; import sales_coach.app.main; import sales_assistant.app.main; import shared.rate_limiter"`）
