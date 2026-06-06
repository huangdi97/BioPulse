TABLE_COMPLIANCE_RULES_COLS = [
    "id",
    "name",
    "category",
    "keyword",
    "max_value",
    "created_by",
    "created_at",
]

TABLE_COMPLIANCE_AUDIT_RECORDS_COLS = [
    "id",
    "message_type",
    "content",
    "source_id",
    "score",
    "risk_level",
    "passed",
    "violations",
    "ai_analysis",
    "reviewed_by",
    "reviewed_at",
    "created_by",
    "created_at",
]

TABLE_NMPA_COMPLIANCE_LOGS_COLS = [
    "id",
    "log_id",
    "document_type",
    "content_summary",
    "check_result",
    "violations_found",
    "violation_details",
    "human_review_required",
    "human_reviewer",
    "human_reviewed_at",
    "created_by",
    "created_at",
]

TABLE_AUDIT_CHAIN_ENTRIES_COLS = [
    "id",
    "entity_type",
    "entity_id",
    "action",
    "previous_hash",
    "current_hash",
    "payload",
    "metadata",
    "source",
    "created_by",
    "performed_at",
]

TABLE_AUDIT_CHAIN_BLOCKS_COLS = [
    "id",
    "block_hash",
    "prev_block_hash",
    "block_data",
    "block_type",
    "created_by",
    "node_id",
    "timestamp",
]

TABLE_AUDIT_LOGS_COLS = [
    "id",
    "user_id",
    "action",
    "entity_type",
    "entity_id",
    "detail",
    "source_end",
    "ip_address",
    "created_at",
]

TABLE_FED_AUDIT_CONTRIBUTIONS_COLS = [
    "id",
    "contributor_did",
    "contribution_type",
    "payload_hash",
    "payload_summary",
    "weight",
    "verified",
    "verified_by",
    "audit_chain_hash",
    "created_at",
]

TABLE_SENSOR_SESSIONS_COLS = [
    "id",
    "session_id",
    "session_name",
    "event_type",
    "location",
    "start_time",
    "end_time",
    "data_summary",
    "status",
    "created_at",
]

TABLE_BENCHMARK_REPORTS_COLS = [
    "id",
    "report_id",
    "report_name",
    "report_type",
    "data_source",
    "summary",
    "metrics",
    "period",
    "created_at",
]
