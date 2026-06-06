"""反思报告路由：创建、获取反思报告及摘要。"""

import json

from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from sales_coach.app.services.reflection_service import generate_reflection_report, get_scenario
from sales_coach.app.services.session_service import SessionService
from shared.auth_scope import require_scope
from shared.base import ApiResponse, success

router = APIRouter(prefix="/reflections", tags=["反思 Agent"])


@router.get("", summary="反思列表", description="获取所有反思报告列表")
def list_reflections(
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse:
    """获取所有反思报告列表。"""
    return success(data=[])


@router.post("/{session_id}", summary="创建反思", description="读取会话日志并生成反思报告")
def create_reflection(
    session_id: int,
    session_service: SessionService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse:
    """创建反思报告。读取会话对话日志 → 计算分数 → 调用 AI Gateway → 返回报告。"""
    session = session_service.get(session_id)
    if not session:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Session not found")
    dialogue_log = json.loads(session.get("dialogue_log") or "[]")
    compliance_violations = session.get("compliance_violations") or 0
    scenario = None
    if session.get("scenario_id"):
        scenario = get_scenario(session["scenario_id"])
    report = generate_reflection_report(
        session_id=session_id,
        dialogue_log=dialogue_log,
        compliance_violations=compliance_violations,
        scenario=scenario,
    )
    session_service.update_reflection(session_id, report)
    return success(data=report)


@router.get("/{session_id}", summary="反思详情", description="获取已生成的反思报告详情")
def get_reflection(
    session_id: int,
    session_service: SessionService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
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


@router.get("/{session_id}/summary", summary="反思摘要", description="获取反思报告简短摘要用于列表展示")
def get_reflection_summary(
    session_id: int,
    session_service: SessionService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
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
