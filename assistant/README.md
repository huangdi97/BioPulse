# Assistant · 跟台助手

> 医药代表跟台场景专用服务。管理拜访记录、手术跟台、HCP 信息、访前计划、离线同步。

**端口：** 8003

## 核心文件

| 文件 | 说明 |
|:-----|:-----|
| `app/main.py` | 应用入口 |
| `app/visit_router.py` | 拜访管理 API |
| `app/surgery_router.py` | 手术跟台 API |
| `app/hcp_router.py` | HCP（医疗专业人士）信息 API |
| `app/location_router.py` | 定位服务 API |
| `app/media_router.py` | 多媒体管理 API |
| `app/offline_router.py` | 离线数据同步 API |
| `app/sync_router.py` | 在线同步 API |
| `app/qa_router.py` | 问答 API |
| `app/task_router.py` | 任务管理 API |
| `app/voice_router.py` | 语音服务 API |
| `app/ws_router.py` / `ws_manager.py` | WebSocket 实时通信 |
| `app/services/visit_service.py` | 拜访业务逻辑 |
| `app/services/surgery_service.py` | 跟台业务逻辑 |
| `app/services/sync_service.py` | 同步业务逻辑 |
| `app/repositories.py` | 数据仓库 |

## 启动

```bash
uvicorn assistant.app.main:app --port 8003
```
