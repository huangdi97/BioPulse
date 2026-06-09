"""监查员任务管理数据模型。"""

from datetime import date

from pydantic import BaseModel, Field


class MonitorTask(BaseModel):
    id: str = Field(..., description="任务编号")
    title: str = Field(..., description="任务标题")
    description: str = Field("", description="任务描述")
    assignee: str = Field(..., description="负责人")
    site_id: str = Field(..., description="中心编号")
    priority: str = Field("medium", description="优先级")
    status: str = Field("todo", description="状态")
    due_date: date = Field(..., description="到期日期")
    reminder_sent: bool = Field(False, description="是否已发送提醒")


class MonitorTaskCreate(BaseModel):
    title: str = Field(..., description="任务标题")
    description: str = Field("", description="任务描述")
    assignee: str = Field(..., description="负责人")
    site_id: str = Field(..., description="中心编号")
    priority: str = Field("medium", description="优先级")
    status: str = Field("todo", description="状态")
    due_date: date = Field(..., description="到期日期")


class MonitorTaskUpdate(BaseModel):
    title: str | None = Field(None, description="任务标题")
    description: str | None = Field(None, description="任务描述")
    assignee: str | None = Field(None, description="负责人")
    site_id: str | None = Field(None, description="中心编号")
    priority: str | None = Field(None, description="优先级")
    status: str | None = Field(None, description="状态")
    due_date: date | None = Field(None, description="到期日期")
    reminder_sent: bool | None = Field(None, description="是否已发送提醒")


class TaskDashboard(BaseModel):
    total: int = Field(..., description="任务总数")
    todo: int = Field(..., description="待处理数量")
    in_progress: int = Field(..., description="进行中数量")
    done: int = Field(..., description="已完成数量")
    overdue_count: int = Field(..., description="逾期数量")
