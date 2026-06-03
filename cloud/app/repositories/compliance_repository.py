from cloud.shared.columns import (
    TABLE_COMPLIANCE_AUDIT_RECORDS_COLS,
    TABLE_COMPLIANCE_RULES_COLS,
    TABLE_DATA_MASKING_RULES_COLS,
    TABLE_DID_REGISTRY_COLS,
    TABLE_NMPA_COMPLIANCE_LOGS_COLS,
)
from cloud.shared.repository import BaseRepository


class ComplianceRulesRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "compliance_rules", TABLE_COMPLIANCE_RULES_COLS)


class ComplianceAuditRecordsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "compliance_audit_records", TABLE_COMPLIANCE_AUDIT_RECORDS_COLS)


class NmpaComplianceLogsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "nmpa_compliance_logs", TABLE_NMPA_COMPLIANCE_LOGS_COLS)

    def list_filtered(self, document_type=None, check_result=None, human_review_required=None):
        conditions, params = [], []
        if document_type:
            conditions.append("document_type=?")
            params.append(document_type)
        if check_result:
            conditions.append("check_result=?")
            params.append(check_result)
        if human_review_required is not None:
            conditions.append("human_review_required=?")
            params.append(human_review_required)
        return self.list_all(
            conditions=conditions or None,
            params=params or None,
            order_by="created_at DESC",
        )


class DataMaskingRulesRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "data_masking_rules", TABLE_DATA_MASKING_RULES_COLS)


class DidRegistryRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "did_registry", TABLE_DID_REGISTRY_COLS)

    def get_by_did(self, did: str):
        row = self.db.execute(f"SELECT {', '.join(self.cols)} FROM {self.table_name} WHERE did=?", (did,)).fetchone()
        return dict(row) if row else None

    def count_by_status(self):
        rows = self.db.execute(f"SELECT status, COUNT(*) as cnt FROM {self.table_name} GROUP BY status").fetchall()
        return {r["status"]: r["cnt"] for r in rows}

    def count_by_entity_type(self):
        rows = self.db.execute(f"SELECT entity_type, COUNT(*) as cnt FROM {self.table_name} GROUP BY entity_type").fetchall()
        return {r["entity_type"]: r["cnt"] for r in rows}
