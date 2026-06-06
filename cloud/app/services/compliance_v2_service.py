"""合规 V2 门面服务，统一暴露评估器的扫描与报告器的审计/纠偏接口。"""

from typing import Optional

from fastapi import Depends, Request

from cloud.app.database import get_db
from cloud.app.services.base import BaseService
from cloud.app.services.compliance_v2_evaluator import RuleEvaluator
from cloud.app.services.compliance_v2_report import ReportGenerator


class ComplianceV2Service(BaseService):
    """ComplianceV2 服务类。"""

    def __init__(self, db=Depends(get_db)):
        super().__init__(db)
        self._evaluator = RuleEvaluator(self.db)
        self._reporter = ReportGenerator(self.db)

    def scan(self, body, request: Request, uid: int) -> dict:
        return self._evaluator.scan(body, request, uid)

    def list_records(
        self,
        message_type: Optional[str],
        risk_level: Optional[str],
        passed: Optional[int],
        date_from: Optional[str],
        date_to: Optional[str],
        page: int,
        page_size: int,
    ) -> dict:
        return self._evaluator.list_records(message_type, risk_level, passed, date_from, date_to, page, page_size)

    def get_record(self, record_id: int) -> dict:
        return self._evaluator.get_record(record_id)

    def review_record(self, record_id: int, body, uid: int) -> dict:
        return self._reporter.review_record(record_id, body, uid)

    def create_audit_chain(self, body, uid: int) -> dict:
        return self._reporter.create_audit_chain(body, uid)

    def get_audit_chain(self, entity_type: str, entity_id: str) -> dict:
        return self._reporter.get_audit_chain(entity_type, entity_id)

    def verify_audit_chain(self, entity_type: str, entity_id: str) -> dict:
        return self._reporter.verify_audit_chain(entity_type, entity_id)

    def train_correction(self, record_id: int, request: Request, uid: int) -> dict:
        return self._reporter.train_correction(record_id, request, uid)

    def list_corrections(
        self,
        category: Optional[str],
        severity: Optional[str],
        status: Optional[str],
        page: int,
        page_size: int,
    ) -> dict:
        return self._reporter.list_corrections(category, severity, status, page, page_size)

    def update_correction(self, correction_id: int, body) -> dict:
        return self._reporter.update_correction(correction_id, body)

    def list_l2_rules(self) -> dict:
        return self._evaluator.list_l2_rules()

    def evaluate_visit(self, body) -> dict:
        return self._evaluator.evaluate_visit(body)

    def dashboard(self) -> dict:
        return self._reporter.dashboard()
