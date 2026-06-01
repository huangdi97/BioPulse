# Phase 2 剩余任务

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

## Task A: 剩余 PaginatedResponse 统一

以下路由文件中的列表端点仍然使用 `success(data={"items": ..., "total": ..., "page": ..., "page_size": ...})` 手工 dict 格式。改成使用 `PaginatedResponse`。

**注意：**
- 需要 import `math` 和 `from shared.base import success, PaginatedResponse`
- 计算 `total_pages = math.ceil(total / max(page_size, 1))`
- 如果已有 `total_pages` 变量在作用域中，直接使用
- 修改后格式为：`return success(data=PaginatedResponse(items=items, total=total, page=page, page_size=page_size, total_pages=total_pages))`

**需要修改的文件和行号：**

1. `cloud/app/recommend_router.py:110` — data={"items": items, "total": total, "limit": limit, "offset": offset}
   - 注意：这里的参数叫 limit/offset 不是 page/page_size，需要保留或做适配
   - 加上 total_pages = math.ceil(total / max(limit, 1))

2. `cloud/app/recommend_router.py:151` — 同样格式，同上

3. `cloud/app/decision_intel_router.py:82` — data={"items": items, "total": total, "page": page, "page_size": page_size}
   - 检查 total_pages 是否已在作用域中

4. `cloud/app/decision_intel_router.py:212` — 同上

5. `cloud/app/market_intel_router.py:182` — 同上

6. `cloud/app/memory_gate_router.py:116` — 同上

7. `cloud/app/compliance_v2_router.py:148` — data={"items": rows, "total": total, "page": page, "page_size": page_size}

8. `cloud/app/compliance_v2_router.py:298` — 同上

9. `cloud/app/training_coach_router.py:185` — 特殊格式：`success({"items":..., "total":...})` 没有 `data=` 关键字
   - 改为 `success(data=PaginatedResponse(...))`

10. `cloud/app/soap_decision_router.py:132` — 同上，没有 data= 关键字

11. `cloud/app/hcp_sandbox_router.py:115` — 同上，没有 data= 关键字

12. `cloud/app/hcp_sandbox_router.py:178` — 同上

13. `cloud/app/hcp_sandbox_router.py:230` — 同上

---

## Task B: API 文档补齐

给以下路由端点添加 summary 和 description：

### cloud/app/auth_router.py

```python
@router.post("/register", status_code=status.HTTP_201_CREATED, 
    summary="Register a new user account",
    description="Creates a new user with username and password. Returns user_id on success.",
)
def register(...)

@router.post("/login",
    summary="Authenticate user and get tokens",
    description="Validates credentials and returns access_token and refresh_token.",
)
def login(...)

@router.post("/refresh",
    summary="Refresh access token",
    description="Exchange a valid refresh_token for a new access_token.",
)
def refresh(...)
```

---

## 验收标准

- [ ] 所有列表端点使用 PaginatedResponse
- [ ] 全项目编译通过
- [ ] 14个测试通过（`rm -f data/test_cloud.db && python -m pytest cloud/app/tests/ -v`）
