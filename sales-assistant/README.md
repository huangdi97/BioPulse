# Sales-Assistant · 销售助理

> 医药代表日常销售辅助工具。访前准备、拜访笔记、客户异议处理、销售漏斗分析、日程管理。

**端口：** 8004

## 核心文件

| 文件 | 说明 |
|:-----|:-----|
| `app/main.py` | 应用入口 |
| `app/precall_router.py` | 访前准备 API |
| `app/note_router.py` | 拜访笔记 API |
| `app/objection_router.py` | 异议处理 API |
| `app/funnel_router.py` | 销售漏斗 API |
| `app/schedule_router.py` | 日程管理 API |
| `app/hcp_router.py` | HCP 信息 API |
| `app/content_router.py` | 内容管理 API |
| `app/coach_router.py` | 教练辅助 API |
| `app/strategy_router.py` | 策略 API |
| `app/anomaly_router.py` | 异常检测 API |
| `app/repositories.py` | 数据仓库 |

## 启动

```bash
uvicorn sales_assistant.app.main:app --port 8004
```
