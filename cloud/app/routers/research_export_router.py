"""科研导出路由：PI CSV 导出与报价单 JSON 导出。"""

from fastapi import APIRouter, Depends, HTTPException, Query
from starlette import status
from starlette.responses import Response

from cloud.app.services.research_export_service import export_pi_csv, export_quotation
from cloud.app.services.research_service import ResearchService
from shared.auth import get_current_user
from shared.auth_scope import require_scope

router = APIRouter(
    prefix="/api/research/export",
    tags=["科研线"],
    dependencies=[Depends(require_scope("research"))],
)


@router.get("/pi", tags=["Research Export"])
def export_pi(
    format: str = Query("csv", description="Export format"),
    current_user: dict = Depends(get_current_user),
):
    if format != "csv":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only CSV format supported")
    content = export_pi_csv()
    ResearchService().log_audit(
        event_type="export",
        entity_type="pi",
        entity_id=0,
        new_value="export_format=csv",
        operator=current_user.get("username", ""),
    )
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=pi_export.csv"},
    )


@router.get("/quotation/{quotation_id}", tags=["Research Export"])
def export_quotation_endpoint(
    quotation_id: int,
    current_user: dict = Depends(get_current_user),
):
    try:
        data = export_quotation(quotation_id)
        ResearchService().log_audit(
            event_type="export",
            entity_type="quotation",
            entity_id=quotation_id,
            new_value="export_format=json",
            operator=current_user.get("username", ""),
        )
        return {"code": 0, "data": data, "message": "success"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
