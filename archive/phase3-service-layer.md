# Phase 3: Service 层引入 — 试点

## 背景

当前架构：Router → Repository（直调）
改造目标：Router → Service → Repository（分层）

**为什么 Service 层：**
- 路由只做：参数校验 + 调 Service + 返回响应
- Service 做：业务逻辑编排 + 事务管理 + 异常处理
- 以后 PG 迁移只需要改 Repository 层，Service 和 Router 不受影响

## 试点范围

先对 Cloud 端 **3 个核心路由**做 Service 层引入作为试点：
1. `auth_router.py` — 注册/登录/刷新
2. `users_router.py` — 用户CRUD
3. `contents_router.py` — 内容CRUD+合规检查

确认模式正确后再全量铺开。

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

## Task 1: 创建 Service 层基类

**新建文件：** `cloud/app/services/__init__.py` 和 `cloud/app/services/base.py`

**base.py 内容：**
```python
from fastapi import Depends
from cloud.app.database import get_db

class BaseService:
    def __init__(self, db=Depends(get_db)):
        self.db = db
```

提供基础依赖注入支持。所有 Service 类继承 BaseService。

---

## Task 2: 创建 AuthService

**新建文件：** `cloud/app/services/auth_service.py`

**从 `auth_router.py` 中提取的业务逻辑：**
- `register()`: 用户名长度校验、密码长度校验、检查重名、密码哈希、创建用户、返回 user_id
- `login()`: 根据用户名查用户、验证密码、生成 access_token + refresh_token
- `refresh()`: 验证 refresh_token、生成新 access_token、返回 token

**方法签名示例：**
```python
class AuthService(BaseService):
    def register(self, username: str, password: str) -> dict:
        # 校验 + 业务逻辑
        ...
        return {"user_id": user_id, "username": username}
    
    def login(self, username: str, password: str) -> dict:
        ...
        return {"access_token": ..., "refresh_token": ..., "token_type": "bearer"}
    
    def refresh(self, refresh_token: str) -> dict:
        ...
        return {"access_token": ..., "token_type": "bearer"}
```

---

## Task 3: 创建 UserService

**新建文件：** `cloud/app/services/user_service.py`

**从 `users_router.py` 中提取的业务逻辑：**
- `list_users()`: 分页查询用户列表
- `get_user()`: 按 ID 获取用户
- `update_user()`: 更新用户信息（列名校验）
- `delete_user()`: 软删除用户

---

## Task 4: 创建 ContentService

**新建文件：** `cloud/app/services/content_service.py`

**从 `contents_router.py` 中提取的业务逻辑：**
- `create_content()`: 创建内容 + 合规检查 + 自动通知
- `get_content()`: 按 ID 获取内容
- `update_content()`: 更新内容 + 重新合规检查
- `delete_content()`: 软删除内容
- `list_contents()`: 分页查询内容列表

注意：合规检查和通知是这里的核心业务逻辑。

---

## Task 5: 改造 auth_router.py

**修改文件：** `cloud/app/auth_router.py`

改造后：
```python
from cloud.app.services.auth_service import AuthService

@router.post("/register", ...)
def register(body: RegisterRequest, service: AuthService = Depends()):
    result = service.register(body.username, body.password)
    return success(data=result)

@router.post("/login", ...)
def login(body: LoginRequest, service: AuthService = Depends()):
    result = service.login(body.username, body.password)
    return success(data=result)

@router.post("/refresh", ...)
def refresh(body: RefreshRequest, service: AuthService = Depends()):
    result = service.refresh(body.refresh_token)
    return success(data=result)
```

---

## Task 6: 改造 users_router.py

**修改文件：** `cloud/app/users_router.py`

改造后：
```python
from cloud.app.services.user_service import UserService

@router.get("/users/")
def list_users(page=Query(1), page_size=Query(20), service: UserService = Depends()):
    return service.list_users(page, page_size)

@router.get("/users/{user_id}")
def get_user(user_id: int, service: UserService = Depends()):
    return service.get_user(user_id)
...
```

---

## Task 7: 改造 contents_router.py

**修改文件：** `cloud/app/contents_router.py`

改造后类似——所有业务逻辑移到 ContentService，router 只做编排。

---

## 验收标准

- [ ] `cloud/app/services/` 目录存在，包含 `__init__.py`, `base.py`, `auth_service.py`, `user_service.py`, `content_service.py`
- [ ] auth_router.py 使用 AuthService
- [ ] users_router.py 使用 UserService
- [ ] contents_router.py 使用 ContentService
- [ ] 全项目编译通过
- [ ] Cloud 端 42 个测试通过
- [ ] 其他4端测试通过（不受影响）
