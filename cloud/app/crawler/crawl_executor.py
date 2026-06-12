"""爬虫执行逻辑 — LocalEventBus 与执行辅助函数。"""

from __future__ import annotations

import inspect
import threading
from datetime import datetime, timedelta, timezone
from typing import Any

from cloud.app.crawler.crawl_task import ScheduledCrawlerJob


class LocalEventBus:
    """Small event bus adapter used when the application EventBus is unavailable."""

    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def publish(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Record and return a local event for later inspection."""
        event = {
            "event_type": event_type,
            "payload": payload,
            "published_at": datetime.now(timezone.utc).isoformat(),
        }
        self.events.append(event)
        return event


def require_job(jobs: dict[str, ScheduledCrawlerJob], job_id: str) -> ScheduledCrawlerJob:
    """Look up a job by id, raising ValueError if not found."""
    try:
        return jobs[job_id]
    except KeyError as exc:
        raise ValueError(f"Unknown crawler job: {job_id}") from exc


def run_job(
    jobs: dict[str, ScheduledCrawlerJob],
    crawler: Any,
    event_bus: Any,
    job_id: str,
) -> list:
    """Execute one scheduled run for the given job, publishing results on completion."""
    job = require_job(jobs, job_id)
    if job.paused:
        return []
    from cloud.app.crawler.data_sources import get_source_config
    from cloud.app.crawler.engine import CrawlResult

    config = get_source_config(job.source)
    results: list[CrawlResult] = []
    for keyword in job.keywords or [""]:
        for page in range(1, job.max_pages + 1):
            url = config.build_search_url(keyword, page)
            results.append(crawler.crawl(url, job.source))
    publish_completed(event_bus, job, results)
    return results


def publish_completed(event_bus: Any, job: ScheduledCrawlerJob, results: list) -> None:
    """Build and publish a crawl.completed event with result summaries."""
    payload = {
        "job_id": job.id,
        "source": job.source,
        "keywords": job.keywords,
        "max_pages": job.max_pages,
        "result_count": len(results),
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "items": [
            {
                "source": result.source,
                "timestamp": result.timestamp.isoformat(),
                "metadata": result.metadata,
                "content_length": len(result.content),
            }
            for result in results
        ],
    }
    publish_event(event_bus, "crawl.completed", payload)


def publish_event(event_bus: Any, event_type: str, payload: dict[str, Any]) -> None:
    """Dispatch event through the event_bus adaptor (supports publish / publish_message)."""
    if hasattr(event_bus, "publish"):
        maybe_result = event_bus.publish(event_type, payload)
        if inspect.isawaitable(maybe_result):
            raise RuntimeError("Async event bus publish is not supported in the sync scheduler")
        return
    if hasattr(event_bus, "publish_message"):
        event_bus.publish_message(
            event_type=event_type,
            source_entity_type="crawler_job",
            source_entity_id=payload["job_id"],
            payload=payload,
            correlation_id=payload["job_id"],
        )
        return
    raise TypeError("event_bus must expose publish() or publish_message()")


def schedule_fallback(
    jobs: dict[str, ScheduledCrawlerJob],
    fallback_lock: threading.Lock,
    fallback_timers: dict[str, threading.Timer],
    fallback_running: set[str],
    crawler: Any,
    event_bus: Any,
    job_id: str,
) -> None:
    """Schedule the next run via threading.Timer when APScheduler is not available."""
    job = require_job(jobs, job_id)
    if job.paused:
        return

    def runner() -> None:
        try:
            run_job(jobs, crawler, event_bus, job_id)
        finally:
            with fallback_lock:
                fallback_running.discard(job_id)
            if job_id in jobs and not jobs[job_id].paused:
                schedule_fallback(
                    jobs,
                    fallback_lock,
                    fallback_timers,
                    fallback_running,
                    crawler,
                    event_bus,
                    job_id,
                )

    with fallback_lock:
        if job_id in fallback_running:
            return
        fallback_running.add(job_id)
        old_timer = fallback_timers.pop(job_id, None)
        if old_timer:
            old_timer.cancel()
        timer = threading.Timer(job.interval, runner)
        timer.daemon = True
        fallback_timers[job_id] = timer
        job.next_run_time = datetime.now(timezone.utc) + timedelta(seconds=job.interval)
    timer.start()
