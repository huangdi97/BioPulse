"""Training module."""

TABLE_TRAINING_ATTRIBUTIONS_COLS = frozenset(
    {
        "id",
        "user_id",
        "training_session_id",
        "metric_name",
        "metric_before",
        "metric_after",
        "change_pct",
        "attribution_score",
        "confidence",
        "analysis",
        "period_days",
        "created_at",
    }
)

TABLE_TRAINING_MODULES_COLS = frozenset(
    {
        "id",
        "title",
        "category",
        "difficulty",
        "content",
        "prerequisites",
        "passing_score",
        "estimated_minutes",
        "is_active",
        "created_by",
        "created_at",
        "updated_at",
    }
)

TABLE_TRAINING_ROI_ANALYSIS_COLS = frozenset(
    {
        "id",
        "analysis_id",
        "period_start",
        "period_end",
        "training_hours",
        "participants",
        "behavior_change_score",
        "sales_impact",
        "cost_savings",
        "roi",
        "metadata",
        "created_at",
    }
)

TABLE_TRAINING_SCRIPTS_COLS = frozenset(
    {
        "id",
        "script_id",
        "script_name",
        "source_agent_role",
        "source_collaboration_id",
        "description",
        "steps",
        "difficulty",
        "target_roles",
        "score",
        "created_by",
        "created_at",
        "updated_at",
    }
)

TABLE_TRAINING_SESSIONS_COLS = frozenset(
    {
        "id",
        "user_id",
        "module_id",
        "score",
        "passed",
        "time_spent_seconds",
        "answers",
        "feedback",
        "difficulty_used",
        "next_difficulty",
        "completed_at",
        "created_at",
    }
)
