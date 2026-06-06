# React 前端 API 调用与后端 FastAPI 路由对齐审计报告

审计时间：2026-06-07
审计范围：`web/src/api/client.ts` → 后端 `cloud/` + `pharma_intel/`

---

## 1. 仪表盘 APIs (Cloud API, baseURL=http://localhost:8000)

### 后端路由文件：`cloud/app/dashboard_router.py`
- **prefix**: `/dashboard`
- **已注册端点**: GET /overview, GET /users, GET /compliance, GET /contents, GET /team/summary, GET /team/ranking

| # | 前端调用 | 方法 | 后端端点 | 状态 | 严重程度 |
|---|---------|------|---------|------|---------|
| 1 | `/dashboard/overview` | GET | `/dashboard/overview` | ✅ 对齐 | — |
| 2 | `/dashboard/visit-trends` | GET | **不存在** | ❌ 缺失 | 🔴 高 |
| 3 | `/dashboard/team-ranks` | GET | `/dashboard/team/ranking` (路径不匹配) | ❌ 路径不一致 | 🔴 高 |
| 4 | `/dashboard/violations` | GET | **不存在** | ❌ 缺失 | 🔴 高 |
| 5 | `/dashboard/research-kpis` | GET | **不存在** | ❌ 缺失 | 🔴 高 |
| 6 | `/dashboard/pi-sources` | GET | **不存在** | ❌ 缺失 | 🔴 高 |
| 7 | `/dashboard/product-match-stats` | GET | **不存在** | ❌ 缺失 | 🔴 高 |
| 8 | `/dashboard/compliance` | GET | `/dashboard/compliance` | ✅ 对齐 | — |

> **说明**: 前端有 8 个仪表盘端点，后端只实现了 2 个（overview、compliance）。其余 6 个（visit-trends、team-ranks、violations、research-kpis、pi-sources、product-match-stats）在后端完全没有路由定义。

---

## 2. 认证 APIs (Cloud API, baseURL=http://localhost:8000)

### 后端路由文件：`cloud/app/auth_router.py`
- **prefix**: `/auth`
- **已注册端点**: POST /register, POST /login, POST /refresh

| # | 前端调用 | 方法 | 后端端点 | 状态 | 严重程度 |
|---|---------|------|---------|------|---------|
| 1 | `/auth/login` | POST | `/auth/login` | ✅ 对齐 | — |
| 2 | `/auth/change-password` | POST | **不存在** | ❌ 缺失 | 🟡 中 |
| 3 | `/auth/register` | POST | `/auth/register` | ✅ 对齐 | — |

> **说明**: 前端用 POST JSON body 调用 `/auth/login`，后端也接受 POST JSON body — 对齐。但 `/auth/change-password` 在后端完全不存在。

---

## 3. 培训教练 APIs (Cloud API, baseURL=http://localhost:8000, 通过 fetchCoachApi 调用)

### 后端路由文件：`cloud/app/training_coach_router.py`
- **prefix**: `/training-coach`
- **已注册端点**: GET/POST /modules, GET/POST /sessions, GET /sessions/{id}, POST /recommend, GET/POST /attributions, POST /attributions/{id}/analyze, GET /dashboard

前端 fetchCoachApi 内部拼接：`/training-coach${path}`

| # | 前端调用 | 实际路径 | 后端端点 | 状态 | 严重程度 |
|---|---------|---------|---------|------|---------|
| 1 | `getCoachModules()` → `/modules` | `/training-coach/modules` | GET `/training-coach/modules` | ✅ 对齐 | — |
| 2 | `getCoachSessions()` → `/sessions?...` | `/training-coach/sessions?...` | GET `/training-coach/sessions` | ✅ 对齐 | — |
| 3 | `getCoachDashboard()` → `/dashboard` | `/training-coach/dashboard` | GET `/training-coach/dashboard` | ✅ 对齐 | — |

> **说明**: 培训教练路由全部对齐。

---

## 4. 制药情报 APIs (独立服务, intelBaseURL=http://localhost:8006)

### 后端路由文件：`pharma_intel/app/intel_router.py`
- **prefix**: `/api/intel`
- **已注册端点**: GET /papers, GET /papers/{id}, GET /pi, GET /pi/{id}, GET /targets, GET /targets/categories, GET /targets/{id}

| # | 前端调用 | 方法 | 后端端点 | 状态 | 严重程度 |
|---|---------|------|---------|------|---------|
| 1 | `/api/intel/papers?...` | GET | `/api/intel/papers` | ✅ 对齐 | — |
| 2 | `/api/intel/pi?...` | GET | `/api/intel/pi` | ✅ 对齐 | — |
| 3 | `/api/intel/targets?...` | GET | `/api/intel/targets` | ✅ 对齐 | — |
| 4 | `/api/intel/targets/categories` | GET | `/api/intel/targets/categories` | ✅ 对齐 | — |

> **说明**: 制药情报 8006 服务的所有 4 个 intel 端点均对齐。注意该服务是一个独立的 FastAPI 服务，运行在端口 8006，与 Cloud API 8000 不同。查询参数（q, page, page_size, category, sort_by, sort_dir）也都匹配。

---

## 5. 汇总

### 总体统计

| 分类 | 总数 | 对齐 | 不匹配 |
|------|:----:|:----:|:-----:|
| 仪表盘 | 8 | 2 | **6** |
| 认证 | 3 | 2 | **1** |
| 培训教练 | 3 | 3 | 0 |
| 制药情报 | 4 | 4 | 0 |
| **合计** | **18** | **11** | **7** |

### 不匹配项详细列表（按严重程度排序）

#### 🔴 高严重度（前端页面将完全无法加载或报错）

| # | 前端路径 | 问题 | 影响 |
|---|---------|------|------|
| 1 | GET `/dashboard/visit-trends` | 后端无此路由 | VisitTrends 页面数据缺失 |
| 2 | GET `/dashboard/team-ranks` | 后端路径为 `/dashboard/team/ranking` | TeamRanks 组件调用 404 |
| 3 | GET `/dashboard/violations` | 后端无此路由 | Violations 页面数据缺失 |
| 4 | GET `/dashboard/research-kpis` | 后端无此路由 | ResearchKpis 页面数据缺失 |
| 5 | GET `/dashboard/pi-sources` | 后端无此路由 | PiSources 页面数据缺失 |
| 6 | GET `/dashboard/product-match-stats` | 后端无此路由 | ProductMatchStats 页面数据缺失 |

#### 🟡 中严重度（功能可用但能力缺失）

| # | 前端路径 | 问题 | 影响 |
|---|---------|------|------|
| 7 | POST `/auth/change-password` | 后端无此路由 | 修改密码功能不可用 |

### 修复建议

1. **后端新增缺失路由（高优先级）**: 在 `cloud/app/dashboard_router.py` 中添加以下端点：
   - `GET /dashboard/visit-trends` → 对应 `getVisitTrends()`
   - `GET /dashboard/violations` → 对应 `getViolations()`
   - `GET /dashboard/research-kpis` → 对应 `getResearchKpis()`
   - `GET /dashboard/pi-sources` → 对应 `getPiSources()`
   - `GET /dashboard/product-match-stats` → 对应 `getProductMatchStats()`

2. **路径对齐（高优先级）**: 将前端 `/dashboard/team-ranks` 改为 `/dashboard/team/ranking`，或将后端添加 `/dashboard/team-ranks` 作为别名。

3. **后端新增修改密码端点（中优先级）**: 在 `cloud/app/auth_router.py` 中添加 `POST /auth/change-password` 端点，调用 `AuthService.change_password()`。
