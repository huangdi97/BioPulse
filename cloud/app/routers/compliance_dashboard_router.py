import json
from datetime import datetime, timezone
from collections import Counter

from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from shared.auth import get_current_user
from cloud.app.dependencies import get_db

router = APIRouter(prefix="/api/compliance/dashboard", tags=["合规"])


def _today_start() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT00:00:00")


@router.get("/summary")
def dashboard_summary(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    today = _today_start()
    rows = db.execute(
        "SELECT rule_code, rule_name, visit_data_json, created_at FROM enforcement_log WHERE created_at >= ?",
        (today,),
    ).fetchall()

    total_today = len(rows)
    l1_count = len([r for r in rows if "L1" in r["rule_code"]])
    rule_counter = Counter(r["rule_code"] for r in rows)
    most_common = rule_counter.most_common(1)
    most_common_rule = most_common[0][0] if most_common else ""

    rep_counter = Counter()
    for r in rows:
        try:
            visit_data = json.loads(r["visit_data_json"])
            rep_id = visit_data.get("rep_id")
            if rep_id is not None:
                rep_counter[rep_id] += 1
        except (json.JSONDecodeError, TypeError):
            pass

    return {
        "total_violations_today": total_today,
        "l1_violations": l1_count,
        "most_common_rule": most_common_rule,
        "violations_by_rep": [{"rep_id": rid, "count": cnt} for rid, cnt in rep_counter.items()],
    }


@router.get("/reps/{rep_id}")
def rep_violations(
    rep_id: int,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    rows = db.execute(
        "SELECT id, rule_code, rule_name, severity, action, visit_data_json, created_at FROM enforcement_log ORDER BY id"
    ).fetchall()

    result = []
    for r in rows:
        try:
            visit_data = json.loads(r["visit_data_json"])
            if visit_data.get("rep_id") == rep_id:
                result.append({
                    "id": r["id"],
                    "rule_code": r["rule_code"],
                    "rule_name": r["rule_name"],
                    "severity": r["severity"],
                    "action": r["action"],
                    "visit_data": visit_data,
                    "created_at": r["created_at"],
                })
        except (json.JSONDecodeError, TypeError):
            pass

    return {"rep_id": rep_id, "violations": result}
