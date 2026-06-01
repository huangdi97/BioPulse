import json
from datetime import datetime


def send_notification(
    db, user_id, title, body, category, ref_type=None, ref_id=None, context=None
):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    context_json = json.dumps(context or {}, ensure_ascii=False)
    cur = db.execute(
        "INSERT INTO notifications (user_id, title, body, category, ref_type, ref_id, context_json, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (user_id, title, body, category, ref_type or "", ref_id, context_json, now),
    )
    db.commit()
    return cur.lastrowid
