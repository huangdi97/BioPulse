"""Triangulation anomaly detection engine — check() entry point."""

from __future__ import annotations

import logging
import sqlite3
from typing import Any, Optional

from shared.base import AppException, ErrorCode

from .decision import TriangulationFinding, TriangulationResult
from .patterns import _correlation_keys, _records, _row_to_dict
from .patterns_detection import _detect_channel_stuffing, _detect_fake_distribution, _finding, _region_mismatch
from .patterns_trend import _total, _trend

logger = logging.getLogger(__name__)


class TriangulationEngine:
    """Cross-validation engine for expense, visit, and distribution signals."""

    def __init__(self, db: Optional[sqlite3.Connection] = None, approval_workflow=None):
        """Initialize the triangulation engine.

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
    ) -> TriangulationResult:
        """Check seven triangulation patterns across expense, visit, flow, and area data.

        Args:
            expense_data: Expense signal or records.
            visit_data: Visit signal or records.
            distribution_data: Distribution or flow signal records.
            distribution_area: Authorized area records for channel stuffing detection.
            sellin_data: Sell-in / shipment records for fake distribution detection.
            sellout_data: Sell-out / consumption records for fake distribution detection.

        Returns:
            TriangulationResult containing findings and confidence scoring.
        """
        expense_records, visit_records, distribution_records = self._correlate(expense_data, visit_data, distribution_data)
        findings = self._evaluate_patterns(expense_records, visit_records, distribution_records, distribution_area, sellin_data, sellout_data)
        score = max([finding.score for finding in findings], default=0.0)
        level = self._level(score)
        decision = self._decision(score)
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
        return TriangulationResult(
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
            raise AppException(ErrorCode.VALIDATION_ERROR, f"Unsupported triangulation table: {table}")
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

    def _evaluate_patterns(
        self,
        expenses: list[dict[str, Any]],
        visits: list[dict[str, Any]],
        distributions: list[dict[str, Any]],
        distribution_area: dict[str, Any] | list[dict[str, Any]] | None = None,
        sellin_data: dict[str, Any] | list[dict[str, Any]] | None = None,
        sellout_data: dict[str, Any] | list[dict[str, Any]] | None = None,
    ) -> list[TriangulationFinding]:
        """Evaluate all seven detection patterns.

        Args:
            expenses: Normalized expense records.
            visits: Normalized visit records.
            distributions: Normalized distribution records.
            distribution_area: Authorized area records for channel stuffing detection.
            sellin_data: Sell-in records for fake distribution detection.
            sellout_data: Sell-out records for fake distribution detection.

        Returns:
            List of findings produced by matched patterns.
        """
        findings = []
        for finder in (
            self._expense_waste,
            self._visit_fraud,
            self._channel_stuffing,
            self._management_neglect,
            self._fake_activity,
        ):
            finding = finder(expenses, visits, distributions)
            if finding:
                findings.append(finding)

        channel_result = _detect_channel_stuffing(distributions, _records(distribution_area))
        if channel_result:
            findings.append(
                _finding(
                    "channel_stuffing_batch",
                    "distribution",
                    channel_result["score"],
                    channel_result["detail"],
                    expenses,
                    visits,
                    distributions,
                )
            )

        sellin_records = _records(sellin_data)
        sellout_records = _records(sellout_data)
        fake_dist_result = _detect_fake_distribution(
            sellin_records or distributions,
            sellout_records or distributions,
        )
        if fake_dist_result:
            findings.append(
                _finding(
                    "fake_distribution",
                    "distribution",
                    fake_dist_result["score"],
                    fake_dist_result["detail"],
                    expenses,
                    visits,
                    distributions,
                )
            )

        return findings

    def _expense_waste(
        self, expenses: list[dict[str, Any]], visits: list[dict[str, Any]], distributions: list[dict[str, Any]]
    ) -> Optional[TriangulationFinding]:
        """Detect expense waste where expense rises while visits and flow fall.

        Args:
            expenses: Normalized expense records.
            visits: Normalized visit records.
            distributions: Normalized distribution records.

        Returns:
            Finding when the pattern matches, otherwise None.
        """
        expense, visit, flow = _trend(expenses, "expense"), _trend(visits, "visit"), _trend(distributions, "distribution")
        if expense == "up" and visit == "down" and flow == "down":
            return _finding("expense_waste", "expense", 0.86, "代表费用上升但拜访与流向同步下降。", expenses, visits, distributions)
        if expense == "up" and visit in {"down", "flat"} and flow in {"down", "flat"}:
            return _finding("expense_waste", "expense", 0.72, "代表费用上升但业务活动或流向未同步改善。", expenses, visits, distributions)
        return None

    def _visit_fraud(
        self, expenses: list[dict[str, Any]], visits: list[dict[str, Any]], distributions: list[dict[str, Any]]
    ) -> Optional[TriangulationFinding]:
        """Detect fabricated visits where visit volume rises without flow change.

        Args:
            expenses: Normalized expense records.
            visits: Normalized visit records.
            distributions: Normalized distribution records.

        Returns:
            Finding when the pattern matches, otherwise None.
        """
        visit, flow = _trend(visits, "visit"), _trend(distributions, "distribution")
        if visit == "up" and flow in {"flat", "down"}:
            score = 0.82 if _total(visits, ("visit_count", "count", "visits")) >= 20 else 0.68
            return _finding("visit_fraud", "visit", score, "拜访量上升但流向未同步增长。", expenses, visits, distributions)
        return None

    def _channel_stuffing(
        self, expenses: list[dict[str, Any]], visits: list[dict[str, Any]], distributions: list[dict[str, Any]]
    ) -> Optional[TriangulationFinding]:
        """Detect cross-region or inconsistent distribution flow.

        Args:
            expenses: Normalized expense records.
            visits: Normalized visit records.
            distributions: Normalized distribution records.

        Returns:
            Finding when the pattern matches, otherwise None.
        """
        if _region_mismatch(visits, distributions) or _trend(distributions, "distribution") == "volatile":
            return _finding("channel_stuffing", "distribution", 0.9, "流向与授权区域、拜访区域或正常波动不一致。", expenses, visits, distributions)
        return None

    def _management_neglect(
        self, expenses: list[dict[str, Any]], visits: list[dict[str, Any]], distributions: list[dict[str, Any]]
    ) -> Optional[TriangulationFinding]:
        """Detect management neglect over repeated unresolved red lights.

        Args:
            expenses: Normalized expense records.
            visits: Normalized visit records.
            distributions: Normalized distribution records.

        Returns:
            Finding when the pattern matches, otherwise None.
        """
        records = expenses + visits + distributions
        red_lights = _total(records, ("red_light_count", "red_lights", "unresolved_red_lights"))
        unresolved = _total(records, ("unresolved_red_lights", "unhandled_red_lights"))
        actions = _total(records, ("manager_action_count", "manager_followup_count", "handled_red_lights"))
        if red_lights >= 2 and unresolved >= 1 and actions == 0:
            return _finding("management_neglect", "management", 0.88, "多次红灯未处理且缺少管理动作。", expenses, visits, distributions)
        return None

    def _fake_activity(
        self, expenses: list[dict[str, Any]], visits: list[dict[str, Any]], distributions: list[dict[str, Any]]
    ) -> Optional[TriangulationFinding]:
        """Detect fake activity where expenses and visits rise while sell-out falls.

        Args:
            expenses: Normalized expense records.
            visits: Normalized visit records.
            distributions: Normalized distribution records.

        Returns:
            Finding when the pattern matches, otherwise None.
        """
        expense, visit, flow = _trend(expenses, "expense"), _trend(visits, "visit"), _trend(distributions, "distribution")
        if expense == "up" and visit == "up" and flow == "down":
            return _finding("fake_activity", "activity", 0.94, "费用与拜访量双增但纯销或流向下降。", expenses, visits, distributions)
        return None

    def _level(self, score: float) -> str:
        """Convert confidence score to suspicion level.

        Args:
            score: Confidence score between 0 and 1.

        Returns:
            Suspicion level string.
        """
        if score >= 0.8:
            return "high"
        if score >= 0.5:
            return "medium"
        if score > 0:
            return "low"
        return "none"

    def _decision(self, score: float) -> str:
        """Convert confidence score to a decision.

        Args:
            score: Confidence score between 0 and 1.

        Returns:
            Decision string.
        """
        if score >= 0.8:
            return "trigger_red_light"
        if score >= 0.5:
            return "secondary_investigation"
        if score > 0:
            return "mark_pending_review"
        return "pass"
