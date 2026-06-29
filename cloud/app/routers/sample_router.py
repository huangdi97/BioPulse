from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from starlette import status

from cloud.app.services.operations.sample_service import SampleService
from shared.auth_scope import require_scope
from shared.base import success

router = APIRouter(prefix="/api/v1/samples", tags=["Samples"])


class SampleCreate(BaseModel):
    sku: str
    name: str
    quantity: int
    location: str
    batch: Optional[str] = None
    expiry: Optional[str] = None


class DispenseCreate(BaseModel):
    recipient: str
    quantity: int
    purpose: Optional[str] = None


class ConfirmReceipt(BaseModel):
    recipient: str


@router.post("/create", status_code=status.HTTP_201_CREATED)
def create_sample(
    body: SampleCreate,
    current_user=Depends(require_scope("visit")),
    service: SampleService = Depends(),
):
    return success(data=service.add_inventory(body.sku, body.name, body.quantity, body.location, body.batch, body.expiry))


@router.post("/{batch_id}/dispense", status_code=status.HTTP_201_CREATED)
def dispense_sample(
    batch_id: int,
    body: DispenseCreate,
    current_user=Depends(require_scope("visit")),
    service: SampleService = Depends(),
):
    return success(data=service.record_dispense(batch_id, body.recipient, body.quantity, body.purpose))


@router.post("/{dispense_id}/confirm")
def confirm_dispense(
    dispense_id: int,
    body: ConfirmReceipt,
    current_user=Depends(require_scope("visit")),
    service: SampleService = Depends(),
):
    return success(data=service.confirm_receipt(dispense_id, body.recipient))


@router.get("/inventory")
def get_inventory(
    sku: Optional[str] = Query(None),
    current_user=Depends(require_scope("visit")),
    service: SampleService = Depends(),
):
    return success(data=service.get_inventory(sku=sku))


@router.get("/alerts")
def get_alerts(
    current_user=Depends(require_scope("visit")),
    service: SampleService = Depends(),
):
    return success(data=service.get_alerts())


@router.get("/report")
def get_report(
    current_user=Depends(require_scope("visit")),
    service: SampleService = Depends(),
):
    return success(data=service.get_compliance_report())
