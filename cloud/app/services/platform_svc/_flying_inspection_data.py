"""Shared data for flying inspection services."""

from cloud.app.schemas.flying_inspection import ChecklistStatus, InspectionChecklist, InspectionTask, TaskStatus

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
    ),
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
