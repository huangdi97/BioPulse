# B2: 双主线物理隔离 — 补齐审计链 + 导出

## 编码准则（必须遵守）
1. Think Before Coding — 先想清楚再写
2. Simplicity First — 简单优先，不过度设计
3. Surgical Changes — 精准改动，不多改
4. Goal-Driven Execution — 目标驱动，不跑偏
5. 架构优先，拒绝补丁 — 先定架构再写代码
6. 面向组件构建 — 组件化开发
7. 显式优于隐式 — 代码清晰可读
8. 代码整洁，自文档化 — 不写多余注释
9. 单一职责 — 一个文件只做一件事
10. 组合优于委托 — 组件组合优先
11. 单一状态源 — 状态不分散
12. 避免语法糖 — 简单直接
13. 命名一致性 — 统一命名风格
14. **文件不超过300行** — 超了必须拆分
15. **低耦合** — 模块间只传ID，不传对象
16. **必须用opencode写代码** — 所有代码通过opencode生成
17. **启动规则: write→TG→confirm→opencode**
18. **完整准则写入每个tasks.md，不可省略**

## 现有上下文

科研模式已有基础设施：
- `cloud/app/research_database.py` — 独立 `research.db`，含 `research_audit_log` 表
- `cloud/app/services/research_export_service.py` — 导出服务，含水印"科研服务记录-学术合规"
- `cloud/rules/research_rules.json` + `research_rules_l2.json` — 独立合规规则
- `shared/auth_scope.py` — `require_scope("research"/"pharma")`
- Cloud 路由中已有 10 个 `research_*` 路由器（PI/产品/匹配/报价/轨迹/出口/执法/路线）

## 任务

### 任务1: 审计日志写入函数

在 `cloud/app/research_database.py` 中添加 `log_research_audit()` 函数：

```python
def log_research_audit(
    event_type: str,
    entity_type: str,
    entity_id: int,
    old_value: str | None = None,
    new_value: str | None = None,
    operator: str = "",
) -> None:
    """写入科研模式审计日志。
    
    Args:
        event_type: 事件类型 (create/update/delete/switch/export)
        entity_type: 实体类型 (pi/quote/product/visit/mode)
        entity_id: 实体ID
        old_value: 旧值（JSON字符串）
        new_value: 新值（JSON字符串）
        operator: 操作者标识
    """
    db = get_research_db()
    try:
        db.execute(
            "INSERT INTO research_audit_log (event_type, entity_type, entity_id, old_value, new_value, operator, timestamp) "
            "VALUES (?, ?, ?, ?, ?, ?, datetime('now'))",
            (event_type, entity_type, entity_id, old_value, new_value, operator),
        )
        db.commit()
    finally:
        db.close()
```

### 任务2: 模式切换审计路由

创建 `cloud/app/routers/research_audit_router.py`：

- 路由前缀: `/api/research/audit`
- GET `/logs` — 获取审计日志列表（支持分页：page, per_page）
- GET `/logs/{log_id}` — 获取单条审计日志详情
- GET `/logs/by-type/{event_type}` — 按事件类型筛选
- POST `/switch` — 记录模式切换事件（请求体: {from_mode, to_mode, device_id, gps}）
  - 写入 `research_audit_log`，event_type="switch", entity_type="mode"
  - 记录切换前后mode、时间、设备ID、GPS

在 `cloud/app/services/` 中创建 `research_audit_service.py` 实现业务逻辑。

在 `cloud/app/main.py` 中注册新路由。

### 任务3: 导出 API 路由

创建 `cloud/app/routers/research_export_router.py`（如果不存在）：

- 路由前缀: `/api/research/export`
- GET `/pi/csv` — 导出PI列表为CSV，文件头加水印"科研服务记录-学术合规"
- GET `/quotation/{quotation_id}/json` — 导出报价单为JSON，含watermark字段
- 每次导出写入审计日志（event_type="export"）

如果在 `cloud/app/routers/` 中已存在 `research_export_router.py`，则检查并增强它。

### 任务4: 在现有研究路由中注入审计日志

在所有 research 路由器的 CRUD 操作中添加审计日志调用。目标是以下文件（如存在）：

- `research_pi_router.py` — PI创建/更新/删除时写审计日志
- `research_quotation_router.py` — 报价单创建/更新/删除时写审计日志
- `research_product_router.py` — 产品创建/更新/删除时写审计日志
- `research_matching_router.py` — 匹配操作写审计日志

在每个 create/update/delete 端点中，在成功操作后调用 `log_research_audit()`。

### 任务5: 验证身份隔离5条

验证并确认以下5条全部完成：

| # | 隔离项 | 状态 |
|:-:|:-------|:-----|
| ① | 独立Schema/数据库 | `research.db` + `research_*` 表前缀 |
| ② | 审计链独立 | `research_audit_log` 表 + 写入函数 + 路由 + 切换日志 |
| ③ | 独立合规库 | `research_rules.json` + `research_rules_l2.json` |
| ④ | JWT scope隔离 | `require_scope("research"/"pharma")` |
| ⑤ | 导出分离 | 导出含"科研服务记录-学术合规"水印 |

## 文件清单

**新增文件：**
```
cloud/app/routers/research_audit_router.py
cloud/app/services/research_audit_service.py
```

**修改文件：**
```
cloud/app/research_database.py（添加 log_research_audit 函数）
cloud/app/main.py（注册新路由）
cloud/app/routers/research_export_router.py（如不存在则创建/增强）
cloud/app/routers/research_pi_router.py（注入审计日志）
cloud/app/routers/research_quotation_router.py（注入审计日志）
cloud/app/routers/research_product_router.py（注入审计日志）
cloud/app/routers/research_matching_router.py（注入审计日志——如存在）
```

## 验收标准

1. ✅ `log_research_audit()` 函数可调用，写入 `research_audit_log` 表
2. ✅ GET `/api/research/audit/logs` 返回审计日志列表
3. ✅ POST `/api/research/audit/switch` 记录模式切换事件
4. ✅ GET `/api/research/export/pi/csv` 返回带水印CSV
5. ✅ GET `/api/research/export/quotation/{id}/json` 返回带水印JSON
6. ✅ PI/报价单/产品的CRUD操作均写入审计日志
7. ✅ 所有文件不超过300行
8. ✅ ruff check 通过
