# Pharma-Intel · 制药情报

> 竞品追踪、会议情报、KOL 管理、研发管线情报。辅助药企决策。

**端口：** 8010

## 核心文件

| 文件 | 说明 |
|:-----|:-----|
| `app/main.py` | 应用入口 |
| `app/intel_router.py` | 情报查询 API |
| `app/competitor_router.py` | 竞品追踪 API |
| `app/conference_router.py` | 会议情报 API |
| `app/kol_router.py` | KOL 管理 API |
| `app/pipeline_router.py` | 研发管线 API |
| `app/target_router.py` | 靶点信息 API |
| `app/seed_data.py` | 种子数据 |
| `app/services/` | 情报业务服务 |

## 启动

```bash
uvicorn pharma_intel.app.main:app --port 8010
```
