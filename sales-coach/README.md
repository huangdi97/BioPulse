# Sales-Coach · 销售教练

> 销售陪练与考核系统。AI 数字人场景模拟、对话反思评分、培训模块管理、会话管理。

**端口：** 8001

## 核心文件

| 文件 | 说明 |
|:-----|:-----|
| `app/main.py` | 应用入口 |
| `app/scenario_router.py` | 场景模拟 API |
| `app/scenario_builder.py` | 场景构建器 |
| `app/scenario_simulator.py` | 场景模拟器 |
| `app/scenario_loader.py` | 场景加载器 |
| `app/scenario_filter.py` | 场景过滤器 |
| `app/scenario_library.py` | 场景库 |
| `app/scenario_db.py` | 场景数据库 |
| `app/digital_human_router.py` | 数字人 API |
| `app/digital_human.py` | 数字人核心 |
| `app/assessment_router.py` | 评估 API |
| `app/reflection_router.py` | 反思 API |
| `app/module_router.py` | 模块管理 API |
| `app/session_router.py` | 会话管理 API |
| `app/stats_router.py` | 统计 API |
| `app/services/digital_human_service.py` | 数字人服务 |
| `app/services/digital_human_provider.py` | 数字人供应商（InternalLLM/WaveCloud/MoShang） |
| `app/services/assessment_service.py` | 评估服务 |
| `app/services/reflection_feedback.py` | 反思反馈 |
| `app/services/reflection_score.py` | 反思评分 |
| `app/services/session_service.py` | 会话管理 |
| `app/repositories.py` | 数据仓库 |

## 启动

```bash
uvicorn sales_coach.app.main:app --port 8001
```
