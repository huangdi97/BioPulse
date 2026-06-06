# Exec-015 · 超大文件拆分（7文件 → ~50文件）

## 编码准则（完整18条）
1. Think Before Coding 2. Simplicity First 3. Surgical Changes 4. Goal-Driven Execution 5. 架构优先拒绝补丁 6. 面向组件构建 7. 显式优于隐式 8. 代码整洁自文档化 9. 单一职责 10. 组合优于委托 11. 单一状态源 12. 避免语法糖 13. 命名一致性 14. 文件不超过300行 15. 低耦合(模块间只传ID) 16. 必须用opencode写代码 17. 启动规则(write→TG→confirm→opencode) 18. 完整准则写入每个tasks.md不可省略

## 一、总览

| # | 文件 | 当前行数 | 拆分方案 | 产出文件数 |
|:---|:---|:---:|:---|:---:|
| 1 | `shared/columns.py` | 1943 | 转 package，按领域拆分 | ~16 个 files |
| 2 | `cloud/app/schema.py` | 1308 | 转 package，按领域拆分 | ~12 个 files |
| 3 | `cloud/app/agent_runtime/runtime_core.py` | 596 | 提取 helpers 到独立模块 | ~3 个 files |
| 4 | `sales-coach/app/scenario_builder.py` | 426 | 提取权重数据到独立模块 | ~2 个 files |
| 5 | `sales-assistant/app/database.py` | 385 | 提取 SCHEMA SQL 到独立文件 | ~2 个 files |
| 6 | `assistant/app/database.py` | 378 | 提取 SCHEMA SQL 到独立文件 | ~2 个 files |
| 7 | `opportunity/app/database.py` | 325 | 提取 SCHEMA SQL 到独立文件 | ~2 个 files |

---

## 二、Batch 1：`shared/columns.py` package 化

### 方案

将 `shared/columns.py` 转为 `shared/columns/` 包，内部按领域分文件，`__init__.py` 统一 re-export。

**重要：** 保持所有现有 `from shared.columns import TABLE_XXX_COLS` 导入不变。

### 子文件清单

| 文件 | 内容 | 预估行数 |
|:---|:---|:---:|
| `shared/columns/__init__.py` | re-export 所有 `TABLE_*_COLS` 符号 | ~20 |
| `shared/columns/auth.py` | users, api_tokens, teams, user_team, system_configs | ~120 |
| `shared/columns/audit.py` | audit_logs, audit_chain_entries, compliance_audit_records, training_corrections | ~130 |
| `shared/columns/content.py` | contents, compliance_rules, notification_templates, notifications | ~130 |
| `shared/columns/customer.py` | customers, customer_interactions, opportunities | ~100 |
| `shared/columns/market.py` | market_intel_sources, market_intel_items | ~80 |
| `shared/columns/task.py` | task_boards, board_tasks | ~60 |
| `shared/columns/agent.py` | agent_roles, agent_pipelines, pipeline_steps, pipeline_runs, pipeline_step_runs | ~200 |
| `shared/columns/decision.py` | decision_cases, causal_analyses, cross_case_insights, causal_graphs, counterfactual_scenarios | ~200 |
| `shared/columns/mdt.py` | mdt_sessions, mdt_participants, mdt_opinions, async_mdt_opinions | ~180 |
| `shared/columns/memory.py` | memory_gates, memory_entries, memory_recall_log, memory_utility_scores, sleep_consolidation_logs, working_memory, episodic_memory, memory_consolidation_log | ~300 → 若超则再拆 |
| `shared/columns/worldtree.py` | world_tree_nodes, node_memory_links, world_tree_snapshots | ~100 |
| `shared/columns/route.py` | route_rules, route_logs, route_stats | ~130 |
| `shared/columns/hcp.py` | hcp_profiles, hcp_interactions, hcp_simulations | ~130 |
| `shared/columns/training.py` | training_modules, training_sessions, training_attributions, training_scripts, training_roi_analysis | ~250 |
| `shared/columns/soap.py` | soap_templates, soap_decisions | ~120 |
| `shared/columns/did.py` | did_registry, vc_credentials, fed_audit_contributions, privacy_budgets, data_masking_rules, dp_audit_log, privacy_compute_jobs, federated_rounds | ~300 |
| `shared/columns/kg.py` | kg_entities, kg_relations, kg_search_cache | ~120 |
| `shared/columns/userprofile.py` | user_profiles, user_behaviors, recommendations | ~130 |
| `shared/columns/collab.py` | agent_skills, collaboration_sessions, collaboration_steps | ~200 |
| `shared/columns/eventbus.py` | event_bus_definitions, event_bus_messages, event_delivery_log | ~200 |
| `shared/columns/exec.py` | agent_execution_tasks, mcp_tools, mcp_audit_log, orchestration_templates | ~250 |
| `shared/columns/misc.py` | agent_marketplace, supply_chain_items, sensor_sessions, effect_metrics, benchmark_reports | ~200 |
| `shared/columns/end_assistant.py` | assistant_hcp, visit_record, task, health_radar, surgery_reminder | ~200 |
| `shared/columns/end_sales_assistant.py` | schedule, meeting_note, content_library, strategy_simulation | ~100 |

### 验收标准

- `from shared.columns import TABLE_USERS_COLS` 依旧正常导入
- 每个子文件不超过 300 行
- 项目测试全部通过
- 没有新增 import 断链

---

## 三、Batch 2：`cloud/app/schema.py` package 化

### 方案

将 `cloud/app/schema.py` 转为 `cloud/app/schema/` 包。所有子文件中的 SQL 字符串拼接为一个 `SCHEMA_SQL`。

**改动点：** `cloud/app/database.py` 中 ``from cloud.app.schema import SCHEMA_SQL`` 不变。
**改动点：** `cloud/app/tests/conftest.py` 中 `from cloud.app.schema import SCHEMA_SQL` 不变。

### 子文件清单（与 columns 子文件一一对应）

| 文件 | 内容 | 预估行数 |
|:---|:---|:---:|
| `cloud/app/schema/__init__.py` | 导入各子模块 SQL 片段并拼接 | ~20 |
| `cloud/app/schema/auth.py` | users, api_tokens, teams, user_team, system_configs | ~30 |
| `cloud/app/schema/audit.py` | audit_logs, audit_chain_entries, compliance_audit_records, training_corrections | ~30 |
| `cloud/app/schema/content.py` | contents, compliance_rules, notification_templates, notifications | ~12 |
| `cloud/app/schema/customer.py` | customers, customer_interactions, opportunities | ~35 |
| `cloud/app/schema/market.py` | market_intel_sources, market_intel_items | ~30 |
| `cloud/app/schema/task.py` | task_boards, board_tasks | ~20 |
| `cloud/app/schema/agent.py` | agent_roles, agent_pipelines, pipeline_steps, pipeline_runs, pipeline_step_runs | ~60 |
| `cloud/app/schema/decision.py` | decision_cases, causal_analyses, cross_case_insights, causal_graphs, counterfactual_scenarios | ~30 |
| `cloud/app/schema/mdt.py` | mdt_sessions, mdt_participants, mdt_opinions, async_mdt_opinions | ~40 |
| `cloud/app/schema/memory.py` | memory_gates, memory_entries, memory_recall_log, memory_utility_scores, sleep_consolidation_logs, working_memory, episodic_memory, memory_consolidation_log | ~80 |
| `cloud/app/schema/worldtree.py` | world_tree_nodes, node_memory_links, world_tree_snapshots | ~45 |
| `cloud/app/schema/route.py` | route_rules, route_logs, route_stats | ~30 |
| `cloud/app/schema/hcp.py` | hcp_profiles, hcp_interactions, hcp_simulations | ~50 |
| `cloud/app/schema/training.py` | training_modules, training_sessions, training_attributions, training_scripts, training_roi_analysis | ~65 |
| `cloud/app/schema/soap.py` | soap_templates, soap_decisions | ~25 |
| `cloud/app/schema/did.py` | did_registry, vc_credentials, fed_audit_contributions, privacy_budgets, data_masking_rules, dp_audit_log, privacy_compute_jobs, federated_rounds | ~95 |
| `cloud/app/schema/kg.py` | kg_entities, kg_relations, kg_search_cache | ~35 |
| `cloud/app/schema/userprofile.py` | user_profiles, user_behaviors, recommendations | ~40 |
| `cloud/app/schema/collab.py` | agent_skills, collaboration_sessions, collaboration_steps | ~35 |
| `cloud/app/schema/eventbus.py` | event_bus_definitions, event_bus_messages, event_delivery_log | ~50 |
| `cloud/app/schema/exec.py` | agent_execution_tasks, mcp_tools, mcp_audit_log, orchestration_templates | ~85 |
| `cloud/app/schema/misc.py` | agent_marketplace, supply_chain_items, sensor_sessions, effect_metrics, benchmark_reports, nmpa_compliance_logs | ~100 |

**不包含** end-specific 的 schema（assistant/sales-assistant/opportunity 各端有各自的 `database.py` 处理自己独立的表）。

### 验收标准

- `from cloud.app.schema import SCHEMA_SQL` （以及 test conftest 中同语句）正常工作
- `SCHEMA_SQL` 内容与拆分前完全一致（不含空格/换行差异）
- cloud 测试全部通过
- 每个子文件不超过 300 行

---

## 四、Batch 3：`runtime_core.py` 提取 helpers

### 方案

`AgentRuntime` 类 596 行，核心执行循环 `_execute_impl` 约 300 行。其余是辅助方法，提取到独立模块。

### 提取内容

新建 `cloud/app/agent_runtime/runtime_helpers.py`，包含：

- `_estimate_token_count()` 静态方法
- `_compress_messages()` 方法
- `_raw_llm_call()` 方法
- `_call_ai()` 方法
- `_save_log()` 方法
- `_save_snapshot()` 方法
- `_restore_from_snapshot()` 方法
- `_try_rollback()` 方法
- `rollback_to()` 方法
- `list_snapshots()` 方法
- `get_cost_usage()` 方法

提取后 `runtime_core.py` 约 300 行，`runtime_helpers.py` 约 250 行。

### 改动点

- 新建 `runtime_helpers.py`，把上述方法作为 standalone functions 或一个 `RuntimeHelper` mixin
- `runtime_core.py` 中 import helpers 替换方法调用
- `__init__.py` 不改（`AgentRuntime` 依然通过 `from .runtime_core import AgentRuntime` 导出）

### 验收标准

- `AgentRuntime` 的所有公有方法（`execute`, `resume`, `get_status`, `rollback_to`, `list_snapshots`, `get_cost_usage`, `brain` 属性）行为不变
- 所有 import `AgentRuntime` 的地方不受影响
- cloud 测试全部通过

---

## 五、Batch 4：`scenario_builder.py` 提取权重数据

### 方案

`scenario_builder.py` 426 行，其中 130 行是 `_S ~ _S21` 权重定义，其余是 `FIXED_SCENARIOS` 列表。

提取权重到 `scenario_weights.py`，`scenario_builder.py` 从那里 import。

### 具体

- 新建 `sales-coach/app/scenario_weights.py`：只包含 `_S = {}` 到 `_S21 = {}` 这 21 个权重 dict（~130 行）
- `scenario_builder.py` 开头加 `from .scenario_weights import _S, _S2, ..., _S21`（可写为 `from .scenario_weights import _S, _S2, _S3, _S4, _S5, _S6, _S7, _S8, _S9, _S10, _S11, _S12, _S13, _S14, _S15, _S16, _S17, _S18, _S19, _S20, _S21`）

### 验收标准

- `scenario_fetcher.py` 中 ``from .scenario_builder import FIXED_SCENARIOS`` 正常工作
- `FIXED_SCENARIOS` 的每个 scenario 中的 `scoring_weights` 指向正确的权重
- sales-coach 测试全部通过

---

## 六、Batch 5-7：三个 `database.py` 提取 SCHEMA SQL

### 方案

三个端各自有一个 database.py，其中 2/3 ~ 3/4 的行数是 SQL 字符串。提取到同目录的 `schema_sql.py`。

**sales-assistant/app/database.py**（385 行）：
- 提取 `SCHEMA` 字符串到 `sales-assistant/app/schema_sql.py`
- database.py 改为 `from .schema_sql import SCHEMA_SQL`
- 剩余 ~100 行（连接管理、get_db 等）

**assistant/app/database.py**（378 行）：
- 同上

**opportunity/app/database.py**（325 行）：
- 同上

**注意命名冲突：** 各端的 schema 变量命名不同（SCHEMA / SCHEMA_SQL），统一命名为 `SCHEMA_SQL`。

### 验收标准

- 各端 database.py 不超过 200 行
- schema_sql.py 不超过 300 行（各端表数量不同，若超则按 domain 再拆）
- 各端测试全部通过
- 所有 `from ...database import get_db, ...` 等不受影响

---

## 七、执行顺序

| 顺序 | Batch | 依赖 | 预估耗时 |
|:---|:---|:---|:---:|
| 1 | Batch 1: columns.py 分拆 | 无 | 40 min |
| 2 | Batch 2: schema.py 分拆 | 无（可与 Batch 1 并行） | 30 min |
| 3 | Batch 3: runtime_core.py helpers 提取 | 无 | 20 min |
| 4 | Batch 4: scenario_builder.py 权重提取 | 无 | 10 min |
| 5 | Batch 5: sales-assistant database.py | 无 | 10 min |
| 6 | Batch 6: assistant database.py | 无 | 10 min |
| 7 | Batch 7: opportunity database.py | 无 | 10 min |
| 8 | 全量测试验证 | 各 Batch 无冲突 | 15 min |

**并行策略：** Batch 1 和 Batch 2 可并行执行（不同端），其余无并行依赖。

---

## 八、风险与回滚

1. **风险：columns/ 包漏掉某个 TABLE_*_COLS 符号**
   - 预防：拆分前用 `grep '^TABLE_.*_COLS' shared/columns.py | wc -l` 统计总数，拆分后验证所有符号都在 `__init__.py` 中 re-export
   - 回滚：`git checkout -- shared/columns.py`

2. **风险：SQL 字符串拼接引入语法错误**
   - 预防：子文件每个都以 SQL 片段形式存在，`__init__.py` 使用 `+` 拼接，生成后与原文件对比 hash
   - 回滚：`git checkout -- cloud/app/schema.py`

3. **风险：runtime_core.py 方法提取后环依赖**
   - 预防：helpers 只从 AgentRuntime 中提取 `self` 作为参数传入，不做子类继承
   - 回滚：`git checkout -- cloud/app/agent_runtime/runtime_core.py`

4. **通用回滚：** 每个 Batch 执行后立即 `git commit`，失败则 `git checkout -- <修改的文件>` 后重试
