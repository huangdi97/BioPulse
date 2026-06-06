TABLE_ROUTE_LOGS_COLS = frozenset(
    {
        "id",
        "input_text",
        "matched_rule_id",
        "matched_rule_name",
        "assigned_role_id",
        "assigned_role_name",
        "confidence",
        "response_summary",
        "tokens_used",
        "latency_ms",
        "source",
        "created_by",
        "created_at",
    }
)

TABLE_ROUTE_RULES_COLS = frozenset(
    {
        "id",
        "name",
        "priority",
        "condition_field",
        "condition_operator",
        "condition_value",
        "target_role_id",
        "fallback_role_id",
        "max_tokens",
        "temperature",
        "is_active",
        "created_by",
        "created_at",
        "updated_at",
    }
)

TABLE_ROUTE_STATS_COLS = frozenset(
    {
        "id",
        "role_id",
        "total_routed",
        "avg_confidence",
        "avg_tokens",
        "avg_latency_ms",
        "last_routed_at",
        "updated_at",
    }
)
