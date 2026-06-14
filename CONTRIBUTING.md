# Contributing · BioPulse 开发指南

> 本仓库的生命科学行业 AI 工作台。本文档告诉你如何从零上手、在哪里改代码、以及遵守什么规则。

---

## 一、环境搭建

### 前置条件

```bash
# 系统要求
Python 3.12+
Node.js 18+（前端开发需要）
Flutter 3.24+（移动端开发需要）

# 克隆
git clone <repo-url>
cd biopulse

# 安装后端依赖
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 启动全部服务（6 个终端，或使用 scripts/start_all.sh）
uvicorn cloud.app.main:app --port 8000        # Cloud
uvicorn assistant.app.main:app --port 8003     # Assistant
uvicorn opportunity.app.main:app --port 8002   # Opportunity
uvicorn sales_assistant.app.main:app --port 8004  # Sales-Assistant
uvicorn sales_coach.app.main:app --port 8001   # Sales-Coach
uvicorn pharma_intel.app.main:app --port 8010  # Pharma-Intel（可选）
uvicorn management.app.main:app --port 8011    # Management（可选）
```

### 数据库初始化

```bash
# 自动初始化（首次启动时 main.py 会创建表）
# 或手动运行种子数据
cd cloud && python -c "from app.seeds.seed_s2 import main; main()"

# 重要：每个端使用独立的 SQLite 数据库，位于 data/
# cloud.db, assistant.db, opportunity.db, sales_assistant.db, sales_coach.db
```

---

## 二、如何添加一个新端点

假设你要在 Opportunity 端加一个「线索标签」功能。

### 步骤 1：创建 Service

```python
# opportunity/app/services/tag_service.py
"""线索标签服务：标签 CRUD、批量标记、标签统计。"""

from fastapi import HTTPException
from starlette import status

from opportunity.app.repositories import TagRepository
from opportunity.app.services.base import BaseService


class TagService(BaseService):
    def create_tag(self, name: str, color: str, user_id: int) -> int:
        # 业务逻辑：校验名称唯一性、创建标签
        ...
        return tag_id

    def list_tags(self, user_id: int) -> list:
        return self.db.execute("SELECT * FROM tags WHERE user_id = ?", (user_id,)).fetchall()
```

### 步骤 2：创建 Repository（如果操作新表）

```python
# opportunity/app/repositories/tag_repository.py
"""标签数据仓库：标签表 CRUD 操作。"""

from shared.repository import BaseRepository


class TagRepository(BaseRepository):
    def create(self, name: str, color: str, user_id: int) -> int:
        cursor = self.db.execute(
            "INSERT INTO tags (name, color, user_id) VALUES (?, ?, ?)",
            (name, color, user_id),
        )
        return cursor.lastrowid
```

如果文件超过 300 行 → 拆分（见 ADR-0001）

### 步骤 3：创建 Router

```python
# opportunity/app/tag_router.py
"""标签 API：创建、查询、删除线索标签。"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from opportunity.app.services.tag_service import TagService
from shared.auth import get_current_user
from shared.base import success

router = APIRouter(prefix="/tags", tags=["tags"])


class TagCreate(BaseModel):
    name: str
    color: str = "#6366f1"


@router.post("")
def create_tag(body: TagCreate, user=Depends(get_current_user), svc: TagService = Depends()):
    tag_id = svc.create_tag(body.name, body.color, user["user_id"])
    return success(data={"id": tag_id})
```

### 步骤 4：注册到 main.py

```python
# opportunity/app/main.py 已有约 20 行 import + register
# 在文件末尾附近加入：
from opportunity.app.tag_router import router as tag_router
app.include_router(tag_router)
```

### 步骤 5：运行测试

```bash
source venv/bin/activate
python3 -m pytest opportunity/app/tests/ -v
# 确保 7 passed
```

### 步骤 6：提交

```bash
git add -A
git commit -m "feat(opportunity): 添加线索标签 CRUD"
```

---

## 三、工程规则

### 代码风格（Pre-commit 自动检查）

```bash
# CI 流水线
ruff check → ruff format → [Debug Env] → [Web Build] → [Mobile Analyze] → [Docker] → [Deploy]
```

- Ruff：所有代码通过 ruff check（零 warning）
- 不允许 `E402`（import 不在文件顶部）
- 不允许 `F401`（未使用的 import）
- 不允许 `F841`（未使用的变量）

### 文件大小规则（ADR-0001）

- 每个 `.py` 文件不超过 **300 行**
- 超限：使用 OpenCode 拆分
- 拆分后：跑全量测试验证（ADR-0004）

### 零容忍手动编码（ADR-0002）

- **禁止**手动 write_file/patch 来写代码
- 所有代码变更必须写 `tasks.md` → `opencode run --file tasks.md`
- 只有文档（.md 文件）可以手写

### 代码分层

```
Router（接收请求、校验参数）
   → Service（业务逻辑、编排）
     → Repository（数据访问、SQL）
```

- Router 不写 SQL
- Service 不直接操作数据库
- Repository 不做业务判断
- 每一层通过 FastAPI Depends 注入

### 命名规范

| 项目 | 规范 | 示例 |
|:-----|:-----|:-----|
| 文件 | snake_case | `tag_service.py` |
| 类 | PascalCase | `TagService` |
| 变量/函数 | snake_case | `create_tag()` |
| 路由标签 | 小写复数 | `tags", "opportunity"` |
| 数据库表 | snake_case 复数 | `tags`, `user_bookmarks` |
| Mixin 类 | 必须以 `Mixin` 结尾 | `LoggingMixin` |

### 安全

- 所有 SQL 必须使用参数化查询（`?` 占位符），禁止字符串拼接
- 所有端点必须通过 `Depends(get_current_user)` 鉴权（health_router 除外）
- 不要将敏感配置（API Key、数据库密码）硬编码在代码里

### 软链接说明

以下软链接是项目基础设施，不可删除：
- `sales_assistant/` → `sales-assistant/`（Python import 需要下划线路径）
- `sales_coach/` → `sales-coach/`（同上）

删除会导致 CI 中 ruff I001 全面炸裂。

---

## 四、测试

```bash
# 运行单个端测试
python3 -m pytest opportunity/app/tests/ -v

# 运行全部测试（注意：6 个目录不能同时跑，有 conftest 路径冲突）
python3 -m pytest cloud/app/tests/ -v
python3 -m pytest opportunity/app/tests/ -v
python3 -m pytest assistant/app/tests/ -v
python3 -m pytest sales_assistant/app/tests/ -v
python3 -m pytest sales_coach/app/tests/ -v

# 生成覆盖率报告
python3 -m pytest --cov=cloud.app --cov-report=html
```

测试原则：
- 新增功能必须附带测试
- 修复 bug 的 commit 要附带对应测试（防止回归）
- 不写集成测试，写单元测试（mock 掉外部依赖）

---

## 五、Git 工作流

```bash
# 日常开发
git checkout -b feat/my-feature
# ... 开发 ...
git add -A
git commit -m "feat(scope): 描述"

# 提交信息格式
<type>(<scope>): <subject>

type: feat / fix / refactor / docs / test / chore
scope: cloud / assistant / opportunity / sales-assistant / sales-coach / web / mobile

# 推送到 GitHub
git push origin feat/my-feature
# 创建 PR → CI 通过 → 合并到 main

# 直接推 master（当前工作流）
git push origin master
```

---

## 六、常见问题

### Q: 新加了一个文件但在另一个文件里 import 报错？

- 检查文件名是否是下划线（Python import 需要 snake_case）
- 检查 `__init__.py` 是否导出（如果用 `from .xxx import YYY`）
- 检查是否超过 300 行需要拆分
- 检查是否存在循环 import

### Q: CI 报 ruff I001？

ruff I001 表示 import 顺序不对。`ruff format` 会自动修复。如果是在 sales-assistant 端报的，检查 softlink `sales_assistant/` 是否存在。

### Q: Cloud 启动报 `ModuleNotFoundError`？

Cloud 路由模块很多（290+），通过 `main.py` 统一注册。新加路由后必须在 `main.py` 中 `include_router`。如果某路由文件删了，`main.py` 的 import 也要同步删除。

### Q: 数据库在哪？

```bash
ls -la data/
# cloud.db  assistant.db  opportunity.db  sales_assistant.db  sales_coach.db
```

每个端独立。删除会自动重建（`database.py` 中有 `CREATE TABLE IF NOT EXISTS`）。
