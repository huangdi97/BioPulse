"""Clinical milestone data access and transformation."""

from datetime import date, timedelta

from ..schemas.milestone_tracker import ClinicalMilestone, GanttItem

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

_MILESTONE_DURATION_DAYS = {"screening": 14, "initiation": 7, "enrollment": 90, "closeout": 21}


def get_trial_milestones(trial_id: str) -> list[ClinicalMilestone]:
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


def build_gantt_items(milestones: list[ClinicalMilestone]) -> list[GanttItem]:
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
    return {"done": 100, "in_progress": 55, "overdue": 35, "planned": 0}.get(status, 0)


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
            [("screening", "2026-02-01"), ("initiation", "2026-02-20"), ("enrollment", "2026-03-15"), ("closeout", "2026-09-30")]
        )
    ]


def get_site_milestones(site_id: str) -> list[ClinicalMilestone]:
    raw_items = [item for item in _MILESTONES if item["site_id"] == site_id]
    if not raw_items:
        raw_items = _build_default_site_milestones(site_id)
    return [_to_milestone(item) for item in raw_items]


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
            [("screening", "2026-02-01"), ("initiation", "2026-02-20"), ("enrollment", "2026-03-15"), ("closeout", "2026-09-30")]
        )
    ]
