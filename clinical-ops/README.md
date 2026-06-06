# Clinical-Ops · 临床试验运营

> 中心筛选、患者招募、监察报告管理。辅助药企临床试验运营。

**端口：** 8010

## 核心文件

| 文件 | 说明 |
|:-----|:-----|
| `app/main.py` | 应用入口 |
| `app/site_router.py` | 中心筛选 API |
| `app/recruitment_router.py` | 患者招募 API |
| `app/monitoring_router.py` | 监察报告 API |
| `app/database.py` | 本地缓存数据库 |
| `app/services/` | 临床运营业务服务 |

## 启动

```bash
uvicorn clinical_ops.app.main:app --port 8010
```
