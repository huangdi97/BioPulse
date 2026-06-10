from pydantic import BaseModel
from typing import Optional


class QuotationSubmit(BaseModel):
    product: str
    amount: float
    limit_amount: float = 0.0
    rep_id: int


class ApprovalResult(BaseModel):
    quotation_id: str
    status: str
    message: str
    review_notes: Optional[str] = None


class ReviewRequest(BaseModel):
    action: str
    notes: str = ""
