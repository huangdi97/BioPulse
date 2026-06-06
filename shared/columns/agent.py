TABLE_AGENT_PIPELINES_COLS = frozenset(
    {
        "id",
        "name",
        "description",
        "is_active",
        "created_by",
        "created_at",
        "updated_at",
    }
)

TABLE_AGENT_ROLES_COLS = frozenset(
    {
        "id",
        "name",
        "role_type",
        "description",
        "system_prompt",
        "input_schema",
        "output_schema",
        "temperature",
        "max_tokens",
        "allowed_tools",
        "is_active",
        "created_by",
        "created_at",
        "updated_at",
    }
)

TABLE_PIPELINE_RUNS_COLS = frozenset(
    {
        "id",
        "pipeline_id",
        "user_input",
        "status",
        "result",
        "error",
        "started_at",
        "completed_at",
        "created_by",
    }
)

TABLE_PIPELINE_STEPS_COLS = frozenset(
    {
        "id",
        "pipeline_id",
        "step_order",
        "agent_role_id",
        "input_mapping",
        "custom_prompt_override",
        "created_at",
    }
)

TABLE_PIPELINE_STEP_RUNS_COLS = frozenset(
    {
        "id",
        "run_id",
        "step_order",
        "agent_role_id",
        "agent_role_name",
        "input_data",
        "output_data",
        "ai_response_raw",
        "tokens_used",
        "started_at",
        "completed_at",
        "status",
    }
)
