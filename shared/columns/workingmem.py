"""Workingmem module."""

TABLE_EPISODIC_MEMORY_COLS = frozenset(
    {
        "id",
        "event_type",
        "title",
        "description",
        "context",
        "outcome",
        "valence",
        "intensity",
        "involved_agents",
        "related_entity_type",
        "related_entity_id",
        "is_consolidated",
        "created_by",
        "created_at",
    }
)

TABLE_WORKING_MEMORY_COLS = frozenset(
    {
        "id",
        "session_id",
        "slot_key",
        "slot_value",
        "slot_type",
        "ttl_seconds",
        "created_at",
        "expires_at",
    }
)
