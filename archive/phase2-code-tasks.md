# Phase 2: API标准化 — 代码改造

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

## Task 1: 修复 exception handler 错误码映射

**背景：** 5端 main.py 中的 HTTPException handler 目前返回 `{"code": exc.status_code, "message": exc.detail}`。`code` 字段应该用 `ErrorCode` 枚举值（0-7），而不是 HTTP 状态码。

**要求：** 修改5端 main.py 中的 exception handler，添加 HTTP status → ErrorCode 映射：

| HTTP Status | ErrorCode | 
|-------------|-----------|
| 401 | ErrorCode.UNAUTHORIZED (1) |
| 403 | ErrorCode.FORBIDDEN (2) |
| 404 | ErrorCode.NOT_FOUND (3) |
| 409, 422 | ErrorCode.VALIDATION_ERROR (4) |
| 429 | ErrorCode.RATE_LIMITED (7) |
| 500 | ErrorCode.INTERNAL_ERROR (5) |
| 其他 | ErrorCode.INTERNAL_ERROR (5) |

**注意：** 响应中的 HTTP 状态码保持不变，只改 JSON body 中的 `code` 字段。

**已有 ErrorCode 定义在：** `shared/base.py`
```python
class ErrorCode(IntEnum):
    SUCCESS = 0
    UNAUTHORIZED = 1
    FORBIDDEN = 2
    NOT_FOUND = 3
    VALIDATION_ERROR = 4
    INTERNAL_ERROR = 5
    CONFLICT = 6
    RATE_LIMITED = 7
```

**修改示例（仅 cloud/app/main.py 为例，其他端同理）：**

当前：
```python
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={'code': exc.status_code, 'message': exc.detail, 'data': None}
    )
```

修改后：
```python
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    code_map = {401: 1, 403: 2, 404: 3, 409: 4, 422: 4, 429: 7}
    error_code = code_map.get(exc.status_code, 5)
    return JSONResponse(
        status_code=exc.status_code,
        content={'code': error_code, 'message': exc.detail, 'data': None}
    )
```

同时 Global exception handler 中的 `code`: 500 改为 `code`: 5（ErrorCode.INTERNAL_ERROR）。

**涉及文件（5个）：**
- cloud/app/main.py
- assistant/app/main.py
- opportunity/app/main.py
- sales-coach/app/main.py
- sales-assistant/app/main.py

**验收：** 所有端编译通过，`import *app/main*` 成功。

---

## Task 2: PaginatedResponse 统一

**背景：** 目前约 50 处引用 `PaginatedResponse`，但很多列表端点返回的是 `{"items": [...], "total": N}` 这种手工拼的 dict，没有统一使用 `PaginatedResponse` 模型。

**PaginatedResponse 模型：**
```python
class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
```

**要求：** 
扫描所有 `*_router.py` 文件（5端），找到所有返回列表数据的端点，确保它们使用 `PaginatedResponse` 而不是手工拼 dict。

具体来说：
- 找到所有 `"items"` 在返回 dict 中的地方
- 检查是否使用了 `PaginatedResponse` 
- 如果没用，改成使用 `PaginatedResponse`
- 需要 import `math` 计算 `total_pages = math.ceil(total / page_size)`（如果还没有 import）

**注意：** `total_pages` 计算用 `math.ceil(total / max(page_size, 1))` 防除零

**涉及文件：** 所有 `*_router.py` 中返回列表数据的端点

---

## Task 3: 裸 dict 返回包装为 success()

**背景：** 约 15 处路由函数直接 `return {...dict...}` 而不是 `return success(data={...})`。这些需要包装为统一的 success() 调用。

**要求：** 扫描所有 `*_router.py` 文件，找到所有直接的 `return {` 语句（不在 `return success(` 内部的），将它们改为 `return success(data={...})`。

**注意：** 排除以下情况：
- `return JSONResponse(...)` — exception handler 里的，不用改
- 内部嵌套函数中的return

通过 grep 查找：
```
grep -rn "^\s*return {" --include="*_router.py" cloud/app assistant/app opportunity/app sales-coach/app sales-assistant/app
```

然后逐一检查每个匹配，确认是否是直接返回数据而非 success() 调用。

---

## Task 4: API 文档补齐

**背景：** 路由装饰器缺少 `summary`, `description`, `response_model`，导致 Swagger 页面可读性差。

**要求：** 为路由装饰器补齐：

对于每个端点添加 `summary="..."` 描述端点功能。summary 应该简洁明了，中文或英文均可。

**示例：**
```python
@router.post("/auth/register", 
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
```

**简化方案：** 不要求所有端点都改——先改 5 个最核心的端点作为示范，确认风格：
- cloud/app/auth_router.py: register, login, refresh
- cloud/app/contents_router.py: create content, list contents

**涉及文件：**
- cloud/app/auth_router.py
- cloud/app/contents_router.py

---

## 验收标准

- [ ] 5端 exception handler 使用正确的 ErrorCode（0-7）
- [ ] PaginatedResponse 在所有列表端点中一致使用
- [ ] 裸 dict 返回包装为 success()
- [ ] 核心端点有 summary/description
- [ ] 全项目编译通过
- [ ] 14个测试通过（`rm -f data/test_cloud.db && python -m pytest cloud/app/tests/ -v`）
