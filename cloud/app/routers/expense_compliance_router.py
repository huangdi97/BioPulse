"""Expense compliance APIs."""

from fastapi import APIRouter, Query

from cloud.app.schemas.expense_compliance import BudgetStatus, ExpenseCheckResult, ExpenseItem
from cloud.app.services.expense_compliance_service import (
    check_expense,
    get_budget_status,
    suggest_alternative,
)

router = APIRouter(prefix="/api/expense", tags=["费用合规"])


@router.post("/check", response_model=ExpenseCheckResult, tags=["费用合规"])
def expense_check(body: ExpenseItem) -> ExpenseCheckResult:
    return check_expense(body.visit_id, body)


@router.get("/budget/{rep_id}", response_model=BudgetStatus, tags=["费用合规"])
def expense_budget(rep_id: str, period: str = Query("2026-06")) -> BudgetStatus:
    return get_budget_status(rep_id, period)


@router.post("/suggest", response_model=str, tags=["费用合规"])
def expense_suggest(body: ExpenseItem) -> str:
    return suggest_alternative(body)
