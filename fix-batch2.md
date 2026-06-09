# 修复·批次2（P0-4～P0-6：data_platform集成 + 标准差修复）

你是 Codex CLI。请直接执行，不要调用其他编码Agent，你自己干。

## 1. P0-4：data_platform 集成到应用中

**新建文件：** `cloud/app/routers/data_platform_router.py`

创建 router 暴露3个API端点：
- `POST /api/data-platform/pipeline/run` — 执行ETL管道
- `POST /api/data-platform/olap/query` — OLAP多维查询
- `GET /api/data-platform/bi/report` — 嵌入式BI报表数据

从 `cloud.app.data_platform.etl.pipeline` 导入 `ETLPipeline`
从 `cloud.app.data_platform.analytics.olap_service` 导入 `OLAPService`
从 `cloud.app.data_platform.analytics.bi_view` 导入 `BIViewService`

**修改：** 在 `cloud/app/app_setup.py` 中注册 `app.include_router(data_platform_router)`

## 2. P0-5：BIReportRequest 默认值不匹配

**文件：** `cloud/app/data_platform/schemas/data_platform.py` 第77行

将 `BIReportRequest.group_by` 的默认值从 `["date", "team"]` 改为 `["activity_date", "team_id"]`，匹配 `bi_view.py` 中实际使用的列名。

## 3. P0-6：anomaly_detector.py 样本标准差公式

**文件：** `cloud/app/crawler/analysis/anomaly_detector.py` 第31行

将 `variance = sum((price - mean) ** 2 for price in prices) / len(prices)` 改为：
```python
n = len(prices)
if n <= 1:
    return 0.0
variance = sum((price - mean) ** 2 for price in prices) / (n - 1)
```
