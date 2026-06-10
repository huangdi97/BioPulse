"""AI排程优化 API 路由。"""

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from sales_assistant.app.schemas.schedule_optimizer import ScheduleRequest, ScheduleResult
from sales_assistant.app.services.schedule_optimizer_service import ScheduleOptimizerService
from shared.auth_scope import require_scope
from shared.base import ApiResponse, success

router = APIRouter(prefix="/api/schedule", tags=["拜访"])


@router.post("/optimize", summary="AI优化每日拜访排程", tags=["拜访"])
def optimize_schedule(
    body: ScheduleRequest,
    service: ScheduleOptimizerService = Depends(),
    _: dict = Depends(require_scope("visit")),
) -> ApiResponse[ScheduleResult]:
    result = service.optimize_daily_schedule(body.rep_id, body.date, body)
    service._ensure_table()
    now = datetime.now(timezone.utc).isoformat()
    service.db.execute(
        """
        INSERT INTO schedule_optimization (rep_id, schedule_date, request_json, result_json, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(rep_id, schedule_date) DO UPDATE SET
            request_json = excluded.request_json,
            result_json = excluded.result_json,
            updated_at = excluded.updated_at
        """,
        (
            body.rep_id,
            body.date,
            body.model_dump_json(),
            result.model_dump_json(),
            now,
            now,
        ),
    )
    service.db.commit()
    return success(data=result)


@router.get("/{rep_id}/{date}", summary="查看AI排程结果", tags=["拜访"])
def get_schedule_result(
    rep_id: str,
    date: str,
    service: ScheduleOptimizerService = Depends(),
) -> ApiResponse:
    service._ensure_table()
    row = service.db.execute(
        "SELECT result_json FROM schedule_optimization WHERE rep_id = ? AND schedule_date = ?",
        (rep_id, date),
    ).fetchone()
    if row:
        return success(data=json.loads(row["result_json"]))
    result = service.optimize_daily_schedule(rep_id, date)
    return success(data=result)
