"""Scheduled crawl job manager using APScheduler."""

from __future__ import annotations

from datetime import timezone
from typing import Any, Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger


class CrawlerScheduler:
    """APScheduler-based scheduler for periodic crawl jobs.

    Supports per-source cron expressions or interval-based frequency.
    """

    def __init__(self):
        self._scheduler = AsyncIOScheduler()
        self._jobs: dict[str, str] = {}

    def start(self) -> None:
        """Start the scheduler."""
        if not self._scheduler.running:
            self._scheduler.start()

    def stop(self) -> None:
        """Stop the scheduler and remove all jobs."""
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)
        self._jobs.clear()

    def add_cron_job(
        self, job_id: str, func: Callable, cron_expr: str,
        args: list[Any] | None = None, kwargs: dict[str, Any] | None = None,
    ) -> str | None:
        """Add a job with a cron expression (e.g. '0 6 * * *' for daily 6am)."""
        if job_id in self._jobs:
            return None
        parts = cron_expr.strip().split()
        if len(parts) != 5:
            return None
        trigger = CronTrigger(
            minute=parts[0], hour=parts[1], day=parts[2],
            month=parts[3], day_of_week=parts[4],
            timezone=timezone.utc,
        )
        self._scheduler.add_job(func, trigger, args=args or [], kwargs=kwargs or {}, id=job_id)
        self._jobs[job_id] = job_id
        return job_id

    def add_interval_job(
        self, job_id: str, func: Callable, minutes: int,
        args: list[Any] | None = None, kwargs: dict[str, Any] | None = None,
    ) -> str | None:
        """Add a job with an interval in minutes."""
        if job_id in self._jobs:
            return None
        trigger = IntervalTrigger(minutes=minutes, timezone=timezone.utc)
        self._scheduler.add_job(func, trigger, args=args or [], kwargs=kwargs or {}, id=job_id)
        self._jobs[job_id] = job_id
        return job_id

    def remove_job(self, job_id: str) -> bool:
        """Remove a scheduled job by id."""
        if job_id not in self._jobs:
            return False
        self._scheduler.remove_job(job_id)
        del self._jobs[job_id]
        return True

    def get_jobs(self) -> list[dict[str, Any]]:
        """Return list of scheduled job info."""
        return [{"id": jid, "next_run": str(j.next_run_time) if j.next_run_time else ""} for jid, j in self._jobs.items()]

    def running(self) -> bool:
        return self._scheduler.running
