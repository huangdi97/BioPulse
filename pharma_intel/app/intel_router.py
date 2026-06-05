from fastapi import APIRouter, HTTPException, Query

from pharma_intel.app.seed_data import papers, pi_profiles, targets
from shared.base import ErrorCode

router = APIRouter(prefix="/api/intel", tags=["制药情报"])


def _ok(data, message: str = "ok") -> dict:
    return {"code": 0, "message": message, "data": data}


def _not_found(entity: str, id: int):
    raise HTTPException(
        status_code=404,
        detail={"code": ErrorCode.NOT_FOUND, "message": f"{entity} not found", "data": None},
    )


# ── Papers ──


@router.get("/papers")
def search_papers(
    q: str = Query("", description="搜索关键词"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    kw = q.strip().lower()
    if kw:
        filtered = [
            p for p in papers if kw in p["title"].lower() or any(kw in a.lower() for a in p["authors"]) or any(kw in k.lower() for k in p["keywords"])
        ]
    else:
        filtered = list(papers)

    total = len(filtered)
    start = (page - 1) * page_size
    items = filtered[start : start + page_size]
    return _ok({"items": items, "total": total, "page": page})


@router.get("/papers/{id}")
def get_paper(id: int):
    for p in papers:
        if p["id"] == id:
            return _ok(p)
    _not_found("Paper", id)


# ── PI Profiles ──


@router.get("/pi")
def search_pi(
    q: str = Query("", description="搜索关键词"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    kw = q.strip().lower()
    if kw:
        filtered = [
            pi
            for pi in pi_profiles
            if kw in pi["name"].lower() or kw in pi["institution"].lower() or any(kw in a.lower() for a in pi["research_areas"])
        ]
    else:
        filtered = list(pi_profiles)

    total = len(filtered)
    start = (page - 1) * page_size
    items = filtered[start : start + page_size]
    return _ok({"items": items, "total": total, "page": page})


@router.get("/pi/{id}")
def get_pi(id: int):
    for pi in pi_profiles:
        if pi["id"] == id:
            return _ok(pi)
    _not_found("PI", id)


# ── Targets ──


@router.get("/targets/categories")
def list_categories():
    cats = sorted({t["category"] for t in targets})
    return _ok(cats)


@router.get("/targets")
def list_targets(
    category: str = Query("", description="分类过滤"),
    sort_by: str = Query("paper_count", description="排序字段"),
    sort_dir: str = Query("desc", description="排序方向 desc|asc"),
):
    filtered = [t for t in targets if t["category"] == category] if category else list(targets)

    reverse = sort_dir.lower() != "asc"
    if sort_by in ("paper_count", "trial_count", "growth", "id", "name"):
        filtered.sort(key=lambda t: t.get(sort_by, 0) if isinstance(t.get(sort_by), (int, float)) else str(t.get(sort_by, "")), reverse=reverse)

    return _ok(filtered)


@router.get("/targets/{id}")
def get_target(id: int):
    for t in targets:
        if t["id"] == id:
            return _ok(t)
    _not_found("Target", id)
