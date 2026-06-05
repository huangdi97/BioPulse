import json

from cloud.app.research_database import get_research_db, log_research_audit


def get_audit_logs(page: int = 1, per_page: int = 20) -> list[dict]:
    db = get_research_db()
    try:
        offset = (page - 1) * per_page
        rows = db.execute(
            "SELECT * FROM research_audit_log ORDER BY log_id DESC LIMIT ? OFFSET ?",
            (per_page, offset),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        db.close()


def get_audit_log(log_id: int) -> dict | None:
    db = get_research_db()
    try:
        row = db.execute("SELECT * FROM research_audit_log WHERE log_id = ?", (log_id,)).fetchone()
        return dict(row) if row else None
    finally:
        db.close()


def get_audit_logs_by_type(event_type: str) -> list[dict]:
    db = get_research_db()
    try:
        rows = db.execute(
            "SELECT * FROM research_audit_log WHERE event_type = ? ORDER BY log_id DESC",
            (event_type,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        db.close()


def record_switch(
    from_mode: str,
    to_mode: str,
    operator: str = "",
    device_id: str = "",
    gps: str = "",
) -> None:
    new_value = json.dumps(
        {
            "from_mode": from_mode,
            "to_mode": to_mode,
            "device_id": device_id,
            "gps": gps,
        }
    )
    log_research_audit(
        event_type="switch",
        entity_type="mode",
        entity_id=0,
        new_value=new_value,
        operator=operator,
    )
