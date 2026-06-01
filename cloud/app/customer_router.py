import json
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from starlette import status

from cloud.app.services.customer_service import CustomerService
from shared.auth_scope import require_scope
from shared.base import success

router = APIRouter(prefix="/customers", tags=["customers"])


class CustomerCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    title: str = ""
    hospital: str = ""
    department: str = ""
    specialty: str = ""
    phone: str = Field("", max_length=20)
    email: str = Field("", max_length=100)
    tags: List[str] = []


class CustomerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    title: Optional[str] = None
    hospital: Optional[str] = None
    department: Optional[str] = None
    specialty: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = None
    status: Optional[str] = None


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_customer(
    body: CustomerCreate,
    current_user: dict = Depends(require_scope("visit")),
    service: CustomerService = Depends(),
) -> Any:
    user_id = int(current_user["sub"])
    row = service.create_customer(
        name=body.name, title=body.title, hospital=body.hospital,
        department=body.department, specialty=body.specialty,
        phone=body.phone, email=body.email, tags=body.tags,
        user_id=user_id,
    )
    return success(data=row)


@router.get("/")
def list_customers(
    name: str = Query(None),
    hospital: str = Query(None),
    department: str = Query(None),
    status: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(require_scope("visit")),
    service: CustomerService = Depends(),
) -> Any:
    result = service.list_customers(
        name=name, hospital=hospital, department=department,
        status=status, page=page, page_size=page_size,
    )
    return success(data=result)


@router.get("/{customer_id}")
def get_customer(
    customer_id: int,
    current_user: dict = Depends(require_scope("visit")),
    service: CustomerService = Depends(),
) -> Any:
    row = service.get_customer(customer_id)
    return success(data=row)


@router.patch("/{customer_id}")
def update_customer(
    customer_id: int,
    body: CustomerUpdate,
    current_user: dict = Depends(require_scope("visit")),
    service: CustomerService = Depends(),
) -> Any:
    row = service.update_customer(
        customer_id=customer_id, name=body.name, title=body.title,
        hospital=body.hospital, department=body.department,
        specialty=body.specialty, phone=body.phone, email=body.email,
        tags=body.tags, status=body.status,
    )
    return success(data=row)


@router.delete("/{customer_id}")
def delete_customer(
    customer_id: int,
    current_user: dict = Depends(require_scope("visit")),
    service: CustomerService = Depends(),
) -> Any:
    service.delete_customer(customer_id)
    return success()
