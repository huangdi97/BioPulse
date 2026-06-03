from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel
from starlette import status

from cloud.app.services.market_intel_service import MarketIntelService
from shared.auth_scope import require_scope
from shared.base import success

router = APIRouter(prefix="/market-intel", tags=["Market Intel"])


class SourceCreate(BaseModel):
    name: str
    source_type: str = "competitor"
    target_keywords: list = []


class SourceUpdate(BaseModel):
    name: Optional[str] = None
    source_type: Optional[str] = None
    target_keywords: Optional[list] = None
    is_active: Optional[int] = None


class ItemStatusUpdate(BaseModel):
    status: str


@router.post("/sources", status_code=status.HTTP_201_CREATED)
def create_source(
    body: SourceCreate,
    current_user=Depends(require_scope("visit")),
    service: MarketIntelService = Depends(),
):
    """创建市场情报源。

    Args:
        body: 源创建参数（名称、类型、关键词）。

    Returns:
        创建的情报源信息。
    """
    uid = int(current_user["sub"])
    return success(data=service.create_source(body.name, body.source_type, body.target_keywords, uid))


@router.get("/sources")
def list_sources(
    source_type: Optional[str] = Query(None),
    is_active: Optional[int] = Query(None),
    current_user=Depends(require_scope("visit")),
    service: MarketIntelService = Depends(),
):
    """获取情报源列表。

    Args:
        source_type: 按类型筛选。
        is_active: 按启用状态筛选。

    Returns:
        情报源列表。
    """
    return success(data=service.list_sources(source_type=source_type, is_active=is_active))


@router.patch("/sources/{source_id}")
def update_source(
    source_id: int,
    body: SourceUpdate,
    current_user=Depends(require_scope("visit")),
    service: MarketIntelService = Depends(),
):
    """更新情报源信息。

    Args:
        source_id: 情报源 ID。
        body: 更新字段。

    Returns:
        更新后的情报源信息。
    """
    return success(data=service.update_source(source_id, body.name, body.source_type, body.target_keywords, body.is_active))


@router.delete("/sources/{source_id}")
def delete_source(
    source_id: int,
    current_user=Depends(require_scope("visit")),
    service: MarketIntelService = Depends(),
):
    """删除指定情报源。

    Args:
        source_id: 要删除的情报源 ID。

    Returns:
        操作成功提示。
    """
    service.delete_source(source_id)
    return success()


@router.post("/sources/{source_id}/collect")
def collect_source(
    source_id: int,
    current_user=Depends(require_scope("visit")),
    service: MarketIntelService = Depends(),
):
    """手动采集指定情报源的数据。

    Args:
        source_id: 情报源 ID。

    Returns:
        采集结果。
    """
    return success(data=service.collect_source(source_id, int(current_user["sub"])))


@router.get("/items")
def list_items(
    item_type: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    impact_level: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(require_scope("visit")),
    service: MarketIntelService = Depends(),
):
    """分页查询情报条目。

    Args:
        item_type: 条目类型筛选。
        status_filter: 状态筛选。
        impact_level: 影响级别筛选。
        keyword: 关键词搜索。
        date_from/date_to: 日期范围。
        page/page_size: 分页参数。

    Returns:
        分页的情报条目列表。
    """
    return success(
        data=service.list_items(
            item_type=item_type,
            status_filter=status_filter,
            impact_level=impact_level,
            keyword=keyword,
            date_from=date_from,
            date_to=date_to,
            page=page,
            page_size=page_size,
        )
    )


@router.get("/items/{item_id}")
def get_item(
    item_id: int,
    current_user=Depends(require_scope("visit")),
    service: MarketIntelService = Depends(),
):
    """获取单条情报详情。

    Args:
        item_id: 情报条目 ID。

    Returns:
        情报条目详情。
    """
    return success(data=service.get_item(item_id))


@router.patch("/items/{item_id}/status")
def update_item_status(
    item_id: int,
    body: ItemStatusUpdate,
    current_user=Depends(require_scope("visit")),
    service: MarketIntelService = Depends(),
):
    """更新情报条目状态。

    Args:
        item_id: 情报条目 ID。
        body: 新状态。

    Returns:
        操作成功提示。
    """
    service.update_item_status(item_id, body.status)
    return success()


@router.post("/items/{item_id}/analyze")
def analyze_item(
    item_id: int,
    request: Request,
    current_user=Depends(require_scope("visit")),
    service: MarketIntelService = Depends(),
):
    """对指定情报条目执行 AI 分析。

    Args:
        item_id: 情报条目 ID。

    Returns:
        分析结果。
    """
    return success(data=service.analyze_item(item_id, request))


@router.post("/collect-all")
def collect_all(
    current_user=Depends(require_scope("visit")),
    service: MarketIntelService = Depends(),
):
    """触发全部活跃情报源的数据采集。

    Returns:
        各源采集结果汇总。
    """
    return success(data=service.collect_all(int(current_user["sub"])))


@router.get("/dashboard")
def dashboard(
    current_user=Depends(require_scope("visit")),
    service: MarketIntelService = Depends(),
):
    """获取市场情报仪表盘统计数据。

    Returns:
        情报统计概览。
    """
    return success(data=service.dashboard())
