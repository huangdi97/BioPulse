# Market-Access · 准入策略服务

> 医保目录查询、准入策略分析、报销信息查询。辅助药企市场准入决策。

**端口：** 8007

## 核心文件

| 文件 | 说明 |
|:-----|:-----|
| `app/main.py` | 应用入口 |
| `app/formulary_router.py` | 医保目录查询 API |
| `app/bidding_router.py` | 招标信息 API |
| `app/strategy_router.py` | 准入策略分析 API |
| `app/database.py` | 本地缓存数据库 |
| `app/services/` | 准入业务服务 |

## 启动

```bash
uvicorn market_access.app.main:app --port 8007
```
