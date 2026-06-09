"""临床试验里程碑跟踪服务。"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from fastapi.encoders import jsonable_encoder

from ..database import get_cache, set_cache
from ..schemas.milestone_tracker import ClinicalMilestone, GanttItem, MilestoneTimeline, SiteProgress

_MILESTONES = [
    {
        "id": "ms-001",
        "trial_id": "trial-001",
        "site_id": "site-001",
        "milestone_type": "screening",
        "planned_date": "2026-01-10",
        "actual_date": "2026-01-12",
        "status": "done",
    },
    {
        "id": "ms-002",
        "trial_id": "trial-001",
        "site_id": "site-001",
        "milestone_type": "initiation",
        "planned_date": "2026-02-05",
        "actual_date": "2026-02-05",
        "status": "done",
    },
    {
        "id": "ms-003",
        "trial_id": "trial-001",
        "site_id": "site-001",
        "milestone_type": "enrollment",
        "planned_date": "2026-03-01",
        "actual_date": None,
        "status": "in_progress",
    },
    {
        "id": "ms-004",
        "trial_id": "trial-001",
        "site_id": "site-001",
        "milestone_type": "closeout",
        "planned_date": "2026-08-20",
        "actual_date": None,
        "status": "planned",
    },
    {
        "id": "ms-005",
        "trial_id": "trial-001",
        "site_id": "site-002",
        "milestone_type": "screening",
        "planned_date": "2026-01-18",
        "actual_date": "2026-01-16",
        "status": "done",
    },
    {
        "id": "ms-006",
        "trial_id": "trial-001",
        "site_id": "site-002",
        "milestone_type": "initiation",
        "planned_date": "2026-02-15",
        "actual_date": "2026-02-20",
        "status": "done",
    },
    {
        "id": "ms-007",
        "trial_id": "trial-001",
        "site_id": "site-002",
        "milestone_type": "enrollment",
        "planned_date": "2026-03-20",
        "actual_date": None,
        "status": "in_progress",
    },
    {
        "id": "ms-008",
        "trial_id": "trial-001",
        "site_id": "site-002",
        "milestone_type": "closeout",
        "planned_date": "2026-09-05",
        "actual_date": None,
        "status": "planned",
    },
]

_MILESTONE_DURATION_DAYS = {
    "screening": 14,
    "initiation": 7,
    "enrollment": 90,
    "closeout": 21,
}


async def get_trial_timeline(trial_id: str) -> dict:
    """获取试验里程碑时间线。"""
    cache_key = f"milestone:timeline:{trial_id}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    milestones = _get_trial_milestones(trial_id)
    timeline = MilestoneTimeline(
        trial_id=trial_id,
        milestones=milestones,
        gantt_data=_build_gantt_items(milestones),
    )
    result = jsonable_encoder(timeline)
    result["last_updated"] = datetime.now(timezone.utc).isoformat()
    set_cache(cache_key, result, ttl=600)
    return result


async def get_site_progress(site_id: str) -> dict:
    """获取中心里程碑进展。"""
    cache_key = f"milestone:site:{site_id}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    raw_items = [item for item in _MILESTONES if item["site_id"] == site_id]
    if not raw_items:
        raw_items = _build_default_site_milestones(site_id)

    milestones = [_to_milestone(item) for item in raw_items]
    completed = sum(1 for item in milestones if item.status == "done")
    overdue = sum(1 for item in milestones if item.status != "done" and item.planned_date < date.today())
    next_milestone = next((item.milestone_type for item in milestones if item.status != "done"), None)

    progress = SiteProgress(
        site_id=site_id,
        trial_id=milestones[0].trial_id,
        total_milestones=len(milestones),
        completed_milestones=completed,
        progress_pct=round(completed / len(milestones) * 100, 2),
        current_status="delayed" if overdue else "on_track",
        next_milestone=next_milestone,
        overdue_count=overdue,
    )
    result = jsonable_encoder(progress)
    result["last_updated"] = datetime.now(timezone.utc).isoformat()
    set_cache(cache_key, result, ttl=600)
    return result


async def get_gantt_data(trial_id: str) -> dict:
    """获取 Gantt 图渲染数据。"""
    cache_key = f"milestone:gantt:{trial_id}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    milestones = _get_trial_milestones(trial_id)
    gantt_items = _build_gantt_items(milestones)
    result = {
        "trial_id": trial_id,
        "gantt_data": jsonable_encoder(gantt_items),
        "legend": {
            "done": "已完成",
            "in_progress": "进行中",
            "planned": "计划中",
            "overdue": "已逾期",
        },
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }
    set_cache(cache_key, result, ttl=600)
    return result


def _get_trial_milestones(trial_id: str) -> list[ClinicalMilestone]:
    raw_items = [item for item in _MILESTONES if item["trial_id"] == trial_id]
    if not raw_items:
        raw_items = _build_default_trial_milestones(trial_id)
    return [_to_milestone(item) for item in raw_items]


def _to_milestone(item: dict) -> ClinicalMilestone:
    planned_date = date.fromisoformat(item["planned_date"])
    actual_date = date.fromisoformat(item["actual_date"]) if item.get("actual_date") else None
    variance_days = (actual_date - planned_date).days if actual_date else (date.today() - planned_date).days

    return ClinicalMilestone(
        id=item["id"],
        trial_id=item["trial_id"],
        site_id=item["site_id"],
        milestone_type=item["milestone_type"],
        planned_date=planned_date,
        actual_date=actual_date,
        status=item["status"],
        variance_days=variance_days,
    )


def _build_gantt_items(milestones: list[ClinicalMilestone]) -> list[GanttItem]:
    gantt_items = []
    for item in milestones:
        duration = _MILESTONE_DURATION_DAYS[item.milestone_type]
        start = item.planned_date
        end = start + timedelta(days=duration)
        status = item.status
        if status != "done" and item.planned_date < date.today():
            status = "overdue"

        gantt_items.append(
            GanttItem(
                id=item.id,
                milestone=item.milestone_type,
                site_id=item.site_id,
                start=start,
                end=end,
                progress=_progress_for_status(status),
                status=status,
            )
        )
    return gantt_items


def _progress_for_status(status: str) -> int:
    return {
        "done": 100,
        "in_progress": 55,
        "overdue": 35,
        "planned": 0,
    }.get(status, 0)


def _build_default_trial_milestones(trial_id: str) -> list[dict]:
    return [
        {
            "id": f"{trial_id}-ms-{index + 1:03d}",
            "trial_id": trial_id,
            "site_id": f"site-{index // 4 + 1:03d}",
            "milestone_type": milestone_type,
            "planned_date": planned_date,
            "actual_date": None,
            "status": "planned",
        }
        for index, (milestone_type, planned_date) in enumerate(
            [
                ("screening", "2026-02-01"),
                ("initiation", "2026-02-20"),
                ("enrollment", "2026-03-15"),
                ("closeout", "2026-09-30"),
            ]
        )
    ]


def _build_default_site_milestones(site_id: str) -> list[dict]:
    return [
        {
            "id": f"{site_id}-ms-{index + 1:03d}",
            "trial_id": "trial-001",
            "site_id": site_id,
            "milestone_type": milestone_type,
            "planned_date": planned_date,
            "actual_date": None,
            "status": "planned",
        }
        for index, (milestone_type, planned_date) in enumerate(
            [
                ("screening", "2026-02-01"),
                ("initiation", "2026-02-20"),
                ("enrollment", "2026-03-15"),
                ("closeout", "2026-09-30"),
            ]
        )
    ]
