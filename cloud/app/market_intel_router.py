from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from starlette import status
from shared.auth import get_current_user
from shared.base import success
from cloud.app.services.market_intel_service import MarketIntelService

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
def create_source(body: SourceCreate, current_user=Depends(get_current_user),
                  service: MarketIntelService = Depends()):
    uid = int(current_user["sub"])
    return success(data=service.create_source(body.name, body.source_type,
                                               body.target_keywords, uid))


@router.get("/sources")
def list_sources(
    source_type: Optional[str] = Query(None), is_active: Optional[int] = Query(None),
    current_user=Depends(get_current_user), service: MarketIntelService = Depends(),
):
    return success(data=service.list_sources(source_type=source_type, is_active=is_active))


@router.patch("/sources/{source_id}")
def update_source(source_id: int, body: SourceUpdate,
                  current_user=Depends(get_current_user), service: MarketIntelService = Depends()):
    return success(data=service.update_source(source_id, body.name, body.source_type,
                                               body.target_keywords, body.is_active))


@router.delete("/sources/{source_id}")
def delete_source(source_id: int, current_user=Depends(get_current_user),
                  service: MarketIntelService = Depends()):
    service.delete_source(source_id)
    return success()


@router.post("/sources/{source_id}/collect")
def collect_source(source_id: int, current_user=Depends(get_current_user),
                   service: MarketIntelService = Depends()):
    return success(data=service.collect_source(source_id, int(current_user["sub"])))


@router.get("/items")
def list_items(
    item_type: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    impact_level: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user), service: MarketIntelService = Depends(),
):
    return success(data=service.list_items(item_type=item_type, status_filter=status_filter,
                                            impact_level=impact_level, keyword=keyword,
                                            date_from=date_from, date_to=date_to,
                                            page=page, page_size=page_size))


@router.get("/items/{item_id}")
def get_item(item_id: int, current_user=Depends(get_current_user),
             service: MarketIntelService = Depends()):
    return success(data=service.get_item(item_id))


@router.patch("/items/{item_id}/status")
def update_item_status(item_id: int, body: ItemStatusUpdate,
                       current_user=Depends(get_current_user), service: MarketIntelService = Depends()):
    service.update_item_status(item_id, body.status)
    return success()


@router.post("/items/{item_id}/analyze")
def analyze_item(item_id: int, request: Request,
                 current_user=Depends(get_current_user), service: MarketIntelService = Depends()):
    return success(data=service.analyze_item(item_id, request))


@router.post("/collect-all")
def collect_all(current_user=Depends(get_current_user), service: MarketIntelService = Depends()):
    return success(data=service.collect_all(int(current_user["sub"])))


@router.get("/dashboard")
def dashboard(current_user=Depends(get_current_user), service: MarketIntelService = Depends()):
    return success(data=service.dashboard())
