"""竞品爬虫管理 API 路由。"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from starlette import status

from cloud.app.competitor_crawler import CrawlerEngine, CrawlerScheduler, CrawlerStorage, DataPipeline
from cloud.app.competitor_crawler.sources import list_sources
from shared.auth_scope import require_scope
from shared.base import success

router = APIRouter(prefix="/api/crawler", tags=["竞品爬虫"])

_engine = CrawlerEngine()
_scheduler = CrawlerScheduler()
_storage = CrawlerStorage()
_pipeline = DataPipeline()
_crawl_results: dict[str, dict[str, Any]] = {}


class CrawlStartRequest(BaseModel):
    keyword: str
    sources: list[str] = ["news"]
    url: str = ""


class CrawlStatusResponse(BaseModel):
    source: str
    running: bool
    total_jobs: int


@router.post("/start", tags=["竞品爬虫"])
async def start_crawl(req: CrawlStartRequest, _: dict = Depends(require_scope("visit"))) -> dict[str, Any]:
    """启动抓取任务。"""
    url = req.url or f"https://news.google.com/search?q={req.keyword}"
    result = await _engine.crawl(url, req.sources[0] if req.sources else "news")
    processed = _pipeline.process(result.content, result.source)
    record_id = _storage.save_metadata(result.source, req.keyword, url, processed)
    _storage.save_log(result.source, url, result.status_code, result.success)
    _crawl_results[result.source] = {
        "id": record_id,
        "source": result.source,
        "url": url,
        "keyword": req.keyword,
        "success": result.success,
        "content_preview": result.content[:200],
        "word_count": processed.get("word_count", 0),
    }
    return success(data={"status": "started", "result": _crawl_results[result.source]})


@router.post("/stop/{source}", tags=["竞品爬虫"])
async def stop_crawl(source: str, _: dict = Depends(require_scope("visit"))) -> dict[str, str]:
    """停止指定源的抓取任务。"""
    removed = _scheduler.remove_job(f"crawl:{source}")
    if not removed:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Source '{source}' not running")
    return success(data={"status": "stopped", "source": source})


@router.get("/status", tags=["竞品爬虫"])
async def crawl_status(current_user: dict = Depends(require_scope("visit"))) -> list[dict[str, Any]]:
    """查看所有源的抓取状态。"""
    sources = list_sources()
    jobs = _scheduler.get_jobs()
    return [
        {"name": name, "cron": cfg.crawl_frequency_minutes, "enabled": True, "scheduled": f"{cfg.name}" in str(jobs)}
        for name, cfg in sources.items()
    ]


@router.get("/data/{source}", tags=["竞品爬虫"])
async def get_crawl_data(
    source: str,
    keyword: str = Query("", description="搜索关键字"),
    limit: int = Query(50, ge=1, le=500),
    current_user: dict = Depends(require_scope("visit")),
) -> list[dict[str, Any]]:
    """查看指定源的抓取数据。"""
    if keyword:
        return _storage.get_metadata(source, keyword, limit)
    logs = _storage.get_logs(source, limit)
    return logs


@router.delete("/data/{record_id}", tags=["竞品爬虫"])
async def delete_crawl_data(record_id: int, _: dict = Depends(require_scope("visit"))) -> dict[str, Any]:
    """删除单条抓取记录。"""
    deleted = _storage.delete_record(record_id)
    if not deleted:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Record {record_id} not found")
    return success(data={"status": "deleted", "record_id": record_id})
