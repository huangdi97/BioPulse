"""监查员任务管理服务。"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder

from ..schemas.monitor_task import MonitorTask, MonitorTaskCreate, MonitorTaskUpdate, TaskDashboard

_TASKS: dict[str, MonitorTask] = {
    "task-001": MonitorTask(
        id="task-001",
        title="核查 site-001 知情同意书",
        description="复核入组前签署版本和签名日期。",
        assignee="CRA-张敏",
        site_id="site-001",
        priority="high",
        status="in_progress",
        due_date=date(2026, 6, 10),
        reminder_sent=False,
    ),
    "task-002": MonitorTask(
        id="task-002",
        title="跟进 SAE 补充材料",
        description="确认 SAE 报告附件和医学判断记录。",
        assignee="CRA-李楠",
        site_id="site-002",
        priority="high",
        status="todo",
        due_date=date(2026, 6, 8),
        reminder_sent=True,
    ),
    "task-003": MonitorTask(
        id="task-003",
        title="完成药物温度记录抽查",
        description="抽查最近 30 天温度记录并归档。",
        assignee="CRA-张敏",
        site_id="site-001",
        priority="medium",
        status="done",
        due_date=date(2026, 6, 1),
        reminder_sent=True,
    ),
}


async def list_tasks(status: str | None = None, site_id: str | None = None) -> dict:
    """查询监查任务列表。"""
    _apply_due_reminders()
    tasks = list(_TASKS.values())
    if status:
        tasks = [task for task in tasks if task.status == status]
    if site_id:
        tasks = [task for task in tasks if task.site_id == site_id]

    return {
        "total": len(tasks),
        "tasks": jsonable_encoder(tasks),
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }


async def create_task(payload: MonitorTaskCreate) -> dict:
    """创建监查任务。"""
    task_id = _next_task_id()
    task = MonitorTask(id=task_id, reminder_sent=False, **payload.dict())
    _TASKS[task_id] = task
    return jsonable_encoder(task)


async def update_task(task_id: str, payload: MonitorTaskUpdate) -> dict:
    """更新监查任务。"""
    if task_id not in _TASKS:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    current = _TASKS[task_id]
    updates = payload.dict(exclude_unset=True)
    task = current.copy(update=updates)
    _TASKS[task_id] = task
    return jsonable_encoder(task)


async def get_task_dashboard() -> dict:
    """获取监查任务 dashboard。"""
    _apply_due_reminders()
    tasks = list(_TASKS.values())
    today = date.today()
    dashboard = TaskDashboard(
        total=len(tasks),
        todo=sum(1 for task in tasks if task.status == "todo"),
        in_progress=sum(1 for task in tasks if task.status == "in_progress"),
        done=sum(1 for task in tasks if task.status == "done"),
        overdue_count=sum(1 for task in tasks if task.status != "done" and task.due_date < today),
    )
    result = jsonable_encoder(dashboard)
    result["due_soon_count"] = sum(1 for task in tasks if task.status != "done" and today <= task.due_date <= today + timedelta(days=2))
    result["last_updated"] = datetime.now(timezone.utc).isoformat()
    return result


def _apply_due_reminders() -> None:
    today = date.today()
    remind_until = today + timedelta(days=2)
    for task_id, task in list(_TASKS.items()):
        if task.status != "done" and task.due_date <= remind_until and not task.reminder_sent:
            _TASKS[task_id] = task.copy(update={"reminder_sent": True})


def _next_task_id() -> str:
    max_id = 0
    for task_id in _TASKS:
        try:
            max_id = max(max_id, int(task_id.split("-")[-1]))
        except ValueError:
            continue
    return f"task-{max_id + 1:03d}"
