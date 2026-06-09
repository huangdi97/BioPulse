"""合规审查 v2 路由。"""

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


@router.post("/scan", status_code=201, summary="扫描内容合规性", description="对内容进行合规扫描检查", tags=["合规"])
def scan(
    body: ScanRequest,
    request: Request,
    current_user=Depends(require_scope("visit")),
    service: ComplianceV2Service = Depends(),
):
    """扫描内容合规性。"""
    uid = int(current_user["sub"])
    return service.scan(body, request, uid)


@router.get("/records", summary="分页查询合规审核记录", description="按消息类型、风险等级等条件分页查询合规审核记录", tags=["合规"])
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


@router.get("/records/{record_id}", summary="获取单条审核记录", description="根据记录ID获取合规审核单条记录详情", tags=["合规"])
def get_record(
    record_id: int,
    current_user=Depends(require_scope("visit")),
    service: ComplianceV2Service = Depends(),
):
    """获取单条审核记录。"""
    return service.get_record(record_id)


@router.post("/records/{record_id}/review", summary="人工审核合规记录", description="对合规记录进行人工审核操作", tags=["合规"])
def review_record(
    record_id: int,
    body: ReviewRequest,
    current_user=Depends(require_scope("visit")),
    service: ComplianceV2Service = Depends(),
):
    """人工审核合规记录。"""
    uid = int(current_user["sub"])
    return service.review_record(record_id, body, uid)


@router.post("/audit-chain", status_code=201, summary="创建审计链条目", description="创建一条新的审计链条目记录", tags=["合规"])
def create_audit_chain(
    body: AuditChainCreate,
    current_user=Depends(require_scope("visit")),
    service: ComplianceV2Service = Depends(),
):
    """创建审计链条目。"""
    uid = int(current_user["sub"])
    return service.create_audit_chain(body, uid)


@router.get("/audit-chain/{entity_type}/{entity_id}", summary="获取实体审计链", description="根据实体类型和ID获取完整的审计链", tags=["合规"])
def get_audit_chain(
    entity_type: str,
    entity_id: str,
    current_user=Depends(require_scope("visit")),
    service: ComplianceV2Service = Depends(),
):
    """获取实体的审计链。"""
    return service.get_audit_chain(entity_type, entity_id)


@router.get("/audit-chain/verify/{entity_type}/{entity_id}", summary="验证审计链完整性", description="验证指定实体的审计链数据完整性", tags=["合规"])
def verify_audit_chain(
    entity_type: str,
    entity_id: str,
    current_user=Depends(require_scope("visit")),
    service: ComplianceV2Service = Depends(),
):
    """验证审计链完整性。"""
    return service.verify_audit_chain(entity_type, entity_id)


@router.post("/audit-records/{record_id}/train", summary="生成培训纠正", description="基于审核记录生成培训纠正建议", tags=["合规"])
def train_correction(
    record_id: int,
    request: Request,
    current_user=Depends(require_scope("visit")),
    service: ComplianceV2Service = Depends(),
):
    """基于审核记录生成培训纠正。"""
    uid = int(current_user["sub"])
    return service.train_correction(record_id, request, uid)


@router.get("/corrections", summary="分页查询培训纠正记录", description="按类别、严重程度等条件分页查询培训纠正记录", tags=["合规"])
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


@router.patch("/corrections/{correction_id}", summary="更新培训纠正状态", description="更新指定培训纠正记录的状态或分配人", tags=["合规"])
def update_correction(
    correction_id: int,
    body: CorrectionUpdate,
    current_user=Depends(require_scope("visit")),
    service: ComplianceV2Service = Depends(),
):
    """更新培训纠正状态。"""
    return service.update_correction(correction_id, body)


@router.get("/rules/l2", summary="列出L2合规规则", description="获取所有二级合规规则列表", tags=["合规"])
def list_l2_rules(
    current_user=Depends(require_scope("visit")),
    service: ComplianceV2Service = Depends(),
):
    """列出 L2 合规规则。"""
    return service.list_l2_rules()


@router.post("/evaluate", summary="评估拜访数据合规性", description="评估医访数据的合规性", tags=["合规"])
def evaluate_visit(
    body: EvaluateRequest,
    current_user=Depends(require_scope("visit")),
    service: ComplianceV2Service = Depends(),
):
    """评估拜访数据的合规性。"""
    return service.evaluate_visit(body)


@router.get("/dashboard", summary="获取合规仪表盘数据", description="获取合规系统的仪表盘统计数据", tags=["合规"])
def dashboard(
    current_user=Depends(require_scope("visit")),
    service: ComplianceV2Service = Depends(),
):
    """获取合规仪表盘数据。"""
    return service.dashboard()
