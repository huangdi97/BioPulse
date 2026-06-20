"""Coach module."""

TABLE_COACHING_PROMPT_COLS = frozenset(
    {
        "id",
        "trigger_type",
        "trigger_keywords",
        "scenario",
        "prompt_template",
        "priority",
        "category",
        "is_active",
        "created_by",
        "created_at",
        "updated_at",
    }
)

TABLE_COACHING_SESSION_COLS = frozenset(
    {
        "id",
        "schedule_id",
        "hcp_name",
        "current_scenario",
        "status",
        "started_at",
        "ended_at",
        "notes",
        "created_by",
        "created_at",
    }
)

TABLE_COACH_SCENARIO_COLS = frozenset(
    {
        "id",
        "title",
        "role_setting",
        "goal",
        "difficulty",
        "category",
        "content",
        "tips",
        "is_active",
        "created_by",
        "created_at",
        "updated_at",
    }
)

TABLE_COACH_SESSION_COLS = frozenset(
    {
        "id",
        "module_id",
        "trainee_name",
        "score",
        "feedback",
        "strengths",
        "improvements",
        "session_date",
        "created_by",
        "created_at",
        "session_type",
        "scenario_id",
        "dialogue_log",
        "role",
        "compliance_violations",
        "auto_assessment",
        "reflection_report",
    }
)

TABLE_EDUCATION_ASSESSMENT_COLS = frozenset(
    {
        "id",
        "trainee_name",
        "assessment_date",
        "current_level",
        "target_level",
        "strengths",
        "weaknesses",
        "recommended_modules",
        "notes",
        "is_active",
        "created_by",
        "created_at",
        "updated_at",
    }
)

TABLE_TRAINING_MODULE_COLS = frozenset(
    {
        "id",
        "title",
        "description",
        "category",
        "content",
        "difficulty",
        "is_active",
        "created_by",
        "created_at",
        "updated_at",
    }
)
