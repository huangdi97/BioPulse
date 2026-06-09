"""Real-time expense compliance service."""

from __future__ import annotations

from copy import deepcopy

from cloud.app.schemas.expense_compliance import (
    Budget,
    BudgetStatus,
    ExpenseCategory,
    ExpenseCheckResult,
    ExpenseItem,
    ExpenseStatus,
)

_DEFAULT_PERIOD = "2026-06"
_BUDGETS: dict[str, dict[ExpenseCategory, Budget]] = {
    "rep-001": {
        ExpenseCategory.MEAL: Budget(
            category=ExpenseCategory.MEAL,
            period=_DEFAULT_PERIOD,
            total_budget=3000,
            used_amount=2300,
            remaining=700,
        ),
        ExpenseCategory.TRANSPORT: Budget(
            category=ExpenseCategory.TRANSPORT,
            period=_DEFAULT_PERIOD,
            total_budget=2000,
            used_amount=900,
            remaining=1100,
        ),
        ExpenseCategory.ACCOMMODATION: Budget(
            category=ExpenseCategory.ACCOMMODATION,
            period=_DEFAULT_PERIOD,
            total_budget=5000,
            used_amount=3500,
            remaining=1500,
        ),
        ExpenseCategory.GIFT: Budget(
            category=ExpenseCategory.GIFT,
            period=_DEFAULT_PERIOD,
            total_budget=500,
            used_amount=450,
            remaining=50,
        ),
        ExpenseCategory.OTHER: Budget(
            category=ExpenseCategory.OTHER,
            period=_DEFAULT_PERIOD,
            total_budget=1000,
            used_amount=200,
            remaining=800,
        ),
    }
}
_CATEGORY_LIMITS = {
    ExpenseCategory.MEAL: 300,
    ExpenseCategory.TRANSPORT: 500,
    ExpenseCategory.ACCOMMODATION: 1200,
    ExpenseCategory.GIFT: 200,
    ExpenseCategory.OTHER: 300,
}
_VISIT_REP = {"visit-001": "rep-001"}


def _normalize_item(expense_item: ExpenseItem) -> ExpenseItem:
    if expense_item.budget_category is None:
        return expense_item.model_copy(update={"budget_category": expense_item.category})
    return expense_item


def _budget_for(rep_id: str, category: ExpenseCategory) -> Budget:
    budgets = _BUDGETS.setdefault(rep_id, deepcopy(_BUDGETS["rep-001"]))
    return budgets[category]


def suggest_alternative(expense_item: ExpenseItem) -> str:
    item = _normalize_item(expense_item)
    if item.category == ExpenseCategory.GIFT:
        return "礼品费用易触发合规风险，建议改为other并补充业务必要性说明。"
    limit = _CATEGORY_LIMITS[item.budget_category or item.category]
    if item.amount > limit:
        return f"建议将金额调整至{limit}以内，或拆分到真实发生的合规预算类型并补充凭证。"
    return "费用类型与金额处于常规范围，保留发票和拜访关联凭证。"


def check_expense(visit_id: str, expense_item: ExpenseItem) -> ExpenseCheckResult:
    item = _normalize_item(expense_item.model_copy(update={"visit_id": visit_id}))
    rep_id = _VISIT_REP.get(visit_id, "rep-001")
    budget = _budget_for(rep_id, item.budget_category or item.category)

    if item.amount > budget.remaining:
        return ExpenseCheckResult(
            item=item,
            status=ExpenseStatus.REJECTED,
            reason=f"{budget.category.value}预算余额不足，剩余{budget.remaining}，本次申请{item.amount}。",
            suggestion=suggest_alternative(item),
        )

    per_item_limit = _CATEGORY_LIMITS[item.budget_category or item.category]
    if item.category == ExpenseCategory.GIFT or item.amount > per_item_limit:
        return ExpenseCheckResult(
            item=item,
            status=ExpenseStatus.FLAGGED,
            reason=f"费用未超预算，但超过{item.category.value}单笔合规阈值{per_item_limit}或属于敏感费用类型。",
            suggestion=suggest_alternative(item),
        )

    budget.used_amount += item.amount
    budget.remaining = max(budget.total_budget - budget.used_amount, 0)
    return ExpenseCheckResult(
        item=item,
        status=ExpenseStatus.APPROVED,
        reason="费用在预算余额和单笔合规阈值内。",
        suggestion=suggest_alternative(item),
    )


def get_budget_status(rep_id: str, period: str = _DEFAULT_PERIOD) -> BudgetStatus:
    budgets = [budget.model_copy(update={"period": period}) for budget in _BUDGETS.setdefault(rep_id, deepcopy(_BUDGETS["rep-001"])).values()]
    return BudgetStatus(rep_id=rep_id, period=period, budgets=budgets)
