# Layer: mdt_engine_router.py

## 编码准则

1. Think Before Coding — 已读取源文件
2. Simplicity First — 新建1个service文件，router改为委托调用
3. Surgical Changes — 只改1个router+新建1个service
4. Goal-Driven — 移除get_db依赖，测试全过
5-15. 保持架构不变
16. 必须用opencode写代码 ✅
17. 启动规则(write→TG→confirm) ✅ 已确认
18. 完整准则写入每个tasks.md ✅

## 背景

`cloud/app/mdt_engine_router.py` 当前202行。包含：
- 3个工具函数：`_now()`, `_call_ai()`, `_parse_json()`
- 6个端点：create_session, list_sessions, get_session, debate, consensus, get_opinions, timeline, dashboard
- 直接使用4个Repository：MdtSessionsRepository, MdtParticipantsRepository, MdtOpinionsRepository, AgentRolesRepository
- 依赖 `db=Depends(get_db)`

## Step 1：新建 Service 文件

创建 `cloud/app/services/mdt_engine_service.py`，内容要求：

1. 类名 `MdtEngineService`
2. 构造方法 `__init__(self, db=Depends(get_db)): self.db = db`
3. 工具方法（从 router 原样搬过来）：
   - `_now()` → 静态方法，返回当前时间字符串
   - `_parse_json(raw, default)` → 静态方法，安全 JSON 解析
   - `_call_ai(messages, auth_header)` → 静态方法，调用 AI 网关
4. 业务方法（每个端点对应一个方法，从 router 搬逻辑）：
   - `create_session(body, uid) → dict` — 创建 MDT 会诊，返回 id/title/participant_count
   - `list_sessions(status_filter, page, page_size) → dict` — 分页列表
   - `get_session(session_id) → dict` — 获取 session + participants + opinions，不存在则 404
   - `debate(session_id, max_rounds, auth_header) → dict` — 辩论循环，逐轮收集各方观点
   - `consensus(session_id, auth_header) → dict` — AI 生成共识报告
   - `get_opinions(session_id, round_number) → list` — 按轮次过滤观点
   - `timeline(session_id) → dict` — 时间线数据
   - `dashboard() → dict` — 统计数据
5. import 从 router 文件原样复制（`json`, `urllib.request`, `datetime`, `fastapi`, `cloud.app.repositories` 等）
6. `ParticipantDef` 是 router 中的 Pydantic model，service 的 `create_session` 直接引用它（用 `from cloud.app.mdt_engine_router import ParticipantDef` 延迟导入避免循环依赖）

## Step 2：修改 Router 文件

对 `cloud/app/mdt_engine_router.py`：

1. 删除 `from cloud.app.database import get_db` 导入
2. 添加 `from cloud.app.services.mdt_engine_service import MdtEngineService`
3. 删除工具函数 `_now()`, `_call_ai()`, `_parse_json()`（已移到 service）
4. 每个端点的 `db=Depends(get_db)` 参数改为 `service: MdtEngineService = Depends()`
5. 端点体内的逻辑替换为调用 `service.xxx(...)` 方法
6. 保留 Pydantic model 定义（ParticipantDef, SessionCreate, DebateRequest）
7. 保留 `router = APIRouter(...)` 行

## 验收

1. `python3 -c "import ast; ast.parse(open('cloud/app/mdt_engine_router.py').read()); print('OK')"` → OK
2. `python3 -c "import ast; ast.parse(open('cloud/app/services/mdt_engine_service.py').read()); print('OK')"` → OK
3. `python -m pytest cloud/app/tests/test_mdt.py -x -q --no-cov` → 13 passed
4. `python -m pytest cloud/app/tests/ -x -q --no-cov` → 153 passed
