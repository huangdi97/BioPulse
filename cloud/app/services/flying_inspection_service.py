"""飞检（飞行检查）流程管理 —— 编排层。"""

import warnings

from cloud.app.services.capa_workflow_service import confirm_remediation
from cloud.app.services.flying_inspection_crud import create_remediation_task, get_audit_trail, get_checklist, get_dashboard, get_history

__all__ = ["confirm_remediation", "create_remediation_task", "get_audit_trail", "get_checklist", "get_dashboard", "get_history"]

warnings.warn(
    "cloud.app.services.flying_inspection_service is deprecated",
    DeprecationWarning,
    stacklevel=2,
)
