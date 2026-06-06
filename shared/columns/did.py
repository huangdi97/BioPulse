TABLE_DATA_MASKING_RULES_COLS = frozenset(
    {
        "id",
        "rule_name",
        "field_pattern",
        "masking_type",
        "masking_config",
        "applies_to",
        "enabled",
        "created_by",
        "created_at",
        "updated_at",
    }
)

TABLE_DID_REGISTRY_COLS = frozenset(
    {
        "id",
        "did",
        "entity_type",
        "entity_id",
        "public_key",
        "status",
        "metadata",
        "created_by",
        "created_at",
        "updated_at",
    }
)

TABLE_DP_AUDIT_LOG_COLS = frozenset(
    {
        "id",
        "did",
        "operation_type",
        "epsilon_consumed",
        "data_category",
        "row_count",
        "noise_level",
        "approved",
        "details",
        "created_at",
    }
)

TABLE_FED_AUDIT_CONTRIBUTIONS_COLS = frozenset(
    {
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
    }
)

TABLE_PRIVACY_BUDGETS_COLS = frozenset(
    {
        "id",
        "did",
        "epsilon_total",
        "epsilon_spent",
        "epsilon_remaining",
        "query_count",
        "last_query_at",
        "reset_at",
        "created_at",
    }
)

TABLE_VC_CREDENTIALS_COLS = frozenset(
    {
        "id",
        "vc_id",
        "issuer_did",
        "subject_did",
        "credential_type",
        "claims",
        "issuance_date",
        "expiration_date",
        "proof",
        "status",
        "revoked_at",
        "created_at",
    }
)
