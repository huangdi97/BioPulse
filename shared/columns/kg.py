"""Kg module."""

TABLE_KG_ENTITIES_COLS = frozenset(
    {
        "id",
        "entity_id",
        "entity_type",
        "name",
        "aliases",
        "properties",
        "source_table",
        "source_row_id",
        "status",
        "confidence",
        "created_by",
        "created_at",
        "updated_at",
    }
)

TABLE_KG_RELATIONS_COLS = frozenset(
    {
        "id",
        "source_entity_id",
        "target_entity_id",
        "relation_type",
        "weight",
        "properties",
        "direction",
        "confidence",
        "source",
        "created_at",
    }
)

TABLE_KG_SEARCH_CACHE_COLS = frozenset(
    {
        "id",
        "query_hash",
        "query_text",
        "result_summary",
        "result_count",
        "cache_ttl",
        "created_at",
    }
)
