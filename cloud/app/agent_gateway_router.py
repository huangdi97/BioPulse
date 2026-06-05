import json
import urllib.request

from fastapi import APIRouter, Request
from pydantic import BaseModel

GATEWAY_ROUTES: dict[str, str] = {
    "query_bidding": "GET /opportunity/bidding/list",
    "query_opportunity": "GET /opportunity/opportunity/list",
    "query_knowledge_graph": "GET /cloud/kg/query",
    "create_notification": "POST /cloud/notification/create",
    "analyze_with_llm": "POST /ai/chat",
    "compliance_check": "POST /cloud/compliance/check",
    "search_memory": "POST /memory/recall",
    "write_memory": "POST /memory/entries",
}

router = APIRouter(prefix="/agent-gateway", tags=["Agent Gateway"])

BASE_URL = "http://localhost:8000"


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
            return {"success": True, "data": json.loads(raw), "error": ""}
    except Exception as e:
        return {"success": False, "data": None, "error": str(e)}


@router.post("/execute")
def execute(body: ExecuteRequest, request: Request):
    route = GATEWAY_ROUTES.get(body.tool_name)
    if not route:
        return {"success": False, "data": None, "error": f"unknown tool: {body.tool_name}"}

    parts = route.split(" ", 1)
    method = parts[0]
    path = parts[1] if len(parts) > 1 else ""
    auth_header = request.headers.get("Authorization", "")
    return _http_forward(method, path, body.params, auth_header)


@router.post("/tools/register")
def register_tool(body: RegisterRequest):
    GATEWAY_ROUTES[body.tool_name] = f"{body.method.upper()} {body.url}"
    return {
        "success": True,
        "data": {
            "tool_name": body.tool_name,
            "method": body.method.upper(),
            "url": body.url,
            "description": body.description,
            "permission_level": body.permission_level,
        },
        "error": "",
    }


@router.get("/tools")
def list_tools():
    return {"success": True, "data": list(GATEWAY_ROUTES.keys()), "error": ""}
