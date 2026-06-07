# 一云四端 · 代码执行清单

> 基于全面代码审计（647文件 / 72,611行）整理
> 只做代码，不做客户验证，CI已就绪

---

## P0 — 必须修

### P0-1 拆分 runtime_core.py（641行 → ≤300行）
- **路径**: `cloud/app/agent_runtime/runtime_core.py`
- **问题**: 超过第14条准则（≤300行）2倍。`execute()` 方法 ~400行内联逻辑，含状态管理/成本追踪/回滚/日志混在一起
- **方案**: 将 `_execute_step()`、`_save_checkpoint()`、`_save_log()`、`_handle_failure()`、`_handle_budget_exceeded()` 等提取为独立方法
- **风险**: 高 — 核心执行引擎，改完必须全量回归测试（421 passed）

### P0-2 补 `__init__.py` 接口暴露（2个空文件）
- **路径**: `cloud/app/agent_runtime/__init__.py`（0字节空）
- **路径**: `cloud/app/services/__init__.py`（0字节空）
- **问题**: 空文件不暴露任何接口，外部全靠硬 import 完整路径
- **方案**: 显式导入公开类（`from .runtime_core import AgentRuntime` 等）

### P0-3 替换 `import *` 为显式导入（2个文件）
- **路径**: `shared/columns/__init__.py`（27个 `from .X import *`）
- **路径**: `cloud/shared/columns/__init__.py`（6个 `from .X import *`）
- **问题**: 无 `__all__` 控制，命名空间完全污染
- **方案**: 替换为 `from .X import A, B, C` + `__all__` 白名单

---

## P1 — 高优

### P1-1 拆分超过300行的测试文件（6个）
| 文件 | 行数 |
|------|:---:|
| `cloud/app/tests/test_cloud_api.py` | 1226 |
| `cloud/app/tests/test_mdt.py` | 405 |
| `cloud/app/tests/test_cloud_agents.py` | 405 |
| `cloud/app/tests/test_agents.py` | 399 |
| `cloud/app/tests/test_repositories.py` | 327 |
| `cloud/app/services/event_bus_service.py` | 372 |

- **方案**: test 文件按功能拆分子文件（`test_cloud_auth.py`、`test_cloud_compliance.py` 等），`event_bus_service.py` 按后端类型拆

### P1-2 统一命名不一致（Agent Runtime 14个文件 + Services）

**Agent Runtime（全部不一致）：**
| 文件名 | 当前主类 | 应改为 |
|--------|---------|-------|
| `analyzer.py` | `Analysis` | `Analyzer` |
| `guard.py` | `Layer` / `Layer1Filter` | `Guard` |
| `planner.py` | `PlanStep` | `Planner` |
| `verifier.py` | `CheckResult` | `Verifier` |
| `reflector.py` | `ReflectionResult` | `Reflector` |
| `memory.py` | `AgentBrain` | `Memory` |
| `state_snapshot.py` | `SnapshotManager` | `StateSnapshot` |
| `runtime_core.py` | `AgentRuntime` | `RuntimeCore` |
| `runtime_state.py` | `CheckpointManager` | `RuntimeState` |
| `tool_bridge.py` | `ToolRegistry` | `ToolBridge` |
| `validator.py` | `AgentOutputValidator` | `Validator` |
| `models.py` | `ToolDef` | `Models` |
| `notifier.py` | `AgentNotifier` | `Notifier` |
| `pipeline.py` | `PipelineStep` | `Pipeline` |

**Services（高优先）：**
| 文件 | 当前主类 | 问题 |
|------|---------|------|
| `a2a_registry_service.py` | `A`（单字母） | 🔴 极其难维护 |
| `compliance_v2_service.py` | `ComplianceV` | 类名截断 |

### P1-3 统一硬编码 URL 到 config（约12处）
- **问题**: `{cloud_api_base}/ai/chat` 在各 runtime 模块中作为 `__init__` 默认参数分散硬编码
- **涉及文件**: `analyzer.py`、`planner.py`、`verifier.py`、`runtime_llm.py`、`pipeline.py`、`tool_bridge.py` + 约6个 services
- **方案**: 统一走 `shared/config.py` 的 `settings`，不在 `__init__` 默认参数里硬编码

### P1-4 合并 compliance 四文件
- **路径**: `compliance_enforcer.py` / `engine` / `audit` / `strategy_service`
- **问题**: 四文件功能高度耦合，约200行冗余
- **方案**: 合并为一个 `compliance_engine.py`（≤300行）

---

## P2 — 清理与优化

### P2-1 删除安全可删的文件
| 文件 | 原因 |
|------|------|
| `cloud/app/main.py.orig` | 旧备份 |
| `cloud/app/agent_runtime/models/distilbert/.gitkeep` | 空占位 |
| `cloud/app/services/research_trajectory_features.py` | 纯 re-export（6行） |
| 3个空 `__init__.py` | agent_runtime / services / tests |

### P2-2 Mock 数据清理（前置任务）
- **问题**: `frontend/src/mock/` 6个文件全部活跃，`frontend/src/pages/admin/` 下 **13+页面内联 mock 在组件中**，不经过 API 层
- **方案**: 先将内联 mock 提取到 mock/ 目录统一管理，后续对接真实 API 时再删除

### P2-3 Front-end mock API 层分离
- 将 admin/president/、manager/、employee/ 下13+页面的内联 mock 数据抽到独立 mock 文件
- 每个页面加 API 调用路径，降级为 try-api → fallback mock
- 清掉 mock 后这些页面才可对接真实后端

---

## P3 — 设计文档同步

### P3-1 更新 §8.12 实现状态表
- 10处「🟡 待实现」→「✅ 已实现」
- Agent 系统、成本追踪、SafetyGuard Layer3、状态快照/回滚

### P3-2 更新 §6.4 代码规模
- 271文件/31,893行 → 647文件/71,942行
- Cloud 138文件 → 367文件（超设计目标104%）

### P3-3 更新 §12 设计与代码差距
- 整章过期，需重写
- Agent 系统标注「待实现」→ 已全部实现
- 双主线隔离标注「未开始」→ 已完整实现

---

## 总优先级建议

```
Round 1: P0-1（runtime_core 拆分）+ P0-2（__init__.py 补全）
  ↓
Round 2: P0-3（import * 清理）+ P1-2（命名统一）
  ↓
Round 3: P1-1（测试文件拆分）+ P1-3（硬编码统一）
  ↓
Round 4: P1-4（compliance 合并）+ P2-1（删安全文件）
  ↓
Round 5: P2-2（Mock 清理前置）+ P2-3（API 层分离）
  ↓
Round 6: P3-1 ~ P3-3（设计文档同步）
```
