TABLE_AGENT_MARKETPLACE_COLS = frozenset(
    {
        "id",
        "item_id",
        "item_name",
        "item_type",
        "description",
        "agent_config",
        "category",
        "price_model",
        "rating",
        "download_count",
        "enabled",
        "publisher",
        "created_at",
        "updated_at",
    }
)

TABLE_ANOMALY_ALERT_COLS = frozenset(
    {
        "id",
        "rule_id",
        "entity_type",
        "entity_id",
        "detected_value",
        "severity",
        "message",
        "status",
        "detected_at",
        "resolved_at",
        "resolved_by",
        "created_at",
    }
)

TABLE_ANOMALY_RULE_COLS = frozenset(
    {
        "id",
        "rule_name",
        "metric",
        "operator",
        "threshold",
        "severity",
        "description",
        "is_active",
        "created_by",
        "created_at",
        "updated_at",
    }
)

TABLE_BENCHMARK_REPORTS_COLS = frozenset(
    {
        "id",
        "report_id",
        "report_name",
        "report_type",
        "data_source",
        "summary",
        "metrics",
        "period",
        "created_at",
    }
)

TABLE_EFFECT_METRICS_COLS = frozenset(
    {
        "id",
        "metric_id",
        "agent_role",
        "metric_type",
        "metric_value",
        "metric_unit",
        "source_table",
        "source_row_id",
        "period_start",
        "period_end",
        "created_at",
    }
)

TABLE_SENSOR_SESSIONS_COLS = frozenset(
    {
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
    }
)

TABLE_SUPPLY_CHAIN_ITEMS_COLS = frozenset(
    {
        "id",
        "item_id",
        "item_name",
        "sku",
        "category",
        "current_stock",
        "min_stock",
        "max_stock",
        "unit_price",
        "supplier",
        "status",
        "created_at",
        "updated_at",
    }
)
