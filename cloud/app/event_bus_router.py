import json
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from starlette import status

from cloud.app.services.event_bus_service import EventBusService
from shared.auth_scope import require_scope
from shared.base import success

router = APIRouter(prefix="/events", tags=["Event Bus"])

ALL_ENDS = ["cloud", "sales-coach", "sales-assistant", "assistant", "opportunity"]


class EventDefCreate(BaseModel):
    event_type: str
    display_name: str = ""
    description: str = ""
    source_end: str = "cloud"
    target_ends: list[str] = []
    schema_template: dict = {}
    priority: int = 100


class EventPublish(BaseModel):
    event_type: str
    source_entity_type: str = ""
    source_entity_id: str = ""
    payload: dict = {}
    correlation_id: str = ""


class EventSubscribe(BaseModel):
    event_types: list[str] = []
    target_end: str
    callback_url: str = ""


@router.post("/definitions/create")
def definitions_create(body: EventDefCreate,
                       current_user: dict = Depends(require_scope("visit")),
                       service: EventBusService = Depends()):
    result = service.create_definition(
        event_type=body.event_type, display_name=body.display_name,
        description=body.description, source_end=body.source_end,
        target_ends=body.target_ends, schema_template=body.schema_template,
        priority=body.priority,
    )
    return success(data=result)


@router.get("/definitions/list")
def definitions_list(source_end: Optional[str] = Query(None),
                     enabled: Optional[int] = Query(None),
                     current_user: dict = Depends(require_scope("visit")),
                     service: EventBusService = Depends()):
    rows = service.list_definitions(source_end=source_end, enabled=enabled)
    return success(data=rows)


@router.patch("/definitions/{event_type}/toggle")
def definitions_toggle(event_type: str,
                       current_user: dict = Depends(require_scope("visit")),
                       service: EventBusService = Depends()):
    result = service.toggle_definition(event_type)
    return success(data=result)


@router.post("/messages/publish")
def messages_publish(body: EventPublish,
                     current_user: dict = Depends(require_scope("visit")),
                     service: EventBusService = Depends()):
    result = service.publish_message(
        event_type=body.event_type, source_entity_type=body.source_entity_type,
        source_entity_id=body.source_entity_id, payload=body.payload,
        correlation_id=body.correlation_id,
    )
    return success(data=result)


@router.get("/messages/list")
def messages_list(event_type: Optional[str] = Query(None),
                  status: Optional[str] = Query(None),
                  source_end: Optional[str] = Query(None),
                  start_date: Optional[str] = Query(None),
                  end_date: Optional[str] = Query(None),
                  current_user: dict = Depends(require_scope("visit")),
                  service: EventBusService = Depends()):
    rows = service.list_messages(event_type=event_type, status=status,
                                  source_end=source_end, start_date=start_date,
                                  end_date=end_date)
    return success(data=rows)


@router.get("/messages/{message_id}")
def messages_get(message_id: str,
                 current_user: dict = Depends(require_scope("visit")),
                 service: EventBusService = Depends()):
    result = service.get_message(message_id)
    return success(data=result)


@router.post("/messages/{message_id}/redeliver")
def messages_redeliver(message_id: str,
                       current_user: dict = Depends(require_scope("visit")),
                       service: EventBusService = Depends()):
    result = service.redeliver_message(message_id)
    return success(data=result)


@router.post("/subscribe")
def subscribe(body: EventSubscribe,
              current_user: dict = Depends(require_scope("visit")),
              service: EventBusService = Depends()):
    result = service.subscribe(target_end=body.target_end,
                                event_types=body.event_types,
                                callback_url=body.callback_url)
    return success(data=result)


@router.get("/delivery/log")
def delivery_log_list(message_id: Optional[str] = Query(None),
                      target_end: Optional[str] = Query(None),
                      delivery_status: Optional[str] = Query(None),
                      current_user: dict = Depends(require_scope("visit")),
                      service: EventBusService = Depends()):
    rows = service.list_delivery_log(message_id=message_id,
                                      target_end=target_end,
                                      delivery_status=delivery_status)
    return success(data=rows)


@router.get("/dashboard")
def dashboard(current_user: dict = Depends(require_scope("visit")),
              service: EventBusService = Depends()):
    result = service.get_dashboard()
    return success(data=result)
