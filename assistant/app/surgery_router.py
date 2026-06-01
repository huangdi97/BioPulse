from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette import status

from shared.auth import get_current_user
from shared.base import ApiResponse, PaginatedResponse, success
from assistant.app.services.surgery_service import SurgeryService

router = APIRouter(prefix="/surgery-reminders", tags=["surgery"])


class SurgeryCreate(BaseModel):
    patient_name: str
    surgery_type: Optional[str] = None
    surgery_date: Optional[str] = None
    hospital: Optional[str] = None
    department: Optional[str] = None
    surgeon_name: Optional[str] = None
    pre_op_notes: Optional[str] = None
    post_op_notes: Optional[str] = None
    status: Optional[str] = None
    reminder_before: Optional[int] = None


class SurgeryUpdate(BaseModel):
    patient_name: Optional[str] = None
    surgery_type: Optional[str] = None
    surgery_date: Optional[str] = None
    hospital: Optional[str] = None
    department: Optional[str] = None
    surgeon_name: Optional[str] = None
    pre_op_notes: Optional[str] = None
    post_op_notes: Optional[str] = None
    status: Optional[str] = None
    reminder_before: Optional[int] = None


class SurgeryOut(BaseModel):
    id: int
    patient_name: str
    surgery_type: Optional[str] = None
    surgery_date: Optional[str] = None
    hospital: Optional[str] = None
    department: Optional[str] = None
    surgeon_name: Optional[str] = None
    pre_op_notes: Optional[str] = None
    post_op_notes: Optional[str] = None
    status: Optional[str] = None
    reminder_before: Optional[int] = None
    last_notified_at: Optional[str] = None
    notification_status: Optional[str] = None
    is_active: int
    created_by: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@router.post("")
def create_surgery(
    body: SurgeryCreate,
    service: SurgeryService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> JSONResponse:
    user_id = int(current_user["sub"])
    result = service.create(body, user_id)
    return JSONResponse(
        content=success(data=result).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@router.get("/today")
def today_surgeries(
    service: SurgeryService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[List[SurgeryOut]]:
    rows = service.today()
    return success(data=[SurgeryOut(**r) for r in rows])


@router.get("")
def list_surgeries(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    patient_name: Optional[str] = Query(None),
    surgery_status: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    service: SurgeryService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[PaginatedResponse[SurgeryOut]]:
    total, total_pages, rows = service.list(
        page, page_size, patient_name, surgery_status, date_from, date_to,
    )
    return success(
        data=PaginatedResponse(
            items=[SurgeryOut(**dict(r)) for r in rows],
            total=total, page=page, page_size=page_size, total_pages=total_pages,
        )
    )


@router.post("/check-now")
def check_reminders_now(
    service: SurgeryService = Depends(),
    current_user: dict = Depends(get_current_user),
):
    data = service.check_reminders_now()
    return success(data=data)


@router.get("/upcoming")
def upcoming_surgeries(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: SurgeryService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[PaginatedResponse[SurgeryOut]]:
    total, total_pages, rows = service.upcoming(page, page_size)
    return success(
        data=PaginatedResponse(
            items=[SurgeryOut(**dict(r)) for r in rows],
            total=total, page=page, page_size=page_size, total_pages=total_pages,
        )
    )


@router.get("/{surgery_id}")
def get_surgery(
    surgery_id: int,
    service: SurgeryService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[SurgeryOut]:
    row = service.get(surgery_id)
    return success(data=SurgeryOut(**row))


@router.patch("/{surgery_id}")
def update_surgery(
    surgery_id: int,
    body: SurgeryUpdate,
    service: SurgeryService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[SurgeryOut]:
    updated = service.update(surgery_id, body)
    return success(data=SurgeryOut(**updated))


@router.delete("/{surgery_id}")
def delete_surgery(
    surgery_id: int,
    service: SurgeryService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    service.delete(surgery_id)
    return success(message="deleted")
