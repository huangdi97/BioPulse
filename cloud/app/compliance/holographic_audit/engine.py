"""Holographic audit anomaly detection engine — check() entry point."""

from __future__ import annotations

import logging
import sqlite3
from typing import Any, Optional

from shared.base import AppException, ErrorCode

from .decision import HolographicResult
from .engine_decision import _decision, _level
from .patterns import _correlation_keys, _records, _row_to_dict

logger = logging.getLogger(__name__)


class HolographicAuditEngine:
    """Cross-validation engine for expense, visit, and distribution signals."""

    def __init__(self, db: Optional[sqlite3.Connection] = None, approval_workflow=None):
        """Initialize the holographic audit engine.

        Args:
            db: Optional SQLite connection used to fetch correlated records.
            approval_workflow: Optional ApprovalWorkflow for HITL approval on red light decisions.

        Returns:
            None.
        """
        self.db = db
        self._approval_workflow = approval_workflow

    def check(
        self,
        expense_data: dict[str, Any] | list[dict[str, Any]] | None,
        visit_data: dict[str, Any] | list[dict[str, Any]] | None,
        distribution_data: dict[str, Any] | list[dict[str, Any]] | None,
        distribution_area: dict[str, Any] | list[dict[str, Any]] | None = None,
        sellin_data: dict[str, Any] | list[dict[str, Any]] | None = None,
        sellout_data: dict[str, Any] | list[dict[str, Any]] | None = None,
    ) -> HolographicResult:
        """Check seven holographic patterns across expense, visit, flow, and area data.

        Args:
            expense_data: Expense signal or records.
            visit_data: Visit signal or records.
            distribution_data: Distribution or flow signal records.
            distribution_area: Authorized area records for channel stuffing detection.
            sellin_data: Sell-in / shipment records for fake distribution detection.
            sellout_data: Sell-out / consumption records for fake distribution detection.

        Returns:
            HolographicResult containing findings and confidence scoring.
        """
        expense_records, visit_records, distribution_records = self._correlate(expense_data, visit_data, distribution_data)
        from .engine_detectors import _evaluate_patterns

        findings = _evaluate_patterns(expense_records, visit_records, distribution_records, distribution_area, sellin_data, sellout_data)
        score = max([finding.score for finding in findings], default=0.0)
        level = _level(score)
        decision = _decision(score)
        approval_request_id = None
        if decision == "trigger_red_light" and self._approval_workflow:
            approval_request_id = self._approval_workflow.request_approval(
                event_type="compliance.red_light.triggered",
                agent_name="compliance_monitor",
                detail={
                    "score": score,
                    "level": level,
                    "findings": [f.to_dict() if hasattr(f, "to_dict") else str(f) for f in findings],
                },
            )
            logger.info("Red light approval requested: %s", approval_request_id)
        return HolographicResult(
            passed=not findings,
            confidence_score=round(score, 4),
            suspicion_level=level,
            decision=decision,
            findings=findings,
            correlated_records={"expenses": expense_records, "visits": visit_records, "distributions": distribution_records},
            recommended_action=decision,
            metadata={"approval_request_id": approval_request_id} if approval_request_id else None,
        )

    def _correlate(
        self,
        expense_data: dict[str, Any] | list[dict[str, Any]] | None,
        visit_data: dict[str, Any] | list[dict[str, Any]] | None,
        distribution_data: dict[str, Any] | list[dict[str, Any]] | None,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
        """Normalize and fetch correlated records when a dimension is missing.

        Args:
            expense_data: Expense input data.
            visit_data: Visit input data.
            distribution_data: Distribution input data.

        Returns:
            Tuple of expense, visit, and distribution record lists.
        """
        expenses = _records(expense_data)
        visits = _records(visit_data)
        distributions = _records(distribution_data)
        keys = _correlation_keys(expenses + visits + distributions)
        if self.db and keys:
            visits = visits or self._fetch_related("visits", keys)
            expenses = expenses or self._fetch_related("expenses", keys)
            distributions = distributions or self._fetch_related("distributions", keys)
        return expenses, visits, distributions

    def _fetch_related(self, table: str, keys: dict[str, Any]) -> list[dict[str, Any]]:
        """Fetch related records from a whitelisted table.

        Args:
            table: Whitelisted table name to query.
            keys: Correlation key values.

        Returns:
            List of related rows converted to dictionaries.
        """
        allowed = {
            "visits": {"visit_id", "rep_id", "hcp_id", "product_id", "region_id"},
            "expenses": {"visit_id", "rep_id", "hcp_id", "product_id", "region_id"},
            "distributions": {"visit_id", "rep_id", "hcp_id", "product_id", "region_id", "distributor_id"},
        }
        if table not in allowed:
            raise AppException(ErrorCode.VALIDATION_ERROR, f"Unsupported holographic_audit table: {table}")
        filters = [(key, value) for key, value in keys.items() if key in allowed[table] and value not in (None, "")]
        if not filters:
            return []
        where = " OR ".join(f"{key} = ?" for key, _ in filters)
        values = tuple(value for _, value in filters)
        try:
            rows = self.db.execute(f"SELECT * FROM {table} WHERE {where} LIMIT 100", values).fetchall()
        except sqlite3.Error:
            return []
        return [_row_to_dict(row) for row in rows]
