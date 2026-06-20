"""Userprofile module."""

TABLE_RECOMMENDATIONS_COLS = frozenset(
    {
        "id",
        "user_id",
        "rec_type",
        "rec_target_id",
        "rec_title",
        "rec_reason",
        "score",
        "strategy_name",
        "clicked",
        "dismissed",
        "created_at",
    }
)

TABLE_USER_BEHAVIORS_COLS = frozenset(
    {
        "id",
        "user_id",
        "action_type",
        "target_type",
        "target_id",
        "metadata",
        "session_id",
        "duration_seconds",
        "created_at",
    }
)

TABLE_USER_PROFILES_COLS = frozenset(
    {
        "id",
        "user_id",
        "persona_type",
        "specialization",
        "experience_level",
        "preferred_content_types",
        "custom_tags",
        "embedding",
        "updated_at",
        "created_at",
    }
)
