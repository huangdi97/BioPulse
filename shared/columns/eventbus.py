TABLE_EVENT_BUS_DEFINITIONS_COLS = frozenset(
    {
        "id",
        "event_type",
        "display_name",
        "description",
        "source_end",
        "target_ends",
        "schema_template",
        "priority",
        "enabled",
        "created_at",
    }
)

TABLE_EVENT_BUS_MESSAGES_COLS = frozenset(
    {
        "id",
        "message_id",
        "event_type",
        "source_end",
        "source_entity_type",
        "source_entity_id",
        "payload",
        "correlation_id",
        "priority",
        "status",
        "retry_count",
        "max_retries",
        "created_at",
        "delivered_at",
    }
)

TABLE_EVENT_DELIVERY_LOG_COLS = frozenset(
    {
        "id",
        "message_id",
        "target_end",
        "delivery_status",
        "attempt",
        "response_summary",
        "duration_ms",
        "error_message",
        "created_at",
    }
)
