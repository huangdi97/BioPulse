# Step 1/3：后端 — Cloud demo_router 加 6 个端点

## 编码准则（完整18条）
1. Think Before Coding 2. Simplicity First 3. Surgical Changes 4. Goal-Driven Execution 5. 架构优先拒绝补丁 6. 面向组件构建 7. 显式优于隐式 8. 代码整洁自文档化 9. 单一职责 10. 组合优于委托 11. 单一状态源 12. 避免语法糖 13. 命名一致性 14. 文件不超过300行 15. 低耦合(模块间只传ID) 16. 必须用opencode写代码 17. 启动规则(write→TG→confirm→opencode) 18. 完整准则写入每个tasks.md不可省略

## 任务
在 Cloud:8000 的 demo_router.py + dashboard_service.py 中新增 6 个 demo 数据端点。数据用逻辑生成（可预测，非随机），数据结构与 web/src/api/mockData.ts 保持一致。

### 文件1：cloud/app/services/dashboard_service.py
新增 6 个方法（在 class DashboardService 末尾、get_content_stats 之后）：

```python
def get_visit_trends(self) -> dict:
    """返回近30天拜访趋势。数据结构：{dates:[str], counts:[int], pass_rates:[float]}"""
    
def get_team_ranks(self) -> list:
    """返回团队排名。返回：[{name:str, visits:int, compliance_rate:float, deals:int}, ...]"""
    
def get_violations(self) -> list:
    """返回违规列表。返回：[{id:int, rep_name:str, type:str, detail:str, severity:str, date:str, status:str}, ...]"""
    
def get_research_kpis(self) -> list:
    """返回科研KPI。返回：[{title:str, value, change:int, icon:str}, ...]"""
    
def get_pi_sources(self) -> list:
    """返回PI来源。返回：[{name:str, institution:str, matches:int, last_activity:str}, ...]"""
    
def get_product_match_stats(self) -> list:
    """返回产品匹配统计。返回：[{category:str, total:int, matched:int, rate:int}, ...]"""
```

数据内容参考 mockData.ts 但不要硬编码完全相同。日期用 datetime 生成最近 N 天。名字用中文姓名。

### 文件2：cloud/app/routers/demo_router.py
新增 6 个 GET 端点，照已有模式：
```python
@router.get("/visit-trends")
def visit_trends(service: DashboardService = Depends()):
    return service.get_visit_trends()

@router.get("/team-ranks")
def team_ranks(service: DashboardService = Depends()):
    return service.get_team_ranks()

@router.get("/violations")
def violations(service: DashboardService = Depends()):
    return service.get_violations()

@router.get("/research-kpis")
def research_kpis(service: DashboardService = Depends()):
    return service.get_research_kpis()

@router.get("/pi-sources")
def pi_sources(service: DashboardService = Depends()):
    return service.get_pi_sources()

@router.get("/product-match-stats")
def product_match_stats(service: DashboardService = Depends()):
    return service.get_product_match_stats()
```

## 验收标准
- `GET /api/demo/visit-trends` → 200, 含30天日期和counts
- `GET /api/demo/team-ranks` → 200, 8人排名
- `GET /api/demo/violations` → 200, 10条违规
- `GET /api/demo/research-kpis` → 200, 4个KPI
- `GET /api/demo/pi-sources` → 200, 6个PI
- `GET /api/demo/product-match-stats` → 200, 4个品类
- 所有端点返回 JSON，数据结构与 mockData.ts 兼容
- dashboard_service.py 不超过300行
- demo_router.py 不超过300行
