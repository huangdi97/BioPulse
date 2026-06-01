from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from shared.auth import get_current_user
from shared.base import success
from cloud.app.services.nmpa_service import NmpaService

router = APIRouter(prefix="/compliance/gov", tags=["NMPA Compliance"])


class NmpaCheck(BaseModel):
    document_type: str
    content: str


@router.post("/check")
def nmpa_check(
    body: NmpaCheck,
    user: dict = Depends(get_current_user),
    service: NmpaService = Depends(),
):
    user_id = int(user["sub"])
    result = service.check(body.document_type, body.content, user_id)
    return success(result)


@router.get("/logs/list")
def logs_list(
    document_type: Optional[str] = Query(None),
    check_result: Optional[str] = Query(None),
    human_review_required: Optional[int] = Query(None),
    user: dict = Depends(get_current_user),
    service: NmpaService = Depends(),
):
    result = service.list_logs(
        document_type=document_type,
        check_result=check_result,
        human_review_required=human_review_required,
    )
    return success(result)
