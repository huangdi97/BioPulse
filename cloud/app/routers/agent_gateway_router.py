"""Agent 网关路由转发。"""

import json
import urllib.request

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from starlette import status

from shared.app_settings import settings
from shared.auth_scope import require_scope
from shared.base import error, success
from shared.error_code import ErrorCode

GATEWAY_ROUTES: dict[str, str] = {
    "query_bidding": "GET /opportunity/bidding/list",
    "query_opportunity": "GET /opportunity/opportunity/list",
    "query_knowledge_graph": "GET /cloud/kg/query",
    "create_notification": "POST /cloud/notification/create",
    "analyze_with_llm": "POST /ai/chat",
    "compliance_check": "POST /cloud/compliance/check",
    "search_memory": "POST /memory/recall",
    "write_memory": "POST /memory/entries",
    "verify_expense": "POST /cloud/compliance/expense/check",
    "verify_visit": "POST /cloud/compliance/visit/check",
    "trace_distribution": "POST /cloud/compliance/distribution/trace",
    "triangulation_check": "POST /cloud/compliance/triangulation/check",
    "write_audit_log": "POST /cloud/compliance/audit/log",
    "query_visit_history": "POST /cloud/visit/history/query",
    "query_hcp_profile": "POST /cloud/hcp/profile/query",
    "query_competitor_intel": "POST /cloud/competitor/intel/query",
    "run_causal_attribution": "POST /cloud/causal/attribution/run",
    "generate_brief": "POST /cloud/visit/brief/generate",
    "collect_related_data": "POST /cloud/analysis/collect",
    "run_pattern_analysis": "POST /cloud/analysis/pattern",
    "run_causal_inference": "POST /cloud/causal/inference",
    "generate_narrative": "POST /cloud/analysis/narrative",
    "discover_related_patterns": "POST /cloud/analysis/related-patterns",
    "trigger_red_light": "POST /cloud/compliance/red-light/trigger",
}

router = APIRouter(prefix="/agent-gateway", tags=["Agent Gateway"])

BASE_URL = settings.cloud_api_base


class ExecuteRequest(BaseModel):
    tool_name: str
    params: dict


class RegisterRequest(BaseModel):
    tool_name: str
    method: str
    url: str
    description: str
    permission_level: str = "read"


def _http_forward(method: str, path: str, params: dict, auth_header: str) -> dict:
    url = f"{BASE_URL}{path}"
    method_upper = method.upper()
    data = json.dumps(params).encode("utf-8") if method_upper == "POST" else None
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": auth_header,
        },
        method=method_upper,
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as rp:
            raw = rp.read().decode("utf-8")
            return success(data=json.loads(raw))
    except Exception as e:
        return error(ErrorCode.INTERNAL_ERROR, str(e))


@router.post("/execute", summary="执行工具", description="通过网关转发执行指定的Agent工具", tags=["Agent Gateway"])
def execute(body: ExecuteRequest, request: Request, _: dict = Depends(require_scope("visit"))):
    route = GATEWAY_ROUTES.get(body.tool_name)
    if not route:
        return error(ErrorCode.NOT_FOUND, f"unknown tool: {body.tool_name}")

    parts = route.split(" ", 1)
    method = parts[0]
    path = parts[1] if len(parts) > 1 else ""
    auth_header = request.headers.get("Authorization", "")
    return _http_forward(method, path, body.params, auth_header)


@router.post(
    "/tools/register", status_code=status.HTTP_201_CREATED, summary="注册工具", description="向网关注册一个新的Agent工具路由", tags=["Agent Gateway"]
)
def register_tool(body: RegisterRequest, _: dict = Depends(require_scope("visit"))):
    GATEWAY_ROUTES[body.tool_name] = f"{body.method.upper()} {body.url}"
    return success(
        data={
            "tool_name": body.tool_name,
            "method": body.method.upper(),
            "url": body.url,
            "description": body.description,
            "permission_level": body.permission_level,
        }
    )


@router.get("/tools", summary="工具列表", description="获取所有已注册的Agent工具名称列表", tags=["Agent Gateway"])
def list_tools():
    return success(data=list(GATEWAY_ROUTES.keys()))
