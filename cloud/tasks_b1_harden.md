# B1: 生产硬化 + CI/CD

## 编码准则（必须遵守）
1. Think Before Coding — 先想清楚再写
2. Simplicity First — 简单优先，不过度设计
3. Surgical Changes — 精准改动，不多改
4. Goal-Driven Execution — 目标驱动，不跑偏
5. 架构优先，拒绝补丁 — 先定架构再写代码
6. 面向组件构建 — 组件化开发
7. 显式优于隐式 — 代码清晰可读
8. 代码整洁，自文档化 — 不写多余注释
9. 单一职责 — 一个文件只做一件事
10. 组合优于委托 — 组件组合优先
11. 单一状态源 — 状态不分散
12. 避免语法糖 — 简单直接
13. 命名一致性 — 统一命名风格
14. **文件不超过300行** — 超了必须拆分
15. **低耦合** — 模块间只传ID，不传对象
16. **必须用opencode写代码** — 所有代码通过opencode生成
17. **启动规则: write→TG→confirm→opencode**
18. **完整准则写入每个tasks.md，不可省略**

## 任务

### 任务1: 修复SQL注入漏洞

文件：`/home/hermes/one-cloud-four-ends/cloud/app/services/training_coach_service.py`

问题在第263行：
```python
f"ORDER BY CASE WHEN difficulty='{suggested}' THEN 0 ELSE 1 END, id LIMIT 1"
```

`suggested` 变量来自于 `self._suggest_diff(avg_score)` 的返回值。看 `_suggest_diff` 方法确认它的可能值（应该是 'beginner', 'intermediate', 'advanced' 等枚举值）。

修复方案：
- 定义一个白名单集合 `VALID_DIFFICULTIES = {'beginner', 'intermediate', 'advanced'}`
- 在拼接到SQL之前检查 `suggested in VALID_DIFFICULTIES`
- 如果不在白名单中，默认用 `'beginner'`

### 任务2: 合并 shared/ 层代码重复

有两组代码重复：

**第一组：JSONFormatter**
- `shared/structured_logging.py`（49行）— `setup_logging()` 函数 + `JSONFormatter` 类
- `shared/middleware.py`（84行）— 也有一个 `JSONFormatter` + `setup_json_logging()`

合并方案：
1. 保留 `shared/structured_logging.py` 作为JSONFormatter的唯一实现
2. 增强它：把 `shared/middleware.py` 中 JSONFormatter 的额外字段（如果存在）合并进去
3. 修改 `shared/middleware.py`，让它 import 并使用 `shared/structured_logging` 的 JSONFormatter 而不是自己实现

**第二组：RequestIDMiddleware**
- `shared/request_id_middleware.py` — 独立的 RequestIDMiddleware
- `shared/middleware.py` — 也有 RequestIDMiddleware

合并方案：
1. `shared/middleware.py` 的版本更完整（有时序、ContextVar等），保留它
2. `shared/request_id_middleware.py` 改为 import 并 re-export `shared/middleware` 中的版本
3. 或者直接删除 `shared/request_id_middleware.py`，更新所有 import 它的地方改为 import 自 `shared.middleware`

### 任务3: GitHub Actions CI

创建 `/home/hermes/one-cloud-four-ends/.github/workflows/ci.yml`：

```yaml
name: CI
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install Python deps
        run: pip install -r requirements.txt
      - name: Ruff check
        run: ruff check
      - name: Pytest
        run: cd cloud && python -m pytest && cd ..

  web:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: web
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '22'
      - name: Install
        run: npm ci
      - name: Build
        run: npm run build

  mobile:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: mobile_app
    steps:
      - uses: actions/checkout@v4
      - name: dart analyze
        run: |
          if command -v dart; then
            dart analyze
          else
            echo "dart not available, skipping"
          fi
```

创建 `cloud/requirements.txt`（如果不存在）包含项目依赖：
```
fastapi
uvicorn
pydantic
pydantic-settings
pytest
ruff
```

## 验收标准

1. ✅ `training_coach_service.py` 第263行的SQL注入已修复（白名单校验）
2. ✅ `shared/structured_logging.py` 为唯一JSONFormatter实现
3. ✅ `shared/middleware.py` import 使用 shared/structured_logging 的 JSONFormatter
4. ✅ `shared/request_id_middleware.py` 被合并到 shared/middleware 或删除
5. ✅ 所有 import 了被删除文件的地方已更新
6. ✅ `.github/workflows/ci.yml` 存在且结构正确
7. ✅ `pytest` 全部通过
8. ✅ `ruff check` 无报错
