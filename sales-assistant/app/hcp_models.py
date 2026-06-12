from typing import Optional

from pydantic import BaseModel, Field


class HcpCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    hospital: Optional[str] = None
    department: Optional[str] = None
    specialty: Optional[str] = None
    tier: Optional[str] = "C"
    city: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    wechat: Optional[str] = None


class HcpUpdate(BaseModel):
    name: Optional[str] = None
    hospital: Optional[str] = None
    department: Optional[str] = None
    specialty: Optional[str] = None
    tier: Optional[str] = None
    city: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    wechat: Optional[str] = None


class HcpOut(BaseModel):
    id: int
    name: str
    hospital: Optional[str] = None
    department: Optional[str] = None
    specialty: Optional[str] = None
    tier: Optional[str] = None
    city: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    wechat: Optional[str] = None
    is_active: int
    created_by: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    category: Optional[str] = None
    specification: Optional[str] = None
    company: Optional[str] = Field(None, max_length=100)


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    specification: Optional[str] = None
    company: Optional[str] = None


class ProductOut(BaseModel):
    id: int
    name: str
    category: Optional[str] = None
    specification: Optional[str] = None
    company: Optional[str] = None
    is_active: int
    created_by: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class RelationCreate(BaseModel):
    product_id: int
    relation_type: str
    strength: Optional[int] = 3
    notes: Optional[str] = None


class RelationOut(BaseModel):
    id: int
    hcp_id: int
    product_id: int
    relation_type: str
    strength: Optional[int] = None
    notes: Optional[str] = None
    is_active: int
    product_name: Optional[str] = None
