import json
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from starlette import status

from cloud.app.database import get_db
from cloud.app.repositories import AgentExecutionTasksRepository, AgentSkillsRepository
from shared.auth_scope import require_scope
from shared.base import success

router = APIRouter(prefix="/agent/exec", tags=["Agent系统"])


class TaskSubmit(BaseModel):
    agent_role: str = ""
    action_type: str = "process"
    input_data: dict = {}
    max_retries: int = 3


class A2ATask(BaseModel):
    task_id: str = ""
    agent_role: str = ""
    input_data: dict = {}
    callback_url: str = ""


def _row(r):
    if not r:
        return None
    d = dict(r)
    for k in ("input_data", "output_data"):
        if k in d and isinstance(d[k], str):
            try:
                d[k] = json.loads(d[k])
            except (json.JSONDecodeError, TypeError):
                pass
    return d


def _rows(rows):
    return [_row(r) for r in rows]


@router.post("/submit", status_code=status.HTTP_201_CREATED)
def submit_task(body: TaskSubmit, current_user=Depends(require_scope("visit")), db=Depends(get_db)):
    """提交Agent执行任务并返回任务记录。Args: body (TaskSubmit) 任务体; current_user 用户; db SQLite连接。Returns: dict 成功响应"""
    repo = AgentExecutionTasksRepository(db)
    task_id = f"aet:{uuid.uuid4()}"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    repo.create(
        {
            "task_id": task_id,
            "source": "internal",
            "agent_role": body.agent_role,
            "action_type": body.action_type,
            "input_data": json.dumps(body.input_data, ensure_ascii=False),
            "max_retries": body.max_retries,
            "status": "completed",
            "created_at": now,
            "completed_at": now,
            "duration_ms": 0,
        }
    )
    row = repo.get_by_task_id(task_id)
    return success(data=_row(row))


@router.get("/tasks/list")
def list_tasks(
    status_filter: Optional[str] = Query(None, alias="status"),
    agent_role: Optional[str] = Query(None),
    current_user=Depends(require_scope("visit")),
    db=Depends(get_db),
):
    """按状态和角色筛选任务列表。Args: status_filter (Optional[str]) 状态; agent_role (Optional[str]) 角色; current_user 用户; db SQLite连接。Returns: dict 成功响应"""
    repo = AgentExecutionTasksRepository(db)
    conds, pars = [], []
    if status_filter:
        conds.append("status=?")
        pars.append(status_filter)
    if agent_role:
        conds.append("agent_role=?")
        pars.append(agent_role)
    rows = repo.list_all(conditions=conds or None, params=pars or None, order_by="created_at DESC")
    return success(data=_rows(rows))


@router.get("/tasks/{task_id}")
def get_task(task_id: str, current_user=Depends(require_scope("visit")), db=Depends(get_db)):
    """根据task_id获取任务详情。Args: task_id (str) 任务ID; current_user 用户; db SQLite连接。Returns: dict 成功响应"""
    repo = AgentExecutionTasksRepository(db)
    row = repo.get_by_task_id(task_id)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Task not found")
    return success(data=_row(row))


@router.post("/tasks/{task_id}/retry")
def retry_task(task_id: str, current_user=Depends(require_scope("visit")), db=Depends(get_db)):
    """递增重试次数并重置状态为pending。Args: task_id (str) 任务ID; current_user 用户; db SQLite连接。Returns: dict 成功响应"""
    repo = AgentExecutionTasksRepository(db)
    row = repo.get_by_task_id(task_id)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Task not found")
    new_count = row["retry_count"] + 1
    repo.update(row["id"], {"retry_count": new_count, "status": "pending"})
    updated = repo.get_by_task_id(task_id)
    return success(data=_row(updated))


@router.post("/tasks/{task_id}/approve")
def approve_task(task_id: str, current_user=Depends(require_scope("visit")), db=Depends(get_db)):
    """批准任务，标记为completed并记录完成时间。Args: task_id (str) 任务ID; current_user 用户; db SQLite连接。Returns: dict 成功响应"""
    repo = AgentExecutionTasksRepository(db)
    row = repo.get_by_task_id(task_id)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Task not found")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    repo.update(row["id"], {"status": "completed", "completed_at": now})
    updated = repo.get_by_task_id(task_id)
    return success(data=_row(updated))


@router.get("/a2a/card")
def a2a_card(current_user=Depends(require_scope("visit")), db=Depends(get_db)):
    """返回A2A能力卡片（名称和技能列表）。Args: current_user 用户; db SQLite连接。Returns: dict 能力卡片数据"""
    skills_repo = AgentSkillsRepository(db)
    rows = skills_repo.list_all(conditions=["enabled=1"], order_by="priority ASC")
    skill_names = [s["skill_name"] for s in rows]
    return success(data={"name": "Cloud Agent", "skills": skill_names})


@router.post("/a2a/task", status_code=status.HTTP_201_CREATED)
def a2a_task(body: A2ATask, current_user=Depends(require_scope("visit")), db=Depends(get_db)):
    """通过A2A协议提交跨Agent任务。Args: body (A2ATask) A2A任务体; current_user 用户; db SQLite连接。Returns: dict 成功响应"""
    repo = AgentExecutionTasksRepository(db)
    task_id = body.task_id or f"aet:{uuid.uuid4()}"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    repo.create(
        {
            "task_id": task_id,
            "source": "a2a",
            "agent_role": body.agent_role,
            "action_type": "process",
            "input_data": json.dumps(body.input_data, ensure_ascii=False),
            "status": "pending",
            "created_at": now,
        }
    )
    row = repo.get_by_task_id(task_id)
    return success(data=_row(row))
