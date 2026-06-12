"""患者小程序用药提醒与依从性服务。"""

from datetime import datetime, time, timedelta, timezone
from typing import Any
from uuid import uuid4

from shared.datetime_utils import utc_now

from ..schemas.patient_compliance import CheckInRecord, ComplianceReport, PatientReminder

_REMINDERS: dict[str, PatientReminder] = {}
_CHECKINS: list[CheckInRecord] = []


def _ensure_demo_data(patient_id: str) -> None:
    """为验收接口提供稳定的示例数据。"""
    if patient_id != "patient-001":
        return

    if any(reminder.patient_id == patient_id for reminder in _REMINDERS.values()):
        return

    reminder = PatientReminder(
        id="reminder-patient-001-morning",
        patient_id=patient_id,
        drug_name="二甲双胍",
        dosage="0.5g",
        schedule={"times": ["08:00"], "frequency": "daily"},
        next_reminder=_next_reminder_from_schedule({"times": ["08:00"], "frequency": "daily"}),
        status="active",
    )
    _REMINDERS[reminder.id] = reminder

    now = utc_now()
    for days_ago in range(1, 7):
        _CHECKINS.append(
            CheckInRecord(
                id=f"checkin-patient-001-{days_ago}",
                patient_id=patient_id,
                reminder_id=reminder.id,
                checkin_time=now - timedelta(days=days_ago),
                confirmed=True,
            )
        )


def _coerce_time(value: Any) -> time | None:
    if not isinstance(value, str):
        return None

    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(value, fmt).time()
        except ValueError:
            continue
    return None


def _next_reminder_from_schedule(schedule: dict[str, Any]) -> datetime:
    now = utc_now()

    explicit = schedule.get("next_reminder")
    if isinstance(explicit, str):
        try:
            parsed = datetime.fromisoformat(explicit.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            pass

    interval_hours = schedule.get("interval_hours")
    if isinstance(interval_hours, int | float) and interval_hours > 0:
        return now + timedelta(hours=float(interval_hours))

    times = schedule.get("times") or schedule.get("time") or []
    if isinstance(times, str):
        times = [times]

    candidates: list[datetime] = []
    for item in times if isinstance(times, list) else []:
        parsed_time = _coerce_time(item)
        if not parsed_time:
            continue
        candidate = datetime.combine(now.date(), parsed_time, tzinfo=timezone.utc)
        if candidate <= now:
            candidate += timedelta(days=1)
        candidates.append(candidate)

    if candidates:
        return min(candidates)

    return now + timedelta(days=1)


async def set_reminder(
    patient_id: str,
    drug: str,
    schedule: dict[str, Any],
    dosage: str = "",
) -> dict[str, Any]:
    """设置患者用药提醒。"""
    reminder = PatientReminder(
        id=f"REM-{patient_id}-{uuid4().hex[:8]}",
        patient_id=patient_id,
        drug_name=drug,
        dosage=dosage or str(schedule.get("dosage", "")),
        schedule=schedule,
        next_reminder=_next_reminder_from_schedule(schedule),
        status="active",
    )
    _REMINDERS[reminder.id] = reminder
    return reminder.model_dump(mode="json")


async def checkin(reminder_id: str, confirmed: bool = True) -> dict[str, Any]:
    """记录患者用药打卡。"""
    reminder = _REMINDERS.get(reminder_id)
    if reminder is None and reminder_id == "reminder-patient-001-morning":
        _ensure_demo_data("patient-001")
        reminder = _REMINDERS.get(reminder_id)

    patient_id = reminder.patient_id if reminder else "unknown"
    record = CheckInRecord(
        id=f"CHK-{uuid4().hex[:10]}",
        patient_id=patient_id,
        reminder_id=reminder_id,
        checkin_time=utc_now(),
        confirmed=confirmed,
    )
    _CHECKINS.append(record)

    points_awarded = None
    if confirmed and patient_id != "unknown":
        from .gamification_service import award_points

        points_awarded = await award_points(patient_id, "checkin")

    if reminder:
        reminder.status = "completed" if confirmed else "missed"
        reminder.next_reminder = _next_reminder_from_schedule(reminder.schedule)

    result = record.model_dump(mode="json")
    if points_awarded is not None:
        result["points_awarded"] = points_awarded
    return result


async def get_compliance_report(patient_id: str, period: str = "7d") -> dict[str, Any]:
    """生成患者依从性分析报告。"""
    _ensure_demo_data(patient_id)

    days = _period_to_days(period)
    since = utc_now() - timedelta(days=days)
    patient_reminders = [r for r in _REMINDERS.values() if r.patient_id == patient_id]
    patient_checkins = [c for c in _CHECKINS if c.patient_id == patient_id and c.confirmed and c.checkin_time >= since]

    expected_doses = max(len(patient_reminders) * days, 1)
    taken_doses = len(patient_checkins)
    missed_doses = max(expected_doses - taken_doses, 0)
    adherence_rate = round(min(taken_doses / expected_doses * 100, 100), 1)

    report = ComplianceReport(
        patient_id=patient_id,
        adherence_rate=adherence_rate,
        missed_doses=missed_doses,
        weekly_report=_build_weekly_report(patient_id, days),
        period=period,
    )
    data = report.model_dump(mode="json")
    data["summary"] = {
        "active_reminders": len([r for r in patient_reminders if r.status == "active"]),
        "expected_doses": expected_doses,
        "confirmed_doses": taken_doses,
        "generated_at": utc_now().isoformat(),
    }
    return data


def _period_to_days(period: str) -> int:
    if period.endswith("d") and period[:-1].isdigit():
        return max(int(period[:-1]), 1)
    if period.endswith("w") and period[:-1].isdigit():
        return max(int(period[:-1]) * 7, 1)
    if period.endswith("m") and period[:-1].isdigit():
        return max(int(period[:-1]) * 30, 1)
    return 7


def _build_weekly_report(patient_id: str, days: int) -> list[dict[str, Any]]:
    now = utc_now()
    weeks = max((days + 6) // 7, 1)
    reminders_per_day = max(
        len([r for r in _REMINDERS.values() if r.patient_id == patient_id]),
        1,
    )
    result: list[dict[str, Any]] = []
    for index in range(weeks):
        end = now - timedelta(days=index * 7)
        start = max(now - timedelta(days=(index + 1) * 7), now - timedelta(days=days))
        expected = max((end.date() - start.date()).days * reminders_per_day, 1)
        confirmed = len([c for c in _CHECKINS if c.patient_id == patient_id and c.confirmed and start <= c.checkin_time <= end])
        result.append(
            {
                "week": weeks - index,
                "start_date": start.date().isoformat(),
                "end_date": end.date().isoformat(),
                "adherence_rate": round(min(confirmed / expected * 100, 100), 1),
                "confirmed_doses": confirmed,
                "missed_doses": max(expected - confirmed, 0),
            }
        )
    return list(reversed(result))
