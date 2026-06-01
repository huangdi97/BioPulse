from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from starlette import status

from shared.auth_scope import require_scope
from shared.base import success
from cloud.app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


class TemplateCreate(BaseModel):
    name: str
    title_template: str
    body_template: str
    category: str


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    title_template: Optional[str] = None
    body_template: Optional[str] = None
    category: Optional[str] = None


class NotificationSend(BaseModel):
    user_id: int
    template_name: Optional[str] = None
    title: Optional[str] = None
    body: Optional[str] = None
    category: Optional[str] = None
    context: Optional[dict] = None
    ref_type: Optional[str] = None
    ref_id: Optional[int] = None


@router.post("/templates", status_code=status.HTTP_201_CREATED)
def create_template(
    body: TemplateCreate,
    current_user: dict = Depends(require_scope("visit")),
    service: NotificationService = Depends(),
) -> Any:
    result = service.create_template(
        name=body.name,
        title_template=body.title_template,
        body_template=body.body_template,
        category=body.category,
    )
    return success(data=result)


@router.get("/templates")
def list_templates(
    current_user: dict = Depends(require_scope("visit")),
    service: NotificationService = Depends(),
) -> Any:
    return success(data=service.list_templates())


@router.get("/templates/{template_id}")
def get_template(
    template_id: int,
    current_user: dict = Depends(require_scope("visit")),
    service: NotificationService = Depends(),
) -> Any:
    return success(data=service.get_template(template_id))


@router.patch("/templates/{template_id}")
def update_template(
    template_id: int,
    body: TemplateUpdate,
    current_user: dict = Depends(require_scope("visit")),
    service: NotificationService = Depends(),
) -> Any:
    updates = {}
    for field in ("name", "title_template", "body_template", "category"):
        val = getattr(body, field, None)
        if val is not None:
            updates[field] = val
    result = service.update_template(template_id, **updates)
    return success(data=result)


@router.delete("/templates/{template_id}")
def delete_template(
    template_id: int,
    current_user: dict = Depends(require_scope("visit")),
    service: NotificationService = Depends(),
) -> Any:
    service.delete_template(template_id)
    return success()


@router.post("/send", status_code=status.HTTP_201_CREATED)
def send_notification(
    body: NotificationSend,
    current_user: dict = Depends(require_scope("visit")),
    service: NotificationService = Depends(),
) -> Any:
    result = service.send(
        user_id=body.user_id,
        template_name=body.template_name,
        title=body.title,
        body=body.body,
        category=body.category,
        context=body.context,
        ref_type=body.ref_type,
        ref_id=body.ref_id,
    )
    return success(data=result)


@router.get("/")
def list_notifications(
    is_read: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(require_scope("visit")),
    service: NotificationService = Depends(),
) -> Any:
    user_id = int(current_user["sub"])
    result = service.list_notifications(
        user_id=user_id, is_read=is_read, page=page, page_size=page_size
    )
    return success(data=result)


@router.patch("/{notification_id}/read")
def mark_read(
    notification_id: int,
    current_user: dict = Depends(require_scope("visit")),
    service: NotificationService = Depends(),
) -> Any:
    user_id = int(current_user["sub"])
    result = service.mark_read(notification_id, user_id)
    return success(data=result)


@router.get("/unread-count")
def unread_count(
    current_user: dict = Depends(require_scope("visit")),
    service: NotificationService = Depends(),
) -> Any:
    user_id = int(current_user["sub"])
    return success(data=service.unread_count(user_id))
