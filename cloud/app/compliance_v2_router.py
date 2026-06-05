from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel

from cloud.app.services.compliance_v2_service import ComplianceV2Service
from shared.auth_scope import require_scope

router = APIRouter(prefix="/compliance-v2", tags=["合规"])


class ScanRequest(BaseModel):
    message_type: str = "text"
    content: str
    source_id: str = ""


class ReviewRequest(BaseModel):
    override_passed: int
    review_notes: str = ""


class AuditChainCreate(BaseModel):
    entity_type: str
    entity_id: str
    action: str
    source: str = ""
    payload: dict = {}
    metadata: dict = {}


class CorrectionUpdate(BaseModel):
    status: Optional[str] = None
    assigned_to: Optional[int] = None


class EvaluateRequest(BaseModel):
    visit_data: dict


@router.post("/scan", status_code=201)
def scan(
    body: ScanRequest,
    request: Request,
    current_user=Depends(require_scope("visit")),
    service: ComplianceV2Service = Depends(),
):
    """扫描内容合规性。"""
    uid = int(current_user["sub"])
    return service.scan(body, request, uid)


@router.get("/records")
def list_records(
    message_type: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    passed: Optional[int] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(require_scope("visit")),
    service: ComplianceV2Service = Depends(),
):
    """分页查询合规审核记录。"""
    return service.list_records(message_type, risk_level, passed, date_from, date_to, page, page_size)


@router.get("/records/{record_id}")
def get_record(
    record_id: int,
    current_user=Depends(require_scope("visit")),
    service: ComplianceV2Service = Depends(),
):
    """获取单条审核记录。"""
    return service.get_record(record_id)


@router.post("/records/{record_id}/review")
def review_record(
    record_id: int,
    body: ReviewRequest,
    current_user=Depends(require_scope("visit")),
    service: ComplianceV2Service = Depends(),
):
    """人工审核合规记录。"""
    uid = int(current_user["sub"])
    return service.review_record(record_id, body, uid)


@router.post("/audit-chain", status_code=201)
def create_audit_chain(
    body: AuditChainCreate,
    current_user=Depends(require_scope("visit")),
    service: ComplianceV2Service = Depends(),
):
    """创建审计链条目。"""
    uid = int(current_user["sub"])
    return service.create_audit_chain(body, uid)


@router.get("/audit-chain/{entity_type}/{entity_id}")
def get_audit_chain(
    entity_type: str,
    entity_id: str,
    current_user=Depends(require_scope("visit")),
    service: ComplianceV2Service = Depends(),
):
    """获取实体的审计链。"""
    return service.get_audit_chain(entity_type, entity_id)


@router.get("/audit-chain/verify/{entity_type}/{entity_id}")
def verify_audit_chain(
    entity_type: str,
    entity_id: str,
    current_user=Depends(require_scope("visit")),
    service: ComplianceV2Service = Depends(),
):
    """验证审计链完整性。"""
    return service.verify_audit_chain(entity_type, entity_id)


@router.post("/audit-records/{record_id}/train")
def train_correction(
    record_id: int,
    request: Request,
    current_user=Depends(require_scope("visit")),
    service: ComplianceV2Service = Depends(),
):
    """基于审核记录生成培训纠正。"""
    uid = int(current_user["sub"])
    return service.train_correction(record_id, request, uid)


@router.get("/corrections")
def list_corrections(
    category: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(require_scope("visit")),
    service: ComplianceV2Service = Depends(),
):
    """分页查询培训纠正记录。"""
    return service.list_corrections(category, severity, status, page, page_size)


@router.patch("/corrections/{correction_id}")
def update_correction(
    correction_id: int,
    body: CorrectionUpdate,
    current_user=Depends(require_scope("visit")),
    service: ComplianceV2Service = Depends(),
):
    """更新培训纠正状态。"""
    return service.update_correction(correction_id, body)


@router.get("/rules/l2")
def list_l2_rules(
    current_user=Depends(require_scope("visit")),
    service: ComplianceV2Service = Depends(),
):
    """列出 L2 合规规则。"""
    return service.list_l2_rules()


@router.post("/evaluate")
def evaluate_visit(
    body: EvaluateRequest,
    current_user=Depends(require_scope("visit")),
    service: ComplianceV2Service = Depends(),
):
    """评估拜访数据的合规性。"""
    return service.evaluate_visit(body)


@router.get("/dashboard")
def dashboard(
    current_user=Depends(require_scope("visit")),
    service: ComplianceV2Service = Depends(),
):
    """获取合规仪表盘数据。"""
    return service.dashboard()
