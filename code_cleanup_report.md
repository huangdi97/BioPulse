# 代码精简机会审计报告

> 审计范围: `cloud/` (Python) 和 `frontend/src/mock/`, `frontend/src/pages/` (TypeScript/React)
> 审计日期: 2026-06-07

---

## 1. 未使用的 Import

### Python (cloud/)

| 文件 | 问题 | 精简行数 | 风险 |
|------|------|---------|------|
| `cloud/app/agent_runtime/scripts/download_layer1_model.py:11` | `import sys` 未使用 | 1 | 低 |
| `cloud/app/database.py:17` | `from cloud.app.seeds.seed_holographic` 未使用 | 1 | 低 |
| `cloud/app/holographic_router.py:1` | `from typing import Optional` 未使用 | 1 | 低 |
| `cloud/app/tests/test_holographic.py:143` | 局部变量 `id_b` 赋值未使用 (`F841`) | 1 | 低 |

### Frontend (mock TS 文件)

mock 文件中的 import 均为 `type` import（编译期抹除），且全部被 API 层引用。**无多余 import。**

---

## 2. 重复代码块 / 高相似度函数

### 2.1 合规执行引擎三文件拆分过度

| 文件 | 行数 | 说明 |
|------|------|------|
| `cloud/app/services/compliance_enforcer.py` | 129 | 主入口 |
| `cloud/app/services/compliance_enforcer_engine.py` | 237 | 规则匹配引擎 |
| `cloud/app/services/compliance_enforcer_audit.py` | 93 | 审计日志 |
| `cloud/app/services/compliance_strategy_service.py` | 279 | 策略封装 |

**分析:** `engine` + `audit` 被 `enforcer` 引用，而 `strategy_service` 又包装 `enforcer`。四文件逻辑耦合度极高，可合并为 1~2 个文件。精简 ~200 行（文件头+跨文件引用开销）。**风险: 中**（需确认不破坏已有 import 路径）。

### 2.2 `_now()` 函数重复定义

多个文件中定义了相同的 `_now()` 辅助函数：

| 文件 | 行数 |
|------|------|
| `cloud/app/services/brain_evolution_service.py:9` | `def _now() -> str:` |
| `cloud/app/services/report_templates.py:7` | `def _now() -> str:` |
| `cloud/app/services/research_trajectory_service.py:12` | `def _now() -> str:` |

可提取到共享模块。精简 ~4 行。**风险: 低**。

### 2.3 `_call_ai()` / `_call_deepseek()` 多次出现

| 文件 | 函数 |
|------|------|
| `cloud/app/services/report_templates.py:25` | `_call_ai(messages, auth_header)` |
| `cloud/app/services/hcp_sandbox_service.py:25` | `_call_ai(system_prompt, user_prompt)` |
| `cloud/app/services/route_service.py:28` | `_call_deepseek(messages, temperature, max_tokens)` |

签名不同但功能高度重叠，可统一定义在共享模块。精简 ~15 行。**风险: 低**。

### 2.4 `research_trajectory_features.py` 纯 re-export 文件

```
cloud/app/services/research_trajectory_features.py（6 行）
  → 仅 re-export feature_analyzer + feature_extractor 中的函数
```

可直接删除，调用方改用原始模块。精简 6 行。**风险: 低**。

### 2.5 内部 mock 数据重复（Frontend）

`frontend/src/pages/admin/employee/MyTasks.tsx` 定义了独立的 `mockTasks` 数组，与 `frontend/src/mock/tasks.ts` 功能重复。

精简 ~15 行。**风险: 低**（页面本身就是 mock-only）。

---

## 3. 空的 / 只抛异常的 / 从未调用的函数

| 文件 | 问题 | 精简行数 | 风险 |
|------|------|---------|------|
| `cloud/app/agent_runtime/__init__.py` | 空文件 | 0 | 低（__init__ 可为空） |
| `cloud/app/services/__init__.py` | 空文件 | 0 | 低（__init__ 可为空） |
| `cloud/app/tests/__init__.py` | 空文件 | 0 | 低（__init__ 可为空） |

**无直接空的函数或只抛异常的代码。** Ruff 未检出 `NotImplementedError` 模式。

---

## 4. 注释掉的代码块

**未发现注释掉的代码块。** 搜索 `# import`, `# def`, `# class`, `# return` 等模式均无命中。代码风格良好。

---

## 5. 空文件或仅含 import 的文件

| 文件 | 行数 | 内容 | 建议 | 风险 |
|------|------|------|------|------|
| `cloud/app/agent_runtime/__init__.py` | 0 | 空 | 可删除（Python 3.3+ 支持 namespace package） | 低 |
| `cloud/app/services/__init__.py` | 0 | 空 | 可删除 | 低 |
| `cloud/app/tests/__init__.py` | 0 | 空 | 可删除 | 低 |
| `cloud/app/services/research_trajectory_features.py` | 6 | 纯 re-export | 可删除 | 低 |
| `cloud/app/agent_runtime/models/distilbert/.gitkeep` | 0 | 占位文件 | 可删除（无模型文件） | 低 |
| `cloud/app/main.py.orig` | 71 | 旧版本备份 | 可删除 | 低 |

---

## 6. mock 目录评估

### 6.1 现状

`frontend/src/mock/` 下 6 个文件，共 589 行，全部**活跃使用中**：

| Mock 文件 | 行数 | 被引用方 |
|-----------|------|----------|
| `compliance.ts` | 156 | API 层 (fallback) |
| `hcps.ts` | 124 | API 层 (fallback) + VisitNew.tsx (直接) |
| `visits.ts` | 106 | API 层 (fallback) |
| `manager.ts` | 81 | API 层 (fallback) + Dashboard/Opportunities/Visits (直接) |
| `recommends.ts` | 65 | API 层 (fallback) |
| `tasks.ts` | 57 | API 层 (fallback) |
| **合计** | **589** | |

### 6.2 使用模式

**模式 A: API fallback (推荐) — 6/6 mock 文件**
```
async function fetchXxx() {
  try { return await client.get(...) }   ← 先调真实 API
  catch { return mockData }              ← 失败时 fallback
}
```

**模式 B: 页面直接使用 mock — 4+ 个页面绕过 API 层**
- `frontend/src/pages/rep/VisitNew.tsx` — `import { mockHcps } from '@/mock/hcps'`
- `frontend/src/pages/manager/Dashboard.tsx` — `import { mockTeamSummary, ... } from '@/mock/manager'`
- `frontend/src/pages/manager/Opportunities.tsx` — `import { mockOpportunities } from '@/mock/manager'`
- `frontend/src/pages/manager/Visits.tsx` — `import { mockTeamRanking } from '@/mock/manager'`

**模式 C: 页面内置 mock（完全独立）— 13+ 个页面**
所有 `frontend/src/pages/admin/*` 下的页面（president/, manager/, employee/）内置自己的 mock 数据，**完全不调用任何 API**。

### 6.3 Mock 清理评估

| 层面 | 清理难度 | 建议 |
|------|---------|------|
| `frontend/src/mock/*.ts` (6 个文件) | 中 | 保留 API fallback 模式中的 mock 引用，但**仅在需要时** |
| `frontend/src/pages/` 直接引用 mock 的页面 (4 个) | 中 | 改为调用 API 层函数，让 mock 仅作为 fallback |
| `frontend/src/pages/admin/*` 内置 mock 的页面 (13 个) | **高** | 这些页面**完全没有真实 API 对接**，清理 mock=不可用 |

**设计意图 "mock 是临时方案" 评估:**
- API 层的 fallback mock (模式 A) 是**合理的降级策略**，在真实 API 完成对接前可保留
- 页面直接使用 mock (模式 B) 应在短期（1-2 周）内改造为 API 调用
- 内置 mock 的 admin 页面 (模式 C) 是**最大的技术债务**，清理需要先完成后端 API

---

## 总结汇总

| 类别 | 项数 | 总精简行数 | 高风险 | 中风险 | 低风险 |
|------|------|-----------|--------|--------|--------|
| 1. 未使用的 import | 4 | 4 | 0 | 0 | 4 |
| 2. 重复代码块 | 5 组 | ~225 | 0 | 1 | 4 |
| 3. 空函数/文件 | 3+3 | 0+77 | 0 | 0 | 6 |
| 4. 注释掉的代码 | 0 | 0 | 0 | 0 | 0 |
| 5. 空文件/import-only | 6 | 77 | 0 | 0 | 6 |
| 6. mock 目录 | 13+ 页面 | 589 (mock数据) | 0 | 0 | 13 |

**高风险项: 0**
**中风险项:** `compliance_enforcer*` 四文件合并（需确保 import 路径兼容）
**立即安全可删除:** `main.py.orig`, `.gitkeep`, `research_trajectory_features.py`, 3 个空 `__init__.py`
**最大优化潜力:** 将所有 `admin/` 页面从硬编码 mock 改造为 API 调用 + fallback 模式，约 1200+ 行 mock 数据可随 API 就绪而清理。
