"""Audit module."""

TABLE_AUDIT_CHAIN_ENTRIES_COLS = frozenset(
    {
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
    }
)

TABLE_AUDIT_LOGS_COLS = frozenset(
    {
        "id",
        "user_id",
        "action",
        "entity_type",
        "entity_id",
        "detail",
        "source_end",
        "ip_address",
        "created_at",
    }
)

TABLE_COMPLIANCE_AUDIT_RECORDS_COLS = frozenset(
    {
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
    }
)

TABLE_AUDIT_CHAIN_BLOCKS_COLS = frozenset(
    {
        "id",
        "block_hash",
        "prev_block_hash",
        "block_data",
        "block_type",
        "created_by",
        "node_id",
        "timestamp",
    }
)

TABLE_TRAINING_CORRECTIONS_COLS = frozenset(
    {
        "id",
        "audit_record_id",
        "title",
        "description",
        "category",
        "severity",
        "status",
        "assigned_to",
        "created_by",
        "created_at",
        "updated_at",
    }
)
