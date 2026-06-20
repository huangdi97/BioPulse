"""Privacy module."""

TABLE_FEDERATED_NODES_COLS = frozenset(
    {
        "id",
        "node_id",
        "node_name",
        "node_type",
        "organization",
        "status",
        "endpoint_url",
        "public_key",
        "data_summary",
        "last_heartbeat",
        "round_count",
        "total_samples",
        "reliability_score",
        "is_active",
        "registered_at",
        "updated_at",
    }
)

TABLE_FEDERATED_ROUNDS_COLS = frozenset(
    {
        "id",
        "round_id",
        "model_name",
        "round_number",
        "participant_count",
        "aggregation_method",
        "global_metrics",
        "status",
        "created_at",
        "completed_at",
    }
)

TABLE_NMPA_COMPLIANCE_LOGS_COLS = frozenset(
    {
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
    }
)

TABLE_PRIVACY_COMPUTE_JOBS_COLS = frozenset(
    {
        "id",
        "job_id",
        "compute_type",
        "sensitivity_level",
        "data_summary",
        "selected_scheme",
        "status",
        "epsilon_used",
        "noise_level",
        "result_summary",
        "created_by",
        "created_at",
        "completed_at",
    }
)
