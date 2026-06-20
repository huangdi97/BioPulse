"""Memory module."""

TABLE_MEMORY_CONSOLIDATION_LOG_COLS = frozenset(
    {
        "id",
        "consolidation_type",
        "source_table",
        "item_count",
        "items_promoted",
        "items_pruned",
        "items_superseded",
        "duration_ms",
        "status",
        "details",
        "created_at",
    }
)

TABLE_MEMORY_ENTRIES_COLS = frozenset(
    {
        "id",
        "title",
        "content",
        "memory_type",
        "source_type",
        "source_id",
        "importance",
        "context_tags",
        "embedding",
        "access_count",
        "last_accessed",
        "is_active",
        "created_by",
        "created_at",
        "updated_at",
    }
)

TABLE_MEMORY_GATES_COLS = frozenset(
    {
        "id",
        "name",
        "source_type",
        "importance_threshold",
        "ttl_days",
        "retention_policy",
        "is_active",
        "created_at",
    }
)

TABLE_MEMORY_RECALL_LOG_COLS = frozenset(
    {
        "id",
        "query_text",
        "memory_ids",
        "result_count",
        "context",
        "created_at",
    }
)

TABLE_MEMORY_UTILITY_SCORES_COLS = frozenset(
    {
        "id",
        "memory_entry_id",
        "utility_score",
        "access_frequency",
        "recency_score",
        "importance_score",
        "connectivity_score",
        "decay_rate",
        "last_utility_update",
        "created_at",
    }
)

TABLE_MEMORY_ASSOCIATIONS_COLS = frozenset(
    {
        "id",
        "memory_id_a",
        "memory_id_b",
        "relation_type",
        "weight",
        "created_at",
    }
)

TABLE_SLEEP_CONSOLIDATION_LOGS_COLS = frozenset(
    {
        "id",
        "consolidation_type",
        "source_entry_ids",
        "target_entry_id",
        "action_detail",
        "utility_before",
        "utility_after",
        "created_at",
    }
)
