"""Crawler scheduler built around APScheduler with an in-memory fallback."""

from __future__ import annotations

import inspect
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

try:
    from apscheduler.schedulers.background import BackgroundScheduler
except ModuleNotFoundError:  # pragma: no cover - exercised only when optional dependency is absent.
    BackgroundScheduler = None

from cloud.app.crawler.data_sources import get_source_config
from cloud.app.crawler.engine import Crawler, CrawlResult


@dataclass
class ScheduledCrawlerJob:
    """A single scheduled crawler job definition."""

    id: str
    source: str
    interval: int
    max_pages: int
    keywords: list[str]
    paused: bool = False
    next_run_time: datetime | None = None


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


class ScraperScheduler:
    """Manage scheduled competitor-intelligence crawler jobs."""

    def __init__(
        self,
        crawler: Crawler | None = None,
        event_bus: Any | None = None,
        autostart: bool = False,
    ) -> None:
        self.crawler = crawler or Crawler()
        self.event_bus = event_bus or LocalEventBus()
        self.jobs: dict[str, ScheduledCrawlerJob] = {}
        self._fallback_lock = threading.Lock()
        self._fallback_timers: dict[str, threading.Timer] = {}
        self._fallback_running: set[str] = set()
        self._scheduler = BackgroundScheduler() if BackgroundScheduler else None
        if autostart:
            self.start()

    def start(self) -> None:
        """Start the APScheduler background scheduler if available and not running."""
        if self._scheduler and not self._scheduler.running:
            self._scheduler.start()

    def shutdown(self) -> None:
        """Shutdown APScheduler and cancel all in-memory fallback timers."""
        if self._scheduler and self._scheduler.running:
            self._scheduler.shutdown(wait=False)
        with self._fallback_lock:
            for timer in self._fallback_timers.values():
                timer.cancel()
            self._fallback_timers.clear()
            self._fallback_running.clear()

    def add_job(
        self,
        source: str,
        interval: int,
        max_pages: int = 1,
        keywords: list[str] | None = None,
    ) -> str:
        """Register a new periodic crawler job and return its job id.

        Args:
            source: Source type name (weibo, bidding, etc.).
            interval: Interval in seconds between runs.
            max_pages: Number of search result pages per run.
            keywords: Keywords to search for.

        Returns:
            A unique job id string.

        Raises:
            ValueError: If source is unknown or interval/max_pages <= 0.
        """
        get_source_config(source)
        if interval <= 0:
            raise ValueError("interval must be greater than 0 seconds")
        if max_pages <= 0:
            raise ValueError("max_pages must be greater than 0")
        job_id = f"crawl:{source}:{uuid.uuid4().hex[:12]}"
        job = ScheduledCrawlerJob(
            id=job_id,
            source=source,
            interval=interval,
            max_pages=max_pages,
            keywords=keywords or [],
        )
        self.jobs[job_id] = job
        if self._scheduler:
            if not self._scheduler.running:
                self._scheduler.start()
            aps_job = self._scheduler.add_job(
                self._run_job,
                "interval",
                seconds=interval,
                id=job_id,
                args=[job_id],
                replace_existing=True,
            )
            job.next_run_time = aps_job.next_run_time
        else:
            self._schedule_fallback(job_id)
        return job_id

    def remove_job(self, job_id: str) -> None:
        """Remove a crawler job by id, cancelling its timer/schedule.

        Raises:
            ValueError: If job_id is unknown.
        """
        if job_id not in self.jobs:
            raise ValueError(f"Unknown crawler job: {job_id}")
        if self._scheduler and self._scheduler.get_job(job_id):
            self._scheduler.remove_job(job_id)
        with self._fallback_lock:
            timer = self._fallback_timers.pop(job_id, None)
            if timer:
                timer.cancel()
        self.jobs.pop(job_id, None)

    def pause_job(self, job_id: str) -> None:
        """Pause a crawler job without removing it.

        Raises:
            ValueError: If job_id is unknown.
        """
        job = self._require_job(job_id)
        job.paused = True
        if self._scheduler and self._scheduler.get_job(job_id):
            self._scheduler.pause_job(job_id)
        with self._fallback_lock:
            timer = self._fallback_timers.pop(job_id, None)
            if timer:
                timer.cancel()

    def resume_job(self, job_id: str) -> None:
        """Resume a paused crawler job.

        Raises:
            ValueError: If job_id is unknown.
        """
        job = self._require_job(job_id)
        job.paused = False
        if self._scheduler and self._scheduler.get_job(job_id):
            self._scheduler.resume_job(job_id)
        elif not self._scheduler:
            self._schedule_fallback(job_id)

    # -- internal helpers ------------------------------------------------------

    def _run_job(self, job_id: str) -> list[CrawlResult]:
        # Execute one scheduled run for the given job, publishing results on completion.
        job = self._require_job(job_id)
        if job.paused:
            return []
        config = get_source_config(job.source)
        results = []
        for keyword in job.keywords or [""]:
            for page in range(1, job.max_pages + 1):
                url = config.build_search_url(keyword, page)
                results.append(self.crawler.crawl(url, job.source))
        self._publish_completed(job, results)
        return results

    def _publish_completed(self, job: ScheduledCrawlerJob, results: list[CrawlResult]) -> None:
        # Build and publish a crawl.completed event with result summaries.
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
        self._publish_event("crawl.completed", payload)

    def _publish_event(self, event_type: str, payload: dict[str, Any]) -> None:
        # Dispatch event through the event_bus adaptor (supports publish / publish_message).
        if hasattr(self.event_bus, "publish"):
            maybe_result = self.event_bus.publish(event_type, payload)
            if inspect.isawaitable(maybe_result):
                raise RuntimeError("Async event bus publish is not supported in the sync scheduler")
            return
        if hasattr(self.event_bus, "publish_message"):
            self.event_bus.publish_message(
                event_type=event_type,
                source_entity_type="crawler_job",
                source_entity_id=payload["job_id"],
                payload=payload,
                correlation_id=payload["job_id"],
            )
            return
        raise TypeError("event_bus must expose publish() or publish_message()")

    def _schedule_fallback(self, job_id: str) -> None:
        # Schedule the next run via threading.Timer when APScheduler is not available.
        job = self._require_job(job_id)
        if job.paused:
            return

        def runner() -> None:
            try:
                self._run_job(job_id)
            finally:
                with self._fallback_lock:
                    self._fallback_running.discard(job_id)
                if job_id in self.jobs and not self.jobs[job_id].paused:
                    self._schedule_fallback(job_id)

        with self._fallback_lock:
            if job_id in self._fallback_running:
                return
            self._fallback_running.add(job_id)
            old_timer = self._fallback_timers.pop(job_id, None)
            if old_timer:
                old_timer.cancel()
            timer = threading.Timer(job.interval, runner)
            timer.daemon = True
            self._fallback_timers[job_id] = timer
            job.next_run_time = datetime.now(timezone.utc) + timedelta(seconds=job.interval)
        timer.start()

    def _require_job(self, job_id: str) -> ScheduledCrawlerJob:
        # Look up a job by id, raising ValueError if not found.
        try:
            return self.jobs[job_id]
        except KeyError as exc:
            raise ValueError(f"Unknown crawler job: {job_id}") from exc


__all__ = ["LocalEventBus", "ScheduledCrawlerJob", "ScraperScheduler"]
