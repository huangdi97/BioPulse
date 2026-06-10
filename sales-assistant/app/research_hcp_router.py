"""Research HCP router: local PI profiles plus cloud-powered research actions."""

from __future__ import annotations

from datetime import UTC, datetime
from threading import Lock
from typing import Any

import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from starlette.exceptions import HTTPException
from starlette.requests import Request

from sales_assistant.app.services.research_hcp_service import enrich_research_profile, get_grants, get_papers
from shared.app_settings import settings
from shared.auth_scope import require_scope

router = APIRouter(prefix="/api/research/hcp")

TIMEOUT_SECONDS = 30.0


class PiCreate(BaseModel):
    """Request body for creating a PI/HCP research profile."""

    model_config = ConfigDict(extra="allow")

    name: str = Field(..., min_length=1)
    institution: str = ""
    hospital: str = ""
    department: str = ""
    title: str = ""
    specialty: str = ""
    city: str = ""
    hcp_id: int | None = None
    research_areas: list[str] = Field(default_factory=list)
    total_papers: int = 0
    total_grants: int = 0
    h_index: int = 0


class MatchRequest(BaseModel):
    """Optional match inputs; empty body matches products for the PI id."""

    method_description: str | None = None


_PI_DATA: list[dict[str, Any]] = [
    {
        "id": 1,
        "name": "Dr. Lin Wei",
        "institution": "Shanghai Ruijin Hospital",
        "hospital": "Shanghai Ruijin Hospital",
        "department": "Oncology",
        "title": "Principal Investigator",
        "specialty": "Lung cancer",
        "city": "Shanghai",
        "hcp_id": None,
        "research_areas": ["NSCLC", "immunotherapy", "biomarkers"],
        "total_papers": 42,
        "total_grants": 6,
        "h_index": 18,
        "created_at": "2026-06-01T00:00:00Z",
    },
    {
        "id": 2,
        "name": "Dr. Chen Xia",
        "institution": "Peking Union Medical College Hospital",
        "hospital": "Peking Union Medical College Hospital",
        "department": "Rheumatology",
        "title": "Associate Professor",
        "specialty": "Autoimmune disease",
        "city": "Beijing",
        "hcp_id": None,
        "research_areas": ["SLE", "clinical trials", "real-world evidence"],
        "total_papers": 31,
        "total_grants": 4,
        "h_index": 14,
        "created_at": "2026-06-01T00:00:00Z",
    },
]
_PI_LOCK = Lock()
_NEXT_ID = 3


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _find_pi(pi_id: int) -> dict[str, Any]:
    for pi in _PI_DATA:
        if pi["id"] == pi_id:
            return pi
    raise HTTPException(status_code=404, detail="PI not found")


def _find_research_hcp(id: str) -> dict[str, Any]:
    if id.isdigit():
        return _find_pi(int(id))
    if id == "hcp-001":
        return {
            "id": id,
            "hcp_id": id,
            "name": "张主任",
            "institution": "上海瑞金医院",
            "hospital": "上海瑞金医院",
            "department": "肿瘤科",
            "title": "Principal Investigator",
            "specialty": "肺癌免疫治疗",
            "city": "Shanghai",
            "research_areas": ["NSCLC", "immunotherapy", "biomarkers"],
            "total_papers": 3,
            "total_grants": 2,
        }
    raise HTTPException(status_code=404, detail="PI not found")


def _with_research_profile(pi: dict[str, Any], hcp_id: str) -> dict[str, Any]:
    profile = enrich_research_profile(hcp_id)
    profile_data = profile.model_dump()
    return {
        **pi,
        **profile_data,
        "research_profile": profile_data,
    }


def _cloud_url(path: str) -> str:
    return f"{settings.cloud_api_base.rstrip('/')}{path}"


def _auth_headers(request: Request) -> dict[str, str]:
    auth = request.headers.get("authorization")
    return {"Authorization": auth} if auth else {}


def _read_cloud_response(response: httpx.Response) -> dict[str, Any]:
    try:
        data = response.json()
    except ValueError as exc:
        raise HTTPException(status_code=502, detail="Cloud API returned invalid JSON") from exc
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=data)
    return data


@router.get("", tags=["科研PI"])
def list_pi(q: str = "") -> dict[str, Any]:
    """List in-memory PI profiles, optionally filtered by keyword."""
    keyword = q.strip().lower()
    if not keyword:
        items = list(_PI_DATA)
    else:
        items = [
            pi
            for pi in _PI_DATA
            if keyword in pi["name"].lower()
            or keyword in pi.get("institution", "").lower()
            or keyword in pi.get("department", "").lower()
            or any(keyword in area.lower() for area in pi.get("research_areas", []))
        ]
    return {"code": 0, "data": items, "message": "success"}


@router.post("", status_code=201, tags=["科研PI"])
def create_pi(body: PiCreate, _: dict = Depends(require_scope("research"))) -> dict[str, Any]:
    """Create an in-memory PI profile."""
    global _NEXT_ID

    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="name is required")

    payload = body.model_dump()
    extras = body.model_extra or {}
    payload.update(extras)
    payload["name"] = name
    if not payload.get("institution") and payload.get("hospital"):
        payload["institution"] = payload["hospital"]
    if not payload.get("hospital") and payload.get("institution"):
        payload["hospital"] = payload["institution"]

    with _PI_LOCK:
        payload["id"] = _NEXT_ID
        _NEXT_ID += 1
        payload["created_at"] = _now_iso()
        _PI_DATA.append(payload)

    return {"code": 0, "data": payload, "message": "success"}


@router.get("/{id}", tags=["科研PI"])
def get_pi_detail(id: str) -> dict[str, Any]:
    """Return a PI profile by id."""
    pi = _find_research_hcp(id)
    hcp_id = id if not id.isdigit() else f"pi-{id}"
    return {"code": 0, "data": _with_research_profile(pi, hcp_id), "message": "success"}


@router.get("/{id}/papers", tags=["科研PI"])
def get_pi_papers(id: str) -> dict[str, Any]:
    """Return PI paper details."""
    _find_research_hcp(id)
    hcp_id = id if not id.isdigit() else f"pi-{id}"
    return {"code": 0, "data": [paper.model_dump() for paper in get_papers(hcp_id)], "message": "success"}


@router.get("/{id}/grants", tags=["科研PI"])
def get_pi_grants(id: str) -> dict[str, Any]:
    """Return PI grant details."""
    _find_research_hcp(id)
    hcp_id = id if not id.isdigit() else f"pi-{id}"
    return {"code": 0, "data": [grant.model_dump() for grant in get_grants(hcp_id)], "message": "success"}


@router.post("/{id}/match", tags=["科研PI"])
def match_products(id: int, request: Request, body: MatchRequest | None = None, _: dict = Depends(require_scope("research"))) -> dict[str, Any]:
    """Proxy PI product matching to the cloud research matching API."""
    _find_pi(id)
    if body and body.method_description:
        url = _cloud_url("/api/research/matching/by-method")
        payload = {"method_description": body.method_description}
    else:
        url = _cloud_url("/api/research/matching/for-pi")
        payload = {"pi_id": id}

    try:
        with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
            response = client.post(url, json=payload, headers=_auth_headers(request))
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Cloud API request failed: {exc}") from exc
    return _read_cloud_response(response)


@router.get("/{id}/trajectory", tags=["科研PI"])
def get_research_trajectory(id: int, request: Request) -> dict[str, Any]:
    """Proxy PI research trajectory lookup to the cloud trajectory API."""
    _find_pi(id)
    url = _cloud_url(f"/api/research/trajectory/pi/{id}/trajectory")
    try:
        with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
            response = client.get(url, headers=_auth_headers(request))
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Cloud API request failed: {exc}") from exc
    return _read_cloud_response(response)
