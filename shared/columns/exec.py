"""Exec module."""

TABLE_AGENT_EXECUTION_TASKS_COLS = frozenset(
    {
        "id",
        "task_id",
        "source",
        "session_id",
        "agent_role",
        "action_type",
        "input_data",
        "output_data",
        "status",
        "retry_count",
        "max_retries",
        "result_verified",
        "verification_detail",
        "requires_human_approval",
        "assigned_to",
        "created_at",
        "completed_at",
        "duration_ms",
    }
)

TABLE_MCP_TOOLS_COLS = frozenset(
    {
        "id",
        "tool_name",
        "description",
        "tool_version",
        "endpoint_url",
        "input_schema",
        "output_schema",
        "auth_required",
        "enabled",
        "created_by",
        "created_at",
        "updated_at",
    }
)

TABLE_ORCHESTRATION_TEMPLATES_COLS = frozenset(
    {
        "id",
        "template_name",
        "description",
        "steps",
        "version",
        "enabled",
        "created_by",
        "created_at",
        "updated_at",
    }
)
