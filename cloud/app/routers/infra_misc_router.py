"""合并的基础设施杂项路由：ASR、演示、推演、产品、入院、MRC、内容工厂、数据中台。"""

from typing import Any, Optional

from fastapi import APIRouter, Body, Depends, File, Query, UploadFile
from pydantic import BaseModel, Field
from starlette import status

from cloud.app.compliance.service import ComplianceService
from cloud.app.data_platform.analytics.bi_view import BIViewService
from cloud.app.data_platform.analytics.olap_service import OLAPService
from cloud.app.data_platform.etl.pipeline import ETLPipeline
from cloud.app.data_platform.schemas.data_platform import OLAPQuery, PipelineRunResult
from cloud.app.schemas.mrc_workflow import (
    ComplianceApproveRequest,
    DistributionRequest,
    MaterialCreate,
    MRCDecisionRequest,
)
from cloud.app.services.admission_service import AdmissionService
from cloud.app.services.asr_service import AsrService
from cloud.app.services.content_factory_service import ContentFactoryService
from cloud.app.services.dashboard_service import DashboardService
from cloud.app.services.inference_pipeline import InferencePipeline
from cloud.app.services.mrc_workflow_service import (
    approve,
    create_material,
    distribute,
    mrc_decision,
    submit_compliance,
    submit_mrc,
    track,
)
from cloud.app.services.product_service import ProductService
from shared.auth_scope import require_scope
from shared.base import success

# ── asr_router ─────────────────────────────────────────────────────────

asr_router = APIRouter(prefix="/api/v1/asr", tags=["ASR录音摘要"])


class UploadResponse(BaseModel):
    task_id: str
    status: str = "pending"


class TranscriptResponse(BaseModel):
    task_id: str
    transcript: str
    status: str


class SummaryResponse(BaseModel):
    task_id: str
    summary: dict
    status: str


@asr_router.post("/upload", status_code=status.HTTP_201_CREATED, response_model=UploadResponse, summary="上传录音文件", tags=["ASR录音摘要"])
async def upload_audio(
    file: UploadFile = File(...),
    service: AsrService = Depends(),
    _: dict = Depends(require_scope("visit")),
):
    import os

    os.makedirs("uploads/audio", exist_ok=True)
    file_path = f"uploads/audio/{file.filename}"
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    result = service.process_audio(file_path)
    return success(data=UploadResponse(**result))


@asr_router.get("/{task_id}/transcript", summary="获取转写结果", tags=["ASR录音摘要"])
def get_transcript(task_id: str, service: AsrService = Depends()):
    result = service.get_transcript(task_id)
    if not result:
        from fastapi import HTTPException

        raise HTTPException(404, "task not found")
    return success(data=TranscriptResponse(**result))


@asr_router.get("/{task_id}/summary", summary="获取结构化摘要", tags=["ASR录音摘要"])
def get_summary(task_id: str, service: AsrService = Depends()):
    result = service.get_summary(task_id)
    if not result:
        from fastapi import HTTPException

        raise HTTPException(404, "task not found")
    return success(data=SummaryResponse(**result))


# ── demo_router ────────────────────────────────────────────────────────

demo_router = APIRouter(prefix="/api/demo", tags=["demo"])


@demo_router.get("/dashboard", summary="仪表盘概览", description="获取演示仪表盘的整体概览数据", tags=["demo"])
def dashboard_overview(service: DashboardService = Depends()):
    return success(data=service.get_overview())


@demo_router.get("/dashboard/users", summary="用户统计", description="获取演示仪表盘的用户统计数据", tags=["demo"])
def dashboard_users(service: DashboardService = Depends()):
    return success(data=service.get_user_stats())


@demo_router.get("/dashboard/compliance", summary="合规统计", description="获取演示仪表盘的合规统计数据", tags=["demo"])
def dashboard_compliance(service: DashboardService = Depends()):
    return success(data=service.get_compliance_stats())


@demo_router.get("/compliance/summary", summary="合规摘要", description="获取合规摘要数据", tags=["demo"])
def compliance_summary(service: ComplianceService = Depends()):
    return success(data=service.dashboard_summary())


@demo_router.get("/visit-trends", summary="拜访趋势", description="获取拜访趋势数据", tags=["demo"])
def visit_trends(service: DashboardService = Depends()):
    return success(data=service.get_visit_trends())


@demo_router.get("/team-ranks", summary="团队排名", description="获取团队排名数据", tags=["demo"])
def team_ranks(service: DashboardService = Depends()):
    return success(data=service.get_team_ranks())


@demo_router.get("/violations", summary="违规记录", description="获取违规记录数据", tags=["demo"])
def violations(service: DashboardService = Depends()):
    return success(data=service.get_violations())


@demo_router.get("/research-kpis", summary="科研KPI", description="获取科研KPI数据", tags=["demo"])
def research_kpis(service: DashboardService = Depends()):
    return success(data=service.get_research_kpis())


@demo_router.get("/pi-sources", summary="PI来源", description="获取PI来源数据", tags=["demo"])
def pi_sources(service: DashboardService = Depends()):
    return success(data=service.get_pi_sources())


@demo_router.get("/product-match-stats", summary="产品匹配统计", description="获取产品匹配统计数据", tags=["demo"])
def product_match_stats(service: DashboardService = Depends()):
    return success(data=service.get_product_match_stats())


# ── inference_router ──────────────────────────────────────────────────

inference_router = APIRouter(prefix="/api/v1/inference", tags=["推演"])


class InferenceRequest(BaseModel):
    scenario: str = Field(..., min_length=1, description="推演场景描述")
    domain: str = Field(..., description="推演领域")
    horizon_days: int = Field(90, ge=1, le=365)


class ScenarioItem(BaseModel):
    id: str
    scenario: str
    domain: str
    reason: str


_PRESET_SCENARIOS: list[dict] = [
    {"id": "s1", "scenario": "如果张代表继续当前拜访模式", "domain": "sales", "reason": "费用趋势异常上升"},
    {"id": "s2", "scenario": "如果陈主任流失", "domain": "compliance", "reason": "关键HCP稳定性下降"},
    {"id": "s3", "scenario": "竞品在华东降价", "domain": "opportunity", "reason": "竞品活跃度上升"},
    {"id": "s4", "scenario": "砍生物线20%预算", "domain": "sales", "reason": "预算分配变化"},
    {"id": "s5", "scenario": "缩减学术会议场次", "domain": "compliance", "reason": "合规成本压力"},
]


@inference_router.post("/run", tags=["推演"])
async def run_inference(
    body: InferenceRequest,
    current_user: dict = Depends(require_scope("visit")),
    pipeline: InferencePipeline = Depends(),
) -> Any:
    pipeline = pipeline or InferencePipeline()
    result = await pipeline.run(
        scenario=body.scenario,
        domain=body.domain,
        user_id=str(current_user.get("sub", "")),
        horizon_days=body.horizon_days,
    )
    return success(data=result.__dict__ if hasattr(result, "__dict__") else result)


@inference_router.get("/scenarios", tags=["推演"])
async def list_scenarios(
    domain: str | None = None,
    current_user: dict = Depends(require_scope("visit")),
) -> Any:
    items = [s for s in _PRESET_SCENARIOS if not domain or s["domain"] == domain]
    return success(data=items)


# ── product_router ────────────────────────────────────────────────────

product_router = APIRouter(prefix="/api/products", tags=["products"])


class ProductCreate(BaseModel):
    name: str
    category: str = ""
    brand: str = ""
    model: str = ""
    spec: str = ""
    unit_price: float = 0.0
    keywords: list[str] = []
    tech_params: dict = {}
    cert_status: str = ""


@product_router.get("/search", summary="搜索产品", description="根据关键词和分类搜索科研产品", tags=["products"])
def search_products(
    q: str = Query("", description="Search keyword"),
    category: str = Query("", description="Category filter"),
    _: dict = Depends(require_scope("research")),
    service: ProductService = Depends(),
):
    results = service.search(q=q, category=category)
    return success(data=results)


@product_router.get("/{product_id}", summary="产品详情", description="获取指定产品的详细信息", tags=["products"])
def get_product(
    product_id: int,
    _: dict = Depends(require_scope("research")),
    service: ProductService = Depends(),
):
    product = service.get_by_id(product_id)
    return success(data=product)


@product_router.post("", status_code=201, summary="创建产品", description="创建新的科研产品信息", tags=["products"])
def create_product(
    body: ProductCreate,
    _: dict = Depends(require_scope("research")),
    service: ProductService = Depends(),
):
    product = service.create(
        name=body.name,
        category=body.category,
        brand=body.brand,
        model=body.model,
        spec=body.spec,
        unit_price=body.unit_price,
        keywords=body.keywords,
        tech_params=body.tech_params,
        cert_status=body.cert_status,
    )
    return success(data=product)


# ── admission_router ──────────────────────────────────────────────────

admission_router = APIRouter(prefix="/api/v1/admission", tags=["入院流程"])


class AdmissionCreate(BaseModel):
    hospital_name: str
    department: str = ""
    product: str
    status: str = "待提交"
    meeting_date: Optional[str] = None
    notes: str = ""
    rep_id: int = 0


class StatusUpdate(BaseModel):
    status: str


@admission_router.post("", status_code=status.HTTP_201_CREATED, summary="创建入院记录", tags=["入院流程"])
def create(body: AdmissionCreate, _: dict = Depends(require_scope("visit")), service: AdmissionService = Depends()):
    result = service.create(body.model_dump())
    return success(data=result)


@admission_router.get("", summary="入院列表", tags=["入院流程"])
def list_admissions(
    status: Optional[str] = Query(None),
    rep_id: Optional[int] = Query(None),
    service: AdmissionService = Depends(),
):
    result = service.list(status, rep_id)
    return success(data=result)


@admission_router.get("/{record_id}", summary="入院详情", tags=["入院流程"])
def get_admission(record_id: int, service: AdmissionService = Depends()):
    result = service.get_by_id(record_id)
    if not result:
        from fastapi import HTTPException

        raise HTTPException(404, "not found")
    return success(data=result)


@admission_router.put("/{record_id}/status", summary="更新节点状态", tags=["入院流程"])
def update_status(record_id: int, body: StatusUpdate, _: dict = Depends(require_scope("visit")), service: AdmissionService = Depends()):
    result = service.update_status(record_id, body.status)
    if not result:
        from fastapi import HTTPException

        raise HTTPException(404, "not found or invalid status")
    return success(data=result)


# ── mrc_workflow_router ──────────────────────────────────────────────

mrc_router = APIRouter(prefix="/api/mrc", tags=["MRC审核流"])


@mrc_router.post("/material", status_code=201, summary="创建营销材料", tags=["MRC审核流"])
def create_mrc_material(body: MaterialCreate, _: dict = Depends(require_scope("visit"))):
    return success(data=create_material(body))


@mrc_router.put("/material/{id}/submit-mrc", summary="提交 MRC 审核", tags=["MRC审核流"])
def submit_material_to_mrc(id: str, _: dict = Depends(require_scope("visit"))):
    return success(data=submit_mrc(id))


@mrc_router.put("/material/{id}/mrc-decision", summary="MRC 审核决策", tags=["MRC审核流"])
def decide_mrc_material(id: str, body: MRCDecisionRequest, _: dict = Depends(require_scope("visit"))):
    return success(data=mrc_decision(id, body))


@mrc_router.put("/material/{id}/compliance-approve", summary="合规审批", tags=["MRC审核流"])
def approve_material_compliance(id: str, body: ComplianceApproveRequest, _: dict = Depends(require_scope("visit"))):
    submit_compliance(id)
    return success(data=approve(id, body))


@mrc_router.post("/material/{id}/distribute", summary="分发营销材料", tags=["MRC审核流"])
def distribute_material(id: str, body: DistributionRequest, _: dict = Depends(require_scope("visit"))):
    return success(data=distribute(id, body))


@mrc_router.get("/material/{id}/effectiveness", summary="查看材料效果", tags=["MRC审核流"])
def get_material_effectiveness(id: str, _: dict = Depends(require_scope("visit"))):
    return success(data=track(id))


# ── content_factory_router ────────────────────────────────────────────

cf_router = APIRouter(prefix="/content-factory", tags=["内容工厂"])


class CreateTemplateRequest(BaseModel):
    template_key: str
    name: str = ""
    content_type: str = "text"
    template_body: str = ""
    compliance_rules: str = "[]"
    variables: str = "{}"


class RenderRequest(BaseModel):
    template_key: str
    variables: dict = {}


@cf_router.post("", status_code=status.HTTP_201_CREATED, summary="创建模板", description="创建新的内容模板", tags=["内容工厂"])
def create_template(
    body: CreateTemplateRequest,
    current_user: dict = Depends(require_scope("visit")),
    service: ContentFactoryService = Depends(),
) -> Any:
    result = service.create_template(
        template_key=body.template_key,
        name=body.name,
        content_type=body.content_type,
        template_body=body.template_body,
        compliance_rules=body.compliance_rules,
        variables=body.variables,
    )
    return success(data=result)


@cf_router.post("/render", summary="渲染模板", description="渲染内容模板并执行合规检查", tags=["内容工厂"])
def render_template(
    body: RenderRequest,
    current_user: dict = Depends(require_scope("visit")),
    service: ContentFactoryService = Depends(),
) -> Any:
    result = service.render(
        template_key=body.template_key,
        variables=body.variables,
    )
    return success(data=result)


@cf_router.get("", summary="模板列表", description="列出所有可用的内容模板", tags=["内容工厂"])
def list_templates(
    current_user: dict = Depends(require_scope("visit")),
    service: ContentFactoryService = Depends(),
) -> Any:
    return success(data=service.list_templates())


# ── data_platform_router ──────────────────────────────────────────────

data_platform_router = APIRouter(prefix="/api/data-platform", tags=["data-platform"])


@data_platform_router.post(
    "/pipeline/run",
    response_model=PipelineRunResult,
    summary="执行ETL管道",
    description="启动数据平台ETL管道，从数据源提取、转换并加载至数据仓库。",
    tags=["data-platform"],
)
def run_pipeline(
    current_user: dict = Depends(require_scope("visit")),
    pipeline: ETLPipeline = Depends(ETLPipeline),
) -> Any:
    result = pipeline.run()
    return success(data=result.dict())


@data_platform_router.post(
    "/olap/query",
    summary="OLAP多维查询",
    description="在多维数据上执行聚合查询，支持自定义维度、度量和过滤条件。",
    tags=["data-platform"],
)
def olap_query(
    payload: OLAPQuery = Body(...),
    current_user: dict = Depends(require_scope("visit")),
) -> Any:
    service = OLAPService()
    rows = service.query(
        dimensions=payload.dimensions or None,
        metrics=None,
        filters=payload.filters,
        date_from=payload.date_from,
        date_to=payload.date_to,
        limit=payload.limit,
    )
    return success(data={"rows": rows, "count": len(rows)})


@data_platform_router.get(
    "/bi/report",
    summary="嵌入式BI报表数据",
    description="获取聚合后的BI报表数据集，可按日期、团队等维度分组展示关键指标。",
    tags=["data-platform"],
)
def bi_report(
    date_from: str | None = None,
    date_to: str | None = None,
    team_id: str | None = None,
    current_user: dict = Depends(require_scope("visit")),
) -> Any:
    service = BIViewService()
    return success(data=service.report_data(date_from=date_from, date_to=date_to, team_id=team_id))


# ── top-level aggregator router ───────────────────────────────────────

router = APIRouter()
router.include_router(asr_router)
router.include_router(demo_router)
router.include_router(inference_router)
router.include_router(product_router)
router.include_router(admission_router)
router.include_router(mrc_router)
router.include_router(cf_router)
router.include_router(data_platform_router)

__all__ = [
    "router",
    "admission_router",
    "asr_router",
    "cf_router",
    "data_platform_router",
    "demo_router",
    "inference_router",
    "mrc_router",
    "product_router",
]
