"""Clinical milestone notification and timeline services."""

from datetime import date, datetime, timezone

from fastapi.encoders import jsonable_encoder

from ..database import get_cache, set_cache
from ..schemas.milestone_tracker import MilestoneTimeline, SiteProgress
from .milestone_crud import build_gantt_items, get_site_milestones, get_trial_milestones


async def get_trial_timeline(trial_id: str) -> dict:
    cache_key = f"milestone:timeline:{trial_id}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    milestones = get_trial_milestones(trial_id)
    timeline = MilestoneTimeline(trial_id=trial_id, milestones=milestones, gantt_data=build_gantt_items(milestones))
    result = jsonable_encoder(timeline)
    result["last_updated"] = datetime.now(timezone.utc).isoformat()
    set_cache(cache_key, result, ttl=600)
    return result


async def get_site_progress(site_id: str) -> dict:
    cache_key = f"milestone:site:{site_id}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    milestones = get_site_milestones(site_id)
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
    cache_key = f"milestone:gantt:{trial_id}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    milestones = get_trial_milestones(trial_id)
    gantt_items = build_gantt_items(milestones)
    result = {
        "trial_id": trial_id,
        "gantt_data": jsonable_encoder(gantt_items),
        "legend": {"done": "已完成", "in_progress": "进行中", "planned": "计划中", "overdue": "已逾期"},
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }
    set_cache(cache_key, result, ttl=600)
    return result
