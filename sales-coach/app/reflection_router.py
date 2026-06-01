"""反思报告路由：创建、获取反思报告及摘要。"""

import json

from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from shared.auth import get_current_user
from shared.base import ApiResponse, success
from sales_coach.app.database import get_db
from sales_coach.app.services.assessment_service import AssessmentService
from sales_coach.app.services.reflection_service import generate_reflection_report
from sales_coach.app.services.session_service import SessionService

router = APIRouter(prefix="/reflections", tags=["反思 Agent"])


@router.post("/{session_id}")
def create_reflection(
    session_id: int,
    session_service: SessionService = Depends(),
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    """创建反思报告。读取会话对话日志 → 计算分数 → 调用 AI Gateway → 返回报告。"""
    session = session_service.get(session_id)
    if not session:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Session not found")
    dialogue_log = json.loads(session.get("dialogue_log") or "[]")
    compliance_violations = session.get("compliance_violations") or 0
    scenario = None
    if session.get("scenario_id"):
        row = db.execute(
            "SELECT * FROM coach_scenario WHERE id = ?",
            (session["scenario_id"],),
        ).fetchone()
        if row:
            scenario = dict(row)
    report = generate_reflection_report(
        session_id=session_id,
        dialogue_log=dialogue_log,
        compliance_violations=compliance_violations,
        scenario=scenario,
    )
    session_service.update_reflection(session_id, report)
    return success(data=report)


@router.get("/{session_id}")
def get_reflection(
    session_id: int,
    session_service: SessionService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    """获取已生成的反思报告。"""
    session = session_service.get(session_id)
    if not session:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Session not found")
    report_raw = session.get("reflection_report")
    if not report_raw:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Reflection not found for this session")
    report = json.loads(report_raw)
    return success(data=report)


@router.get("/{session_id}/summary")
def get_reflection_summary(
    session_id: int,
    session_service: SessionService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    """获取反思报告摘要（短版，用于列表展示）。"""
    session = session_service.get(session_id)
    if not session:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Session not found")
    report_raw = session.get("reflection_report")
    if not report_raw:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Reflection not found for this session")
    report = json.loads(report_raw)
    summary = {
        "session_id": report.get("session_id"),
        "generated_at": report.get("generated_at"),
        "summary": report.get("summary"),
        "overall_score": report.get("scores", {}).get("overall"),
        "strengths_count": len(report.get("strengths", [])),
        "weaknesses_count": len(report.get("weaknesses", [])),
        "improvements_count": len(report.get("improvements", [])),
        "trend": report.get("comparison", {}).get("trend"),
    }
    return success(data=summary)
