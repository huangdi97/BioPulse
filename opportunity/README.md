# Opportunity · 商机挖掘

> 招投标信息监控、商机线索评分、科研轨迹追踪、论文诚信查询、趋势预测。

**端口：** 8002

## 核心文件

| 文件 | 说明 |
|:-----|:-----|
| `app/main.py` | 应用入口 |
| `app/opportunity_router.py` | 商机线索 CRUD |
| `app/bidding_router.py` | 招投标信息管理 |
| `app/bidding_agent_router.py` | 招投标 Agent 调度 |
| `app/scoring_router.py` | 线索评分 API |
| `app/research_router.py` | 科研轨迹 API |
| `app/pubpeer_router.py` | 论文诚信查询 |
| `app/trend_router.py` | 趋势分析 |
| `app/stats_router.py` | 统计报表 |
| `app/services/opportunity_service.py` | 商机业务逻辑 |
| `app/services/scoring_service.py` | 评分引擎 |
| `app/services/bidding_agent_service.py` | 招投标 Agent 调度逻辑 |
| `app/repositories/` | 独立文件仓库层 |

## 启动

```bash
uvicorn opportunity.app.main:app --port 8002
```
