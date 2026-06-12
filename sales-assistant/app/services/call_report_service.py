"""Call report service for the visit three-stage workflow."""

from copy import deepcopy
from threading import Lock

from sales_assistant.app.schemas.call_report import (
    CallReport,
    PostCallSummary,
    PreCallBrief,
    VisitExecution,
)

_REPORTS: dict[str, CallReport] = {}
_LOCK = Lock()


def _default_report(visit_id: str) -> CallReport:
    """生成默认的拜访报告对象。

    Args:
        visit_id: 拜访唯一标识。

    Returns:
        包含默认预填信息的 CallReport 实例。
    """
    return CallReport(
        visit_id=visit_id,
        precall=PreCallBrief(
            target_hcp="待确认HCP" if visit_id != "visit-001" else "张主任",
            visit_goal="确认治疗路径与下一步学术沟通机会",
            key_messages=["产品核心获益", "真实世界证据", "安全性管理要点"],
            prep_materials=["产品DA", "临床研究摘要", "合规拜访清单"],
            hcp_background="基于既往拜访与公开学术信息生成的访前背景摘要。",
        ),
        execution=VisitExecution(
            start_time="",
            end_time="",
            content_tags=[],
            followup_tasks=[],
            compliance_check="pending",
        ),
        summary=PostCallSummary(
            key_conclusions=[],
            next_steps=[],
            hcp_feedback="",
            engagement_score=0,
        ),
    )


def create_call_report(visit_id: str) -> CallReport:
    """创建或获取已有的拜访报告（若已存在则返回副本）。

    Args:
        visit_id: 拜访唯一标识。

    Returns:
        当前拜访报告的深拷贝。
    """
    with _LOCK:
        report = _REPORTS.setdefault(visit_id, _default_report(visit_id))
        return deepcopy(report)


def get_call_report(visit_id: str) -> CallReport:
    """获取指定拜访的当前报告。

    Args:
        visit_id: 拜访唯一标识。

    Returns:
        当前拜访报告的深拷贝。
    """
    return create_call_report(visit_id)


def update_precall(visit_id: str, brief: PreCallBrief) -> CallReport:
    """更新拜访的访前摘要信息。

    Args:
        visit_id: 拜访唯一标识。
        brief: 访前摘要数据。

    Returns:
        更新后的拜访报告深拷贝。
    """
    with _LOCK:
        report = _REPORTS.setdefault(visit_id, _default_report(visit_id))
        report.precall = brief
        return deepcopy(report)


def update_execution(visit_id: str, execution: VisitExecution) -> CallReport:
    """更新拜访的执行记录信息。

    Args:
        visit_id: 拜访唯一标识。
        execution: 执行记录数据。

    Returns:
        更新后的拜访报告深拷贝。
    """
    with _LOCK:
        report = _REPORTS.setdefault(visit_id, _default_report(visit_id))
        report.execution = execution
        return deepcopy(report)


def update_summary(visit_id: str, summary: PostCallSummary) -> CallReport:
    """更新拜访的访后总结信息。

    Args:
        visit_id: 拜访唯一标识。
        summary: 访后总结数据。

    Returns:
        更新后的拜访报告深拷贝。
    """
    with _LOCK:
        report = _REPORTS.setdefault(visit_id, _default_report(visit_id))
        report.summary = summary
        return deepcopy(report)
