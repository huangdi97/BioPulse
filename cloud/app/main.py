import os
import time
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import traceback
import sqlite3
from shared.middleware import RequestIDMiddleware
from shared.rate_limiter import RateLimiterMiddleware
import logging
from shared.config import settings
from cloud.app.database import init_db, DB_PATH
from cloud.app.research_database import init_research_db as init_research
from cloud.app.auth_router import router as auth_router
from cloud.app.api_tokens import router as tokens_router
from cloud.app.compliance_router import router as compliance_router
from cloud.app.users_router import router as users_router
from cloud.app.contents_router import router as contents_router
from cloud.app.ai_gateway import router as ai_router
from cloud.app.teams_router import router as teams_router
from cloud.app.audit_router import router as audit_router
from cloud.app.notification_router import router as notification_router
from cloud.app.board_router import router as board_router
from cloud.app.dashboard_router import router as dashboard_router
from cloud.app.customer_router import router as customer_router
from cloud.app.interaction_router import router as interaction_router
from cloud.app.config_router import router as config_router
from cloud.app.export_router import router as export_router
from cloud.app.opportunity_router import router as opportunity_router
from cloud.app.task_router import router as task_router
from cloud.app.market_intel_router import router as market_intel_router
from cloud.app.agent_role_router import router as agent_role_router
from cloud.app.agent_pipeline_router import router as agent_pipeline_router
from cloud.app.decision_intel_router import router as decision_intel_router
from cloud.app.compliance_v2_router import router as compliance_v2_router
from cloud.app.mdt_engine_router import router as mdt_engine_router
from cloud.app.memory_gate_router import router as memory_gate_router
from cloud.app.world_tree_router import router as world_tree_router
from cloud.app.route_router import router as route_router
from cloud.app.hcp_sandbox_router import router as hcp_sandbox_router
from cloud.app.training_coach_router import router as training_coach_router
from cloud.app.soap_decision_router import router as soap_decision_router
from cloud.app.memory_utility_router import router as memory_utility_router
from cloud.app.brain_memory_router import router as brain_memory_router
# from cloud.app.identity_router import router as identity_router  # ❄️ 冻结
# from cloud.app.privacy_router import router as privacy_router  # ❄️ 冻结
from cloud.app.kg_router import router as kg_router
from cloud.app.recommend_router import router as recommend_router
from cloud.app.collaboration_router import router as collaboration_router
from cloud.app.event_bus_router import router as event_bus_router
from cloud.app.memory_consolidation_router import router as memory_consolidation_router
from cloud.app.agent_execution_router import router as agent_execution_router
from cloud.app.mcp_router import router as mcp_router
from cloud.app.orchestrate_router import router as orchestrate_router
from cloud.app.causal_router import router as causal_router
from cloud.app.compute_router import router as compute_router
from cloud.app.nmpa_router import router as nmpa_router
from cloud.app.training_scripts_router import router as training_scripts_router
from cloud.app.marketplace_router import router as marketplace_router
from fastapi.staticfiles import StaticFiles
# from cloud.app.edge_router import router as edge_router  # ❄️ 冻结
from cloud.app.settings_router import router as settings_router
from cloud.app.visit_router import router as visit_router
from cloud.app.routers.pubmed_router import router as pubmed_router
from cloud.app.routers.pi_router import router as pi_router
from cloud.app.routers.product_router import router as product_router
from cloud.app.routers.langgraph_test_router import router as langgraph_test_router
from cloud.app.routers.enforcer_router import router as enforcer_router
from cloud.app.routers.compliance_dashboard_router import router as compliance_dashboard_router
from cloud.app.routers.research_pi_router import router as research_pi_router
from cloud.app.routers.research_product_router import router as research_product_router
from cloud.app.routers.research_quotation_router import router as research_quotation_router
from cloud.app.routers.research_enforcer_router import router as research_enforcer_router
from cloud.app.routers.research_export_router import router as research_export_router
from cloud.app.routers.research_matching_router import router as research_matching_router
from cloud.app.routers.research_route_router import router as research_route_router
from cloud.app.routers.research_quotation_workflow_router import router as research_quotation_workflow_router
from cloud.app.token_budget_router import router as token_budget_router
# Serve frontend SPA
START_TIME = time.time()

app = FastAPI(
    title="一云四端 · Cloud API",
    description="面向医药+生物双主线的智能CRM SaaS。包含认证、合规、商机、Agent、记忆系统、知识图谱、MDT会诊、因果推理、合规规则引擎等核心模块。",
    version="1.0.0",
    openapi_tags=[
        {"name": "认证", "description": "用户登录、注册、令牌刷新、JWT验证"},
        {"name": "合规", "description": "合规检测、规则管理、合规仪表板、合规证书"},
        {"name": "商机", "description": "商机管理、线索跟踪、客户管理"},
        {"name": "拜访", "description": "拜访计划、执行、记录"},
        {"name": "Agent系统", "description": "Agent角色、管道、执行、记忆"},
        {"name": "MDT会诊", "description": "多专家会诊、辩论引擎、决策树"},
        {"name": "知识图谱", "description": "知识图谱查询、关系分析"},
        {"name": "记忆系统", "description": "记忆门控、巩固、世界树、效用评估"},
        {"name": "❄️ 因果推理", "description": "因果分析、决策推理（冻结）"},
        {"name": "团队管理", "description": "团队、看板、任务分配"},
        {"name": "审计日志", "description": "操作审计、合规审计链"},
        {"name": "数据导出", "description": "报表导出、数据分析"},
        {"name": "科研线", "description": "PI管理、产品匹配、询价报价、科研合规"},
        {"name": "配置", "description": "系统配置、个性化设置"},
        {"name": "系统", "description": "健康检查、服务状态"},
        {"name": "Token 管理", "description": "Token 预算配置、用量监控、告警管理"},
    ]
)

@app.middleware("http")
async def api_path_rewrite(request: Request, call_next):
    path = request.scope["path"]
    if path.startswith("/api/cloud/"):
        new_path = "/" + path[len("/api/cloud/"):]
        request.scope["path"] = new_path
        if "raw_path" in request.scope:
            request.scope["raw_path"] = new_path.encode()
    return await call_next(request)

app.add_middleware(RequestIDMiddleware)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    code_map = {401: 1, 403: 2, 404: 3, 409: 4, 422: 4, 429: 7}
    error_code = code_map.get(exc.status_code, 5)
    return JSONResponse(
        status_code=exc.status_code,
        content={'code': error_code, 'message': exc.detail, 'data': None, 'request_id': request.state.request_id}
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger = logging.getLogger('app')
    logger.error(
        'Unhandled exception',
        extra={'request_id': request.state.request_id},
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={'code': 5, 'message': 'Internal server error', 'data': None, 'request_id': request.state.request_id}
    )


_cors_origins = settings.cors_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins.split(',') if _cors_origins != '*' else ['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.add_middleware(RateLimiterMiddleware, default_rate=100, window=60)

app.include_router(auth_router)
app.include_router(tokens_router)
app.include_router(compliance_router)
app.include_router(users_router)
app.include_router(contents_router)
app.include_router(ai_router)
app.include_router(teams_router)
app.include_router(audit_router)
app.include_router(notification_router)
app.include_router(board_router)
app.include_router(dashboard_router)
app.include_router(customer_router)
app.include_router(interaction_router)
app.include_router(config_router)
app.include_router(export_router)
app.include_router(opportunity_router)
app.include_router(task_router)
app.include_router(market_intel_router)
app.include_router(agent_role_router)
app.include_router(agent_pipeline_router)
app.include_router(decision_intel_router)
app.include_router(compliance_v2_router)
app.include_router(mdt_engine_router)
app.include_router(memory_gate_router)
app.include_router(world_tree_router)
app.include_router(route_router)
app.include_router(hcp_sandbox_router)
app.include_router(training_coach_router)
app.include_router(soap_decision_router)
app.include_router(memory_utility_router)
app.include_router(brain_memory_router)
# app.include_router(identity_router)  # ❄️ 冻结
# app.include_router(privacy_router)  # ❄️ 冻结
app.include_router(kg_router)
app.include_router(recommend_router)
app.include_router(collaboration_router)
app.include_router(event_bus_router)
app.include_router(memory_consolidation_router)
app.include_router(agent_execution_router)
app.include_router(mcp_router)
app.include_router(orchestrate_router)
app.include_router(causal_router)
app.include_router(compute_router)
app.include_router(nmpa_router)
app.include_router(training_scripts_router)
app.include_router(marketplace_router)
# app.include_router(edge_router)  # ❄️ 冻结
app.include_router(settings_router)
app.include_router(visit_router)
app.include_router(pubmed_router)
app.include_router(pi_router)
app.include_router(product_router)
app.include_router(langgraph_test_router)
app.include_router(enforcer_router)
app.include_router(compliance_dashboard_router)
app.include_router(research_pi_router)
app.include_router(research_product_router)
app.include_router(research_quotation_router)
app.include_router(research_enforcer_router)
app.include_router(research_export_router)
app.include_router(research_matching_router)
app.include_router(research_route_router)
app.include_router(research_quotation_workflow_router)
app.include_router(token_budget_router)

@app.on_event("startup")
def startup():
    init_db()
    init_research()


@app.get("/health")
def health():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("SELECT 1")
        conn.close()
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    return {
        "status": "ok",
        "db": db_status,
        "uptime": int(time.time() - START_TIME),
        "version": "0.1.0",
    }


# Serve frontend SPA
app.mount("/assets", StaticFiles(directory="static/assets"), name="assets")
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.api_route("/{path_name:path}", methods=["GET"])
async def catch_all(path_name: str):
    if path_name.startswith("api/") or path_name.startswith("assets/"):
        from starlette import status
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    from fastapi.responses import FileResponse
    from starlette.responses import Response
    headers = {"Cache-Control": "no-cache, no-store, must-revalidate"}
    return Response(
        content=open("static/index.html", "rb").read(),
        media_type="text/html",
        headers=headers,
    )
