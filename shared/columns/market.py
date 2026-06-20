"""Market module."""

TABLE_MARKET_INTEL_ITEMS_COLS = frozenset(
    {
        "id",
        "source_id",
        "title",
        "summary",
        "content",
        "url",
        "item_type",
        "relevance_tags",
        "impact_level",
        "status",
        "ai_analysis",
        "collected_at",
        "created_by",
        "created_at",
        "updated_at",
    }
)

TABLE_MARKET_INTEL_SOURCES_COLS = frozenset(
    {
        "id",
        "name",
        "source_type",
        "target_keywords",
        "is_active",
        "created_by",
        "created_at",
        "updated_at",
    }
)
