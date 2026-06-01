import asyncio
import logging
import sqlite3
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler

from assistant.app.database import DB_PATH
from assistant.app.ws_manager import connection_manager

logger = logging.getLogger(__name__)
reminder_scheduler = BackgroundScheduler()


def _send_ws(user_id: int, message: dict) -> None:
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(connection_manager.send_to_user(user_id, message))
        loop.close()
    except Exception as e:
        logger.warning("WS send failed: %s", e)


def check_reminders() -> int:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    now = datetime.now(timezone.utc).isoformat()
    rows = conn.execute("""
        SELECT * FROM surgery_reminder
        WHERE status='scheduled' AND is_active=1
        AND (notification_status IS NULL OR notification_status='pending')
        AND date(surgery_date) <= date('now', '+1 day')
        AND date(surgery_date) >= date('now')
    """).fetchall()
    count = 0
    for row in rows:
        r = dict(row)
        _send_ws(
            r["created_by"],
            {
                "type": "surgery_reminder",
                "title": "手术提醒",
                "body": f"{r['patient_name']} · {r.get('surgery_type', '手术')} · {r.get('hospital', '')}",
                "surgery_id": r["id"],
                "surgery_date": r.get("surgery_date", ""),
            },
        )
        conn.execute(
            "UPDATE surgery_reminder SET last_notified_at=?, notification_status=? WHERE id=?",
            (now, "sent", r["id"]),
        )
        count += 1
    conn.commit()
    conn.close()
    logger.info("Reminder check: %d triggered", count)
    return count


def start_scheduler():
    reminder_scheduler.add_job(check_reminders, "interval", minutes=30)
    reminder_scheduler.start()
    logger.info("Reminder scheduler started")
