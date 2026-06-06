# Patient-Engage · 患者服务

> 患者教育、用药提醒、随访管理。辅助药企患者关系管理。

**端口：** 8011

## 核心文件

| 文件 | 说明 |
|:-----|:-----|
| `app/main.py` | 应用入口 |
| `app/education_router.py` | 患者教育 API |
| `app/reminder_router.py` | 用药提醒 API |
| `app/followup_router.py` | 随访管理 API |
| `app/database.py` | 本地缓存数据库 |
| `app/services/` | 患者服务业务服务 |

## 启动

```bash
uvicorn patient_engage.app.main:app --port 8011
```
