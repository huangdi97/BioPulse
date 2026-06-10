"""销售漏斗服务：日程完成率、笔记覆盖率等漏斗分析。"""

from sales_assistant.app.repositories import NoteRepository, ScheduleRepository
from shared.base_service import BaseService


class FunnelService(BaseService):
    """销售漏斗服务：计算转化率、按事件类型统计漏斗数据。"""

    def _calc_rate(self, numerator: int, denominator: int) -> float:
        if denominator == 0:
            return 0.0
        return round(numerator / denominator * 100, 1)

    def funnel_analysis(self) -> dict:
        """计算销售漏斗分析数据，包含完成率、笔记覆盖率和按事件类型的分布。

        Returns:
            包含总日程数、完成率、笔记覆盖率及按类型分布的字典。
        """
        schedule_repo = ScheduleRepository(self.db)
        note_repo = NoteRepository(self.db)

        total_schedules = schedule_repo.count()
        completed_schedules = schedule_repo.count(conditions=["is_completed = 1"])

        notes = note_repo.list_all()
        with_notes = len({n["schedule_id"] for n in notes})

        schedules = schedule_repo.list_all()
        by_event_type: dict[str, dict] = {}
        for s in schedules:
            event_type = s["event_type"] or "其他"
            if event_type not in by_event_type:
                by_event_type[event_type] = {"total": 0, "completed": 0}
            by_event_type[event_type]["total"] += 1
            if s["is_completed"]:
                by_event_type[event_type]["completed"] += 1

        completion_rate = self._calc_rate(completed_schedules, total_schedules)
        note_rate = self._calc_rate(with_notes, completed_schedules)

        return {
            "total_schedules": total_schedules,
            "completed_schedules": completed_schedules,
            "completion_rate": completion_rate,
            "with_notes": with_notes,
            "note_rate": note_rate,
            "by_event_type": by_event_type,
        }
