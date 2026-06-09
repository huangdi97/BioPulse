"""Expense compliance schemas."""

from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class ExpenseCategory(str, Enum):
    MEAL = "meal"
    TRANSPORT = "transport"
    ACCOMMODATION = "accommodation"
    GIFT = "gift"
    OTHER = "other"


class ExpenseStatus(str, Enum):
    APPROVED = "approved"
    FLAGGED = "flagged"
    REJECTED = "rejected"


class ExpenseItem(BaseModel):
    id: str = Field(default_factory=lambda: f"exp-{uuid4().hex[:10]}")
    visit_id: str
    category: ExpenseCategory
    amount: float = Field(..., ge=0)
    budget_category: ExpenseCategory | None = None


class Budget(BaseModel):
    category: ExpenseCategory
    period: str
    total_budget: float
    used_amount: float
    remaining: float


class ExpenseCheckResult(BaseModel):
    item: ExpenseItem
    status: ExpenseStatus
    reason: str
    suggestion: str


class BudgetStatus(BaseModel):
    rep_id: str
    period: str
    budgets: list[Budget]
