# 一云四端 · 系统架构

> 生命科学行业全场景 AI 工作台架构文档
> 对应 commit: `4e3f620` (2026-06-06) | 代码行数: ~21,500 | 文件数: 396

---

## 一、总览

```
                    ┌─────────────────────────────────────────────────────────┐
                    │                     Cloud (8000)                        │
                    │  引擎层：Agent Runtime · MCP · MDT · 知识图谱 · 记忆    │
                    │  数据层：Auth · Compliance · 事件总线 · 联邦学习         │
                    └────────────┬───────────┬───────────┬────────────────────┘
                                │           │           │
                    ┌───────────┘   ┌───────┴───────┐   └───────────┐
                    ▼               ▼               ▼               ▼
             ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
             │Assistant │   │Opportunity│  │Sales-    │   │Sales-    │
             │  (8003)  │   │  (8002)   │  │Assistant │   │  Coach   │
             │跟台助手   │   │ 商机挖掘   │  │ (8004)   │   │  (8001)  │
             └──────────┘   └──────────┘  │销售助理   │   │销售教练   │
                                          └──────────┘   └──────────┘
                    ┌──────────┐   ┌──────────┐
                    │ Pharma   │   │Management│
                    │ Intel    │   │ 管理端    │
                    │制药情报   │   └──────────┘
                    └──────────┘
                    ┌──────────┐   ┌──────────┐   ┌──────────┐
                    │   Web   │   │  Mobile  │   │ Frontend │
                    │ React   │   │  Flutter │   │ (legacy) │
                    └──────────┘   └──────────┘   └──────────┘
```

**核心原则：一云厚、四端专**

- **Cloud**（端口 8000）：承载全量业务引擎，不直接面向用户
- **四端**（端口 8001-8004）：每个端是独立 FastAPI 应用，专注一个场景
- **扩展端**：Pharma-Intel（制药情报）、Management（管理员后台）
- **Web/Mobile**：React 和 Flutter 前端，消费 Cloud 和四端的 API
- 端与端之间**不直接通信**，都通过 Cloud 做数据和服务中枢

---

## 二、分层的包架构（每端通用）

每个端内部遵循三层分离：

```
app/
├── routers/          # 路由层：接收请求 → 校验参数 → 调用 Service → 返回响应
├── services/         # 服务层：业务逻辑编排 → 调用 Repository → 处理异常
├── repositories/     # 仓库层：执行 SQL → 返回数据对象
├── schemas/          # Pydantic 模型（定义请求/响应结构）
└── main.py           # FastAPI 应用入口（注册路由、中间件、启动事件）
```

**数据流：**
```
HTTP Request → Router（校验）→ Service（逻辑）→ Repository（SQL）→ Database
                    ↑         → 异常   → HTTPException     → JSONResponse
```

### 路由层（Router）

- 每个端有多个 `*_router.py` 文件，按功能域拆分
- 职责：参数校验（Pydantic）→ 调用 Service → 统一响应格式
- 不包含业务逻辑（那属于 Service）
- 通过 `Depends(get_current_user)` 做认证

### 服务层（Service）

- 每个端有 `services/` 目录，继承 `BaseService`
- `BaseService` 通过 FastAPI `Depends` 注入数据库连接
- 职责：业务逻辑编排、跨 Repository 的事务协调、异常包装
- 不直接感知 HTTP 层（不引用 Request/Response 对象）

### 仓库层（Repository）

- 每个端有 `repositories/` 目录，部分端使用单个 `repositories.py`
- 职责：纯数据访问，一个类只操作一张或一类表
- 方法签名：`get_*`（查询单条）→ `list_*`（查询列表）→ `create_*`→ `update_*`→ `delete_*`
- 不包含业务逻辑，不应跨表编排

### 工程约束

- **文件不超过 300 行**（ADR-0001）：超限必须拆分
- **零容忍手动编码**（ADR-0002）：所有代码变更必须通过 OpenCode
- **独立数据库**（ADR-0003）：每端有自己独立的 SQLite 文件
- **Mixin 与独立类命名区隔**（ADR-0005）：Mixin 类名以 `Mixin` 结尾

---

## 三、服务通信

### 端 → Cloud（REST）

- 各端通过 HTTP 调用 Cloud 的 API（通常是 localhost:8000）
- 认证：JWT Token（所有端共享同一 auth 系统）
- 失败处理：各端独立降级，不因 Cloud 不可用而崩溃

### Cloud → 端（无直接反向调用）

- Cloud 不主动调用各端
- 异步通知通过事件总线（`event_bus_router.py` + `event_bus_service.py`）实现
- 事件总线目前是内存队列 + SQLite 持久化

### 离线模式

- 移动端（Flutter）本地 SQLite + 定时同步
- JWT 本地解码：Cloud 停机时四端仍可验证用户身份
- 同步端点：`sync_router.py` / `offline_router.py`

---

## 四、AI Agent 架构

```
                         ┌─────────────────────────┐
                         │     Agent Runtime Core    │
                         │  (cloud/app/agent_runtime/) │
                         └────────────┬────────────┘
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          ▼                           ▼                           ▼
┌──────────────────┐     ┌──────────────────────┐     ┌──────────────────┐
│    Planner        │     │    Loop Detector      │     │     Validator    │
│  任务拆解 → 子任务  │     │   循环检测 + 终止      │     │   输出校验 + 重试  │
└──────────────────┘     └──────────────────────┘     └──────────────────┘
          ▼                           ▼                           ▼
┌──────────────────┐     ┌──────────────────────┐     ┌──────────────────┐
│    Verifier       │     │     Reflector         │     │   State Snapshot  │
│  结果验证 → 通过/否  │     │    反思 → 调整策略     │     │   检查点 + 恢复    │
└──────────────────┘     └──────────────────────┘     └──────────────────┘
```

### 核心组件（`cloud/app/agent_runtime/`）

| 文件 | 类 | 职责 |
|:-----|:---|:-----|
| `planner.py` | `TaskPlanner` | 将用户目标拆解为可执行的子任务序列 |
| `verifier.py` | `AgentVerifier` | 验证 LLM 输出是否达到任务目标 |
| `reflector.py` | `Reflector` | 分析执行历史，调整后续策略 |
| `analyzer.py` | `AgentAnalyzer` | 分析 Agent 执行表现和失败模式 |
| `loop_detector.py` | `LoopDetector` | 检测循环重复，防止无限循环 |
| `guard.py` | `GuardRail` | 输入端安全过滤和输出端合规检查 |
| `pipeline.py` | `AgentPipeline` | 编排 Agent 执行管线（计划→执行→验证→反思） |
| `runtime_core.py` | `AgentRuntime` | 运行时核心，协调所有子组件 |
| `runtime_state.py` | `CheckpointManager` / `ApprovalManager` | 运行时状态管理 |
| `queue_manager.py` | `AgentQueueManager` | 任务队列与并发控制 |
| `scheduler.py` | `AgentScheduler` | 定时调度和重试策略 |
| `tool_bridge.py` | `ToolRegistry` | 工具注册与调用桥（MCP 协议） |
| `cost_governor.py` | `CostGovernor` | Token 预算控制和成本约束 |
| `validator.py` | `AgentOutputValidator` | LLM 输出结构化验证 |
| `notifier.py` | `AgentNotifier` | 运行状态通知（WebSocket / 轮询） |
| `state_snapshot.py` | `SnapshotManager` | 执行状态快照与恢复 |
| `retry.py` | — | 指数退避重试逻辑 |
| `models.py` | — | Agent 数据模型（Pydantic） |
| `memory.py` | — | Agent 运行时记忆接口 |

### MCP 工具总线

```
Agent Runtime → ToolRegistry (tool_bridge.py) → MCP Router → 各端 Service
```

- 280+ 端点统一注册在 `mcp_router.py` / `mcp_tool_service.py`
- 工具调用经过 `mcp_guard_service.py` 安全校验
- `cloud/app/agent_framework_router.py` — 框架兼容层

### 记忆系统（`cloud/app/services/memory_*.py`）

| 服务 | 职责 |
|:-----|:-----|
| `memory_gate_service.py` | 记忆门控 — 信息筛选进入 LTM 的开关 |
| `memory_consolidation_service.py` | 记忆巩固 — 短期 → 长期转化 |
| `memory_utility_service.py` | 记忆效用 — 基于使用频率的衰减/强化 |
| `unified_memory_service.py` | 统一记忆 — 跨端记忆聚合 |
| `memory_retriever.py` | 记忆检索 — 语义/时序混合检索 |
| `memory_writer.py` | 记忆写入 — 结构化存储 |
| `sage_engine_service.py` | SAGE — 自进化记忆引擎 |
| `world_tree_service.py` | 世界树 — 知识分层存储 |
| `brain_memory_service.py` | 大脑记忆 — 认知架构 |
| `brain_orchestrator_service.py` | 大脑编排 — 记忆调度 |

### 因果推理引擎

| 服务 | 职责 |
|:-----|:-----|
| `causal_service.py` / `causal_attribution_service.py` | 因果归因分析 |
| `attribution_calc.py` / `attribution_check.py` | 归因评分计算与校验 |
| `decision_logger.py` / `decision_intel_service.py` | 决策日志与智能分析 |

### MDT 多专家会诊（`cloud/app/services/mdt_*.py`）

| 服务 | 职责 |
|:-----|:-----|
| `mdt_agent_service.py` | MDT Agent 管理 |
| `mdt_debater.py` | 多角色 LLM 辩论引擎 |
| `mdt_engine_service.py` | MDT 引擎 — 辩论流程编排 |
| `mdt_resolver.py` | 共识生成与分歧解决 |

---

## 五、安全与合规

### 认证体系

- JWT Token 认证，共享 `shared/auth.py`
- 所有端点通过 `Depends(get_current_user)` 做保护
- health_router 和部分开放端点免认证

### 合规引擎

| 文件 | 职责 |
|:-----|:-----|
| `compliance_router.py` | 合规规则查询与管理 |
| `compliance_v2_router.py` / `compliance_v2_service.py` | 合规 v2 — 决策链 SHA256 审计 |
| `compliance_v2_evaluator.py` / `compliance_v2_report.py` | 合规评估与报告 |
| `compliance_enforcer.py` / `compliance_enforcer_engine.py` | 合规强制 — 规则预执行拦截 |

---

## 六、项目结构

```
one-cloud-four-ends/
├── cloud/                    # Cloud 核心服务（280+ 文件 / 290 路由模块）
│   ├── app/
│   │   ├── main.py          # 应用入口，注册所有路由
│   │   ├── agent_runtime/   # Agent 运行时（17 文件）
│   │   ├── services/        # 业务服务（95 文件）
│   │   ├── repositories/    # 数据仓库（21 文件）
│   │   ├── routers/         # 扩展路由（24 文件）
│   │   └── seeds/           # 种子数据（30 文件）
│   ├── langgraph/           # LangGraph 集成
│   ├── shared/              # 公共组件（columns/repository）
│   └── rules/               # 合规规则加载
├── assistant/               # 跟台助手（36 文件）
│   └── app/
│       ├── routers/*        # API 路由
│       ├── services/*       # 业务服务
│       └── repositories.py  # 数据仓库
├── opportunity/             # 商机挖掘（33 文件）
│   └── app/
│       ├── routers/*        # API 路由
│       ├── services/*       # 业务服务
│       └── repositories/    # 数据仓库（独立文件）
├── sales-assistant/         # 销售助理（28 文件）
│   └── app/
│       ├── routers/*        # API 路由
│       ├── services/*       # 业务服务
│       └── repositories.py  # 数据仓库
├── sales-coach/             # 销售教练（33 文件）
│   └── app/
│       ├── routers/*        # API 路由
│       ├── services/*       # 业务服务
│       └── repositories.py  # 数据仓库
├── pharma_intel/            # 制药情报（17 文件）
├── management/              # 管理端（12 文件）
├── web/                     # React 前端
├── mobile_app/              # Flutter 移动端
├── frontend/                # 前端（临时/早年方案）
├── design-tokens/           # 设计系统 Token
├── deploy/                  # 部署配置
├── scripts/                 # 辅助脚本
├── briefings/               # 设计文档（不进 git）
└── docs/adr/                # 架构决策记录（不进 git）
```

---

## 七、技术栈

| 层 | 技术 |
|:---|:-----|
| **后端运行时** | Python 3.12 / FastAPI / uvicorn |
| **数据库** | SQLite（当前）/ PostgreSQL（规划中） |
| **AI 模型** | DeepSeek / 通过 AI Gateway 接入 |
| **Agent 框架** | 自研 Harness（Validator / LoopDetector / Pipeline / RuntimeCore） |
| **前端** | React 18 / Vite 6 / Tailwind CSS |
| **移动端** | Flutter / Dart / Provider / SQLite (offline-first) |
| **CI** | GitHub Actions（Ruff check → Debug → Web build → Mobile analyze → Docker） |
| **部署** | 腾讯云东京 2C4G / systemd 服务 / UFW 防火墙 |

---

## 八、部署架构

```
腾讯云 (43.153.166.191)
├── SSH (62222, key-only)
├── Cloud → uvicorn :8000  (systemd: cloud-api.service)
├── Assistant → uvicorn :8003
├── Opportunity → uvicorn :8002
├── Sales-Coach → uvicorn :8001
├── Sales-Assistant → uvicorn :8004
├── Hermes 网关 (18789)
└── UFW: 仅放行 62222 / 限内部端口开放

数据库：独立 SQLite 文件存储在 data/
```

---

## 九、关键 ADR 索引

| 编号 | 决策 | 详情 |
|:----|:-----|:-----|
| ADR-0001 | 文件不超过 300 行 | 超限必须自动拆分 |
| ADR-0002 | 零容忍手动编码 | 所有代码变更走 OpenCode |
| ADR-0003 | 独立数据库 | 每端独立 SQLite，Cloud 不共享 |
| ADR-0004 | 拆分后全量测试 | 大文件拆分后必须跑全量测试验证 |
| ADR-0005 | Mixin 命名区隔 | Mixin 类名以 Mixin 结尾，与独立类区分 |
| ADR-0006 | Vibecoding 工作流 | Write→TG→Confirm→OpenCode |
| ADR-0007 | 拆分后全量测试 | 与 ADR-0004 配套 |
| ADR-0008 | Class 命名规范 | 同类名不可混淆 |

完整 ADR 见 `docs/adr/README.md`
