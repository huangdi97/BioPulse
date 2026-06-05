# Batch 2：制药情报服务（8006）

## 编码准则（18条）
1. Think Before Coding 2. Simplicity First 3. Surgical Changes 4. Goal-Driven Execution 5. 架构优先拒绝补丁 6. 面向组件构建 7. 显式优于隐式 8. 代码整洁自文档化 9. 单一职责 10. 组合优于委托 11. 单一状态源 12. 避免语法糖 13. 命名一致性 14. 文件不超过300行 15. 低耦合(模块间只传ID) 16. 必须用opencode写代码 17. 启动规则(write→TG→confirm→opencode) 18. 完整准则写入每个tasks.md不可省略

## 架构设计

制药情报 8006 是一个独立 FastAPI 服务，为 MSL/研发总监/BD 提供：
1. **论文检索** — 论文搜索、查看、筛选（当前用种子数据，未来对接 PubMed API）
2. **PI 画像** — PI 搜索、查询、活跃度分析
3. **靶点热度** — 靶点趋势、分类筛选、对比分析

数据接口与现有 React IntelPage 的 mockIntel.ts 数据结构完全对齐，实现无缝替换。

## 文件结构

```
pharma-intel/
├── app/
│   ├── __init__.py
│   ├── main.py                # FastAPI 入口，端口8006
│   ├── health_router.py       # 健康检查
│   ├── intel_router.py        # 情报聚合 API（3组端点）
│   └── seed_data.py           # 与 mockIntel.ts 对齐的种子数据
├── requirements.txt
└── .gitignore
```

## 子任务 1：创建目录结构

`mkdir -p pharma-intel/app` + `__init__.py`

## 子任务 2：seed_data.py

包含与 mockIntel.ts 完全对齐的静态数据：

- `PAPERS: list[dict]` — 与 Paper 接口对齐（id/title/authors/journal/year/citations/keywords/pmid/abstract/relevance）
- `PI_PROFILES: list[dict]` — 与 PiProfile 接口对齐（id/name/institution/title/department/h_index/papers/grants/research_areas/activity_score）
- `TARGETS: list[dict]` — 与 Target 接口对齐（id/name/category/paper_count/trial_count/growth/trend_data）

数据内容直接从 web/src/api/mockIntel.ts 复制结构，转为 Python dict。

## 子任务 3：intel_router.py

三个 API 组：

```
# 论文检索
GET /api/intel/papers?q=xxx&page=1&page_size=10
  → 搜索论文（标题/作者/关键词模糊匹配）
  → 返回 {items: Paper[], total: int, page: int}
GET /api/intel/papers/{id}
  → 返回 Paper detail

# PI画像
GET /api/intel/pi?q=xxx&page=1&page_size=20
  → 搜索PI（姓名/机构/研究方向模糊匹配）
  → 返回 {items: PiProfile[], total: int, page: int}
GET /api/intel/pi/{id}
  → 返回 PiProfile detail

# 靶点热度
GET /api/intel/targets?category=xxx&sort_by=paper_count&sort_dir=desc
  → 返回 Target[] 列表（支持过滤/排序）
GET /api/intel/targets/{id}
  → 返回 Target detail（含 trend_data）
GET /api/intel/targets/categories
  → 返回去重分类列表
```

所有 API 返回格式：`{"code": 0, "message": "ok", "data": ...}`

## 子任务 4：main.py

FastAPI 应用：
- 端口 8006
- RequestID + CORS 中间件
- 注册 health_router + intel_router
- 挂载 /assets 静态文件 + catch-all SPA（引用 web/dist）

## 子任务 5：health_router.py

`GET /health` → `{"status": "ok", "service": "pharma-intel", "version": "1.0.0"}`

## 子任务 6：React 前端对接

修改 `web/src/api/client.ts`：新增 `setIntelBaseURL(url)` 函数。
新增 `getIntelPapers(q, page)`, `getIntelPiProfiles(q)`, `getIntelTargets(category)` 函数。
当 intelBaseURL 被设置为 8006 时，这些函数调用真实 API，否则降级到 mockIntel 数据。

## 子任务 7：验证

1. `python -c 'from pharma_intel.app.main import app; print("OK")'`
2. `uvicorn pharma_intel.app.main:app --port 8006` 启动
3. `curl localhost:8006/health` → 200
4. `curl localhost:8006/api/intel/papers?q=PD-1` → 返回论文
5. `curl localhost:8006/api/intel/pi?q=王` → 返回PI
6. `curl localhost:8006/api/intel/targets` → 返回靶点
7. `npm run build` 通过
