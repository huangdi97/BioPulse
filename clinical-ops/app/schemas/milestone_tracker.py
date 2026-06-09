"""临床里程碑跟踪数据模型。"""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

MilestoneType = Literal["screening", "initiation", "enrollment", "closeout"]


class ClinicalMilestone(BaseModel):
    id: str = Field(..., description="里程碑编号")
    trial_id: str = Field(..., description="试验编号")
    site_id: str = Field(..., description="中心编号")
    milestone_type: MilestoneType = Field(..., description="里程碑类型")
    planned_date: date = Field(..., description="计划日期")
    actual_date: date | None = Field(None, description="实际完成日期")
    status: str = Field(..., description="状态")
    variance_days: int = Field(..., description="偏差天数")


class GanttItem(BaseModel):
    id: str = Field(..., description="任务编号")
    milestone: MilestoneType = Field(..., description="里程碑")
    site_id: str = Field(..., description="中心编号")
    start: date = Field(..., description="开始日期")
    end: date = Field(..., description="结束日期")
    progress: int = Field(..., ge=0, le=100, description="进度")
    status: str = Field(..., description="状态")


class MilestoneTimeline(BaseModel):
    trial_id: str = Field(..., description="试验编号")
    milestones: list[ClinicalMilestone] = Field(default_factory=list, description="里程碑列表")
    gantt_data: list[GanttItem] = Field(default_factory=list, description="Gantt 渲染数据")


class SiteProgress(BaseModel):
    site_id: str = Field(..., description="中心编号")
    trial_id: str = Field(..., description="试验编号")
    total_milestones: int = Field(..., description="里程碑总数")
    completed_milestones: int = Field(..., description="已完成里程碑")
    progress_pct: float = Field(..., description="完成率")
    current_status: str = Field(..., description="当前状态")
    next_milestone: str | None = Field(None, description="下一里程碑")
    overdue_count: int = Field(..., description="逾期数量")
