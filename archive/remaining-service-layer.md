# Opportunity / Sales-Coach / Sales-Assistant 端 Service 层引入

## 模式（Cloud + Assistant 已验证）

和之前完全一致：每个路由文件对应一个 Service 类，路由只保留 Pydantic 模型 + `service: XxxService = Depends()`。

## 任务

### Batch 1: Opportunity 端（10路由）

| Service 文件 | 对应路由 |
|:-------------|:---------|
| opportunity_service.py | opportunity_router.py |
| contact_service.py | contact_router.py |
| bidding_service.py | bidding_router.py |
| bidding_agent_service.py | bidding_agent_router.py |
| stats_service.py | stats_router.py |
| pubpeer_service.py | pubpeer_router.py |
| trend_service.py | trend_router.py |
| bookmark_service.py | bookmark_router.py |
| research_service.py | research_router.py |
| scoring_service.py | scoring_router.py |

### Batch 2: Sales-Coach 端（5路由）

| Service 文件 | 对应路由 |
|:-------------|:---------|
| module_service.py | module_router.py |
| scenario_service.py | scenario_router.py |
| session_service.py | session_router.py |
| assessment_service.py | assessment_router.py |
| stats_service.py | stats_router.py |

### Batch 3: Sales-Assistant 端（10路由）

| Service 文件 | 对应路由 |
|:-------------|:---------|
| schedule_service.py | schedule_router.py |
| note_service.py | note_router.py |
| hcp_service.py | hcp_router.py |
| content_service.py | content_router.py |
| strategy_service.py | strategy_router.py |
| coach_service.py | coach_router.py |
| anomaly_service.py | anomaly_router.py |
| funnel_service.py | funnel_router.py |
| objection_service.py | objection_router.py |
| precall_service.py | precall_router.py |

## 验收

- [ ] 所有端编译通过
- [ ] 各端测试通过（opp 7 + coach 7 + assistant 7 = 21）
- [ ] Cloud 42 + Assistant 8 不受影响
