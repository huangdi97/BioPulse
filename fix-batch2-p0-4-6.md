## P0-4：data_platform 未集成到应用中

文件：cloud/app/data_platform/

问题：整个 data_platform 包无任何外部消费者——无 router、无 service 导入。

改动：
1. 新建 cloud/app/routers/data_platform_router.py，暴露至少 3 个 API 端点：
   - POST /api/data-platform/pipeline/run — 执行ETL管道
   - POST /api/data-platform/olap/query — OLAP多维查询
   - GET /api/data-platform/bi/report — 嵌入式BI报表数据
2. 在 cloud/app/app_setup.py 中注册 router

验收：from cloud.app.routers.data_platform_router import router 通过。

## P0-5：data_platform BIReportRequest 默认值不匹配

文件：cloud/app/data_platform/schemas/data_platform.py

问题：BIReportRequest.group_by 默认值为 ["date", "team"]，但 bi_view.py 实际使用的列名为 ["activity_date", "team_id"]。

改动：将 schema 中的默认值改为 ["activity_date", "team_id"]。

验收：from cloud.app.data_platform.schemas.data_platform import BIReportRequest; r = BIReportRequest(); assert r.group_by == ["activity_date", "team_id"] 通过。

## P0-6：anomaly_detector.py 总体标准差而非样本标准差

文件：cloud/app/crawler/analysis/anomaly_detector.py 第31行

问题：variance = sum((price - mean) ** 2 for price in prices) / len(prices) 使用了总体标准差分母 /n。

改动：当 len(prices) > 1 时使用 /(n-1)，否则返回 0。

验收：python -c "from cloud.app.crawler.analysis.anomaly_detector import detect_anomaly; print(detect_anomaly('test'))" 通过。
