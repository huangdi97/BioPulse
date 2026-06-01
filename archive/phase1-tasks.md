# Phase 1: 健康检查增强 + 速率限制 + 测试修复

## 编码准则（完整版·必须写入每个task）

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

## Task 1: 健康检查增强

**文件：** 5端 main.py（cloud, assistant, opportunity, sales-coach, sales-assistant）

**当前状态：** 每个端 main.py 中 `/health` 端点只返回 `{"status": "ok"}`

**改造要求：**

1. 为每个端 main.py 中的 `/health` 端点添加数据库状态检查：
   - 尝试执行 `SELECT 1`（或当前DB的ping）
   - 如果 DB 正常，状态包含 `"db": "connected"`
   - 如果 DB 异常，状态包含 `"db": "disconnected"`，但端点仍返回200（不要返回500）

2. 响应格式统一为：
   ```json
   {
     "status": "ok",
     "db": "connected",
     "uptime": 12345,
     "version": "0.1.0"
   }
   ```

3. uptime：在 main.py 顶部记录 `START_TIME = time.time()`，然后在 health 端点中计算 `int(time.time() - START_TIME)`

4. version：写死 `"0.1.0"`

5. 需要 import `time`

6. 修改只限 health 端点，不碰其他任何逻辑

**涉及文件：**
- cloud/app/main.py
- assistant/app/main.py
- opportunity/app/main.py
- sales-coach/app/main.py
- sales-assistant/app/main.py

---

## Task 2: 速率限制中间件

**新建文件：** shared/rate_limiter.py

**要求：**

1. 基于内存的令牌桶算法，不上Redis
2. 每个IP每分钟100次请求（全局限制）
3. 对 `/auth/login` 和 `/auth/register` 路径更严格：每分钟20次
4. 返回 429 + `Retry-After` header
5. 支持路径白名单（`/health`, `/docs`, `/openapi.json` 不限速）

**接口：**
```python
class RateLimiterMiddleware:
    def __init__(self, app, default_rate: int = 100, window: int = 60):
        ...
```

**使用方式：** 在每个端 main.py 中注册：
```python
app.add_middleware(RateLimiterMiddleware, default_rate=100, window=60)
```
同时为 auth 路径传特殊配置（在中间件内部判断 path）。

令牌桶实现要点：
- 记录每个IP的（令牌数, 上次补充时间）
- 每次请求前补充令牌（按时间间隔）
- 补充后令牌数 ≤ 上限
- 令牌不足则返回429
- 定期清理过期IP记录（每5分钟清理一次，防止内存泄漏）

**响应格式：**
```json
{"code": 429, "message": "Too many requests, please try again later", "request_id": "xxx"}
```

**涉及文件：**
- 新建：shared/rate_limiter.py
- 修改：5端 main.py（添加中间件注册）

---

## Task 3: 测试修复+验证

**现状：** 项目只剩下 test_batch19.py，所有 pytest 测试文件（test_cloud.py, test_assistant.py 等）已丢失。

**要求：** 为 cloud 端创建完整的集成测试基础设施（作为试点），其他端暂不动。

**新建目录和文件：**
```
cloud/app/tests/
  __init__.py
  conftest.py
  test_cloud.py
```

### conftest.py 要求：

1. 使用 FastAPI TestClient（import starlette.testclient）
2. 从 `cloud.app.main` import app
3. 初始化数据库（创建所有表）：`cloud/app/database.py` 中的 `init_db()` 或手动建表
4. 提供一个 fixture `client` 返回 TestClient 实例
5. 提供一个 fixture `auth_token` 先 register + login 拿到 token
6. 使用独立的测试数据库文件 `test_cloud.db`（不污染主库）
7. 在每个测试函数前清空表（setup）

### test_cloud.py 要求：

覆盖以下核心流程（10个测试用例）：

1. **auth流程：** register → login → refresh → me
2. **用户CRUD：** create → get → update → list → delete
3. **内容CRUD：** create → get → list（需token）
4. **合规检查：** 提交违规内容 → 检查compliance_score < 1.0
5. **审计日志：** 创建 → 列表 → 统计
6. **通知系统：** 创建模板 → 发送通知 → 列表 → 标记已读 → 未读数
7. **看板管理：** 创建看板 → 添加任务 → 查看看板 → 删除任务
8. **数据看板：** overview → users → compliance → contents
9. **团队管理：** 创建团队 → 添加成员 → 列表 → 删除成员
10. **边界情况：** 未认证请求返回401/403

**测试风格：** 使用 `httpx` 风格的 TestClient（FastAPI默认）
- 每个测试函数独立，使用 assert
- 测试函数命名：`test_功能描述`

---

## 验收标准

### Task 1 验收：
- [ ] 5端 main.py 的 `/health` 返回 `{"status": "ok", "db": "connected", "uptime": N, "version": "0.1.0"}`
- [ ] DB断开时 `db` 字段变为 `disconnected`
- [ ] 所有端编译通过

### Task 2 验收：
- [ ] shared/rate_limiter.py 存在且编译通过
- [ ] 5端 main.py 注册了中间件
- [ ] 正常请求通过
- [ ] 超频请求返回 429
- [ ] `/health` 和 `/docs` 不限速
- [ ] `/auth/login` 有更严格的限速

### Task 3 验收：
- [ ] cloud/app/tests/ 目录存在
- [ ] conftest.py + test_cloud.py 编译通过
- [ ] 10个测试用例全部能运行
- [ ] 不污染主数据库（使用 test_cloud.db）
