from typing import Any

from fastapi import APIRouter, Body, Depends

from cloud.app.data_platform.analytics.bi_view import BIViewService
from cloud.app.data_platform.analytics.olap_service import OLAPService
from cloud.app.data_platform.etl.pipeline import ETLPipeline
from cloud.app.data_platform.schemas.data_platform import OLAPQuery, PipelineRunResult
from shared.auth_scope import require_scope
from shared.base import success

router = APIRouter(prefix="/api/data-platform", tags=["data-platform"])


@router.post(
    "/pipeline/run",
    response_model=PipelineRunResult,
    summary="执行ETL管道",
    description="启动数据平台ETL管道，从数据源提取、转换并加载至数据仓库。",
    tags=["data-platform"],
)
def run_pipeline(
    current_user: dict = Depends(require_scope("visit")),
    pipeline: ETLPipeline = Depends(ETLPipeline),
) -> Any:
    result = pipeline.run()
    return success(data=result.dict())


@router.post(
    "/olap/query",
    summary="OLAP多维查询",
    description="在多维数据上执行聚合查询，支持自定义维度、度量和过滤条件。",
    tags=["data-platform"],
)
def olap_query(
    payload: OLAPQuery = Body(...),
    current_user: dict = Depends(require_scope("visit")),
) -> Any:
    service = OLAPService()
    rows = service.query(
        dimensions=payload.dimensions or None,
        metrics=None,
        filters=payload.filters,
        date_from=payload.date_from,
        date_to=payload.date_to,
        limit=payload.limit,
    )
    return success(data={"rows": rows, "count": len(rows)})


@router.get(
    "/bi/report",
    summary="嵌入式BI报表数据",
    description="获取聚合后的BI报表数据集，可按日期、团队等维度分组展示关键指标。",
    tags=["data-platform"],
)
def bi_report(
    date_from: str | None = None,
    date_to: str | None = None,
    team_id: str | None = None,
    current_user: dict = Depends(require_scope("visit")),
) -> Any:
    service = BIViewService()
    return success(data=service.report_data(date_from=date_from, date_to=date_to, team_id=team_id))
