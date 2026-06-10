"""飞检计算引擎 —— 评分与分数计算。"""

from datetime import date, datetime

from cloud.app.schemas.flying_inspection import (
    ChecklistStatus,
    InspectionChecklist,
    InspectionDashboard,
)


def _today() -> date:
    return datetime.now().date()


def compute_dashboard(
    checklist: list[InspectionChecklist],
    history: list[dict],
) -> InspectionDashboard:
    """根据检查清单与历史记录计算飞检准备度仪表盘。"""
    passed = sum(1 for item in checklist if item.status == ChecklistStatus.PASSED)
    total = len(checklist)
    failed = sum(1 for item in checklist if item.status == ChecklistStatus.FAILED)
    overdue_count = sum(
        1
        for item in checklist
        if item.status != ChecklistStatus.PASSED
        and datetime.fromisoformat(item.deadline).date() <= _today()
    )
    self_check_rate = round(passed / total * 100, 1) if total else 0.0
    score = max(0, min(100, int(self_check_rate - overdue_count * 8 - failed * 5 + 20)))
    return InspectionDashboard(
        self_check_rate=self_check_rate,
        overdue_count=overdue_count,
        history_records=history,
        score=score,
    )
