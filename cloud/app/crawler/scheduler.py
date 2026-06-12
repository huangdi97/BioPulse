"""Crawler scheduler built around APScheduler with an in-memory fallback."""

from __future__ import annotations

import threading
import uuid
from typing import Any

try:
    from apscheduler.schedulers.background import BackgroundScheduler
except ModuleNotFoundError:  # pragma: no cover - exercised only when optional dependency is absent.
    BackgroundScheduler = None

from cloud.app.crawler.crawl_executor import (
    LocalEventBus,
    require_job,
    run_job,
    schedule_fallback,
)
from cloud.app.crawler.crawl_task import ScheduledCrawlerJob
from cloud.app.crawler.data_sources import get_source_config
from cloud.app.crawler.engine import Crawler


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
                self._run_job_wrapper,
                "interval",
                seconds=interval,
                id=job_id,
                args=[job_id],
                replace_existing=True,
            )
            job.next_run_time = aps_job.next_run_time
        else:
            schedule_fallback(
                self.jobs,
                self._fallback_lock,
                self._fallback_timers,
                self._fallback_running,
                self.crawler,
                self.event_bus,
                job_id,
            )
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
        job = require_job(self.jobs, job_id)
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
        job = require_job(self.jobs, job_id)
        job.paused = False
        if self._scheduler and self._scheduler.get_job(job_id):
            self._scheduler.resume_job(job_id)
        elif not self._scheduler:
            schedule_fallback(
                self.jobs,
                self._fallback_lock,
                self._fallback_timers,
                self._fallback_running,
                self.crawler,
                self.event_bus,
                job_id,
            )

    # -- internal helpers ------------------------------------------------------

    def _run_job_wrapper(self, job_id: str) -> list:
        return run_job(self.jobs, self.crawler, self.event_bus, job_id)


__all__ = ["ScraperScheduler"]
