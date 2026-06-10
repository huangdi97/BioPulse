"""飞检（飞行检查）流程管理 —— 任务分派、检查流程、审计追踪。"""

from datetime import date, datetime
from typing import Optional
from uuid import uuid4

from fastapi import HTTPException
from starlette import status

from cloud.app.schemas.flying_inspection import (
    ChecklistStatus,
    InspectionChecklist,
    InspectionDashboard,
    InspectionTask,
    TaskStatus,
)
from cloud.app.services.flying_inspection_calculation import compute_dashboard

CHECKLIST = [
    InspectionChecklist(
        id="chk-license",
        category="资质证照",
        item="营业执照、药品经营许可证、GSP证书均在有效期内",
        status=ChecklistStatus.PASSED,
        deadline="2026-06-12",
        assignee="质量负责人",
        remark="证照复印件已归档",
    ),
    InspectionChecklist(
        id="chk-training",
        category="人员培训",
        item="关键岗位年度合规与质量培训记录完整",
        status=ChecklistStatus.PENDING,
        deadline="2026-06-15",
        assignee="培训管理员",
        remark="缺少2名新员工签到记录",
    ),
    InspectionChecklist(
        id="chk-cold-chain",
        category="冷链管理",
        item="冷链温湿度监测、报警处置与校准记录闭环",
        status=ChecklistStatus.FAILED,
        deadline="2026-06-08",
        assignee="仓储主管",
        remark="5月报警复核记录未签字",
    ),
    InspectionChecklist(
        id="chk-sample",
        category="样品管理",
        item="样品领用、流向、销毁台账一致",
        status=ChecklistStatus.PASSED,
        deadline="2026-06-18",
        assignee="医学事务",
        remark="抽查无异常",
    ),
]

TASKS: dict[str, InspectionTask] = {
    "task-cold-chain-001": InspectionTask(
        id="task-cold-chain-001",
        title="补齐冷链报警复核签字",
        description="复核5月冷链报警处置记录，完成质量负责人签字并归档。",
        assignee="仓储主管",
        deadline="2026-06-11",
        status=TaskStatus.IN_PROGRESS,
    )
}

DEFAULT_INSPECTION_ID = "inspection-2026-06"

AUDIT_TRAILS: dict[str, list[dict]] = {
    "inspection-2026-05": [
        {
            "id": "audit-2026-05-self-check",
            "stage": "compliance_self_check",
            "who": "质量负责人",
            "when": "2026-05-28T09:10:00",
            "what": "完成月度合规自检，确认证照与样品台账完整",
            "evidence": "self-checklist-2026-05.pdf",
        },
        {
            "id": "audit-2026-05-task",
            "stage": "remediation_assignment",
            "who": "质量负责人",
            "when": "2026-05-28T10:00:00",
            "what": "无重大缺陷，仅分派培训记录抽查跟进",
            "evidence": "training-sampling-task",
        },
        {
            "id": "audit-2026-05-review",
            "stage": "review_confirmation",
            "who": "质量负责人",
            "when": "2026-05-28T15:30:00",
            "what": "复查确认抽查材料齐备",
            "evidence": "training-sampling-review",
        },
        {
            "id": "audit-2026-05-score",
            "stage": "scoring",
            "who": "合规评分引擎",
            "when": "2026-05-28T15:35:00",
            "what": "月度飞检准备度评分为86",
            "evidence": "inspection-score-ledger",
        },
    ],
    DEFAULT_INSPECTION_ID: [
        {
            "id": "audit-self-check-001",
            "stage": "compliance_self_check",
            "who": "质量负责人",
            "when": "2026-06-08T09:00:00",
            "what": "完成飞检合规自检，识别冷链管理缺陷",
            "evidence": "self-checklist-2026-06.pdf",
        },
        {
            "id": "audit-task-assign-001",
            "stage": "remediation_assignment",
            "who": "质量负责人",
            "when": "2026-06-08T10:20:00",
            "what": "分派冷链报警复核签字整改任务",
            "evidence": "task-cold-chain-001",
        },
        {
            "id": "audit-review-001",
            "stage": "review_confirmation",
            "who": "质量负责人",
            "when": "2026-06-08T16:30:00",
            "what": "复查整改证据，等待补充签字扫描件",
            "evidence": "cold-chain-review-note",
        },
        {
            "id": "audit-score-001",
            "stage": "scoring",
            "who": "合规评分引擎",
            "when": "2026-06-08T16:35:00",
            "what": "飞检准备度评分更新为78",
            "evidence": "inspection-score-ledger",
        },
    ],
}

HISTORY = [
    {
        "id": "hist-2026-05",
        "inspection_id": "inspection-2026-05",
        "date": "2026-05-28",
        "event": "月度飞检自查完成",
        "score": 86,
        "owner": "质量负责人",
        "capa_stage": "scoring",
    },
    {
        "id": "hist-2026-06-cold-chain",
        "inspection_id": DEFAULT_INSPECTION_ID,
        "date": "2026-06-08",
        "event": "冷链管理项发现缺陷并创建整改",
        "score": 78,
        "owner": "仓储主管",
        "capa_stage": "remediation_assignment",
    },
]


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _add_audit_log(
    inspection_id: str,
    stage: str,
    who: str,
    what: str,
    evidence: str,
) -> dict:
    entry = {
        "id": f"audit-{uuid4().hex[:8]}",
        "stage": stage,
        "who": who,
        "when": _now(),
        "what": what,
        "evidence": evidence,
    }
    AUDIT_TRAILS.setdefault(inspection_id, []).append(entry)
    return entry


def _append_history(
    inspection_id: str,
    event: str,
    score: int,
    owner: str,
    capa_stage: str,
) -> None:
    HISTORY.insert(
        0,
        {
            "id": f"hist-{uuid4().hex[:8]}",
            "inspection_id": inspection_id,
            "date": date.today().isoformat(),
            "event": event,
            "score": score,
            "owner": owner,
            "capa_stage": capa_stage,
        },
    )


def get_dashboard() -> InspectionDashboard:
    """委托计算引擎返回飞检准备度仪表盘。"""
    return compute_dashboard(CHECKLIST, HISTORY)


def get_checklist(category: Optional[str] = None) -> list[InspectionChecklist]:
    """获取检查清单，可按分类筛选。"""
    if not category:
        return CHECKLIST
    return [item for item in CHECKLIST if item.category == category]


def create_remediation_task(
    title: str,
    description: str,
    assignee: str,
    deadline: str,
    inspection_id: str = DEFAULT_INSPECTION_ID,
    who: str = "质量负责人",
    evidence: str = "remediation-task-form",
) -> InspectionTask:
    """创建整改任务并记录审计日志与历史。"""
    task_id = f"task-{uuid4().hex[:8]}"
    task = InspectionTask(
        id=task_id,
        title=title,
        description=description,
        assignee=assignee,
        deadline=deadline,
        status=TaskStatus.PENDING,
    )
    TASKS[task_id] = task
    _add_audit_log(
        inspection_id=inspection_id,
        stage="remediation_assignment",
        who=who,
        what=f"分派整改任务给{assignee}：{title}",
        evidence=evidence,
    )
    _append_history(
        inspection_id=inspection_id,
        event=f"创建整改任务：{title}",
        score=get_dashboard().score,
        owner=assignee,
        capa_stage="remediation_assignment",
    )
    return task


def confirm_remediation(
    task_id: str,
    inspection_id: str = DEFAULT_INSPECTION_ID,
    who: str = "质量负责人",
    evidence: str = "remediation-evidence",
) -> InspectionTask:
    """确认整改完成，更新任务状态并记录审计评分。"""
    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Inspection task not found")
    confirmed = task.model_copy(update={"status": TaskStatus.CONFIRMED})
    TASKS[task_id] = confirmed
    _add_audit_log(
        inspection_id=inspection_id,
        stage="review_confirmation",
        who=who,
        what=f"复查确认整改完成：{confirmed.title}",
        evidence=evidence,
    )
    score = get_dashboard().score
    _add_audit_log(
        inspection_id=inspection_id,
        stage="scoring",
        who="合规评分引擎",
        what=f"飞检闭环评分更新为{score}",
        evidence="inspection-score-ledger",
    )
    _append_history(
        inspection_id=inspection_id,
        event=f"确认整改完成：{confirmed.title}",
        score=score,
        owner=confirmed.assignee,
        capa_stage="review_confirmation",
    )
    return confirmed


def get_history() -> list[dict]:
    """获取历史记录列表，每条记录附带完整的审计链。"""
    enriched = []
    for record in HISTORY:
        inspection_id = record.get("inspection_id", DEFAULT_INSPECTION_ID)
        enriched.append(
            {
                **record,
                "audit_chain": AUDIT_TRAILS.get(inspection_id, []),
                "audit_count": len(AUDIT_TRAILS.get(inspection_id, [])),
            }
        )
    return enriched


def get_audit_trail(inspection_id: str) -> dict:
    """获取指定飞检周期的完整审计追踪链。"""
    trail = AUDIT_TRAILS.get(inspection_id)
    if trail is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Inspection audit trail not found")
    return {
        "inspection_id": inspection_id,
        "capa_chain": [
            "compliance_self_check",
            "remediation_assignment",
            "review_confirmation",
            "scoring",
        ],
        "audit_trail": trail,
    }
