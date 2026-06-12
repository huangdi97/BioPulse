"""Compliance rule CRUD, evaluation, and audit orchestration service."""

from __future__ import annotations

from typing import Any, Optional

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import ComplianceRulesRepository
from shared.base_service import BaseService

from .audit_log_service import ComplianceAuditLogService
from .evaluation_service import ComplianceEvaluationService


class ComplianceService(BaseService):
    """Compliance management service providing a unified API over rule CRUD, evaluation, and audit."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._evaluation = ComplianceEvaluationService(*args, **kwargs)
        self._audit_log = ComplianceAuditLogService(*args, **kwargs)

    def _connection(self):
        if hasattr(self, "db") and self.db is not None:
            return self.db
        from cloud.app.database import DB_PATH

        self.db = self._connect(DB_PATH)
        return self.db

    def create_rule(self, name: str, category: str, keyword: str, max_value: Optional[float], created_by: int) -> dict[str, Any]:
        repo = ComplianceRulesRepository(self.db)
        row_id = repo.create({"name": name, "category": category, "keyword": keyword, "max_value": max_value, "created_by": created_by})
        return {"id": row_id, "name": name, "category": category, "keyword": keyword, "max_value": max_value}

    def list_rules(self) -> list[dict[str, Any]]:
        repo = ComplianceRulesRepository(self.db)
        return [
            {"id": r["id"], "name": r["name"], "category": r["category"], "keyword": r["keyword"], "max_value": r["max_value"]}
            for r in repo.list_all()
        ]

    def update_rule(
        self,
        rule_id: int,
        name: Optional[str] = None,
        category: Optional[str] = None,
        keyword: Optional[str] = None,
        max_value: Optional[float] = None,
    ) -> dict[str, Any]:
        repo = ComplianceRulesRepository(self.db)
        row = repo.get_by_id(rule_id)
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Rule not found")
        data: dict[str, Any] = {}
        if name is not None:
            data["name"] = name
        if category is not None:
            data["category"] = category
        if keyword is not None:
            data["keyword"] = keyword
        if max_value is not None:
            data["max_value"] = max_value
        if data:
            repo.update(rule_id, data)
        return {
            "id": rule_id,
            "name": data.get("name", row["name"]),
            "category": data.get("category", row["category"]),
            "keyword": data.get("keyword", row["keyword"]),
            "max_value": data.get("max_value", row["max_value"]),
        }

    def delete_rule(self, rule_id: int) -> None:
        repo = ComplianceRulesRepository(self.db)
        row = repo.get_by_id(rule_id)
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Rule not found")
        repo.delete(rule_id)

    def dashboard_summary(self) -> dict[str, Any]:
        return self._evaluation.dashboard_summary()

    def dashboard(self) -> dict[str, Any]:
        return self._evaluation.dashboard()

    def rep_violations(self, rep_id: int) -> dict[str, Any]:
        return self._audit_log.rep_violations(rep_id)
