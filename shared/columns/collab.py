TABLE_AGENT_SKILLS_COLS = frozenset(
    {
        "id",
        "skill_name",
        "agent_role",
        "description",
        "entity_types",
        "capabilities",
        "confidence",
        "priority",
        "enabled",
        "created_at",
        "updated_at",
    }
)

TABLE_COLLABORATION_SESSIONS_COLS = frozenset(
    {
        "id",
        "session_id",
        "task_description",
        "source_entity_id",
        "source_agent_role",
        "orchestrator_agent",
        "status",
        "involved_agents",
        "routing_strategy",
        "total_steps",
        "completed_steps",
        "started_at",
        "completed_at",
        "result_summary",
    }
)

TABLE_COLLABORATION_STEPS_COLS = frozenset(
    {
        "id",
        "session_id",
        "step_order",
        "agent_role",
        "action_type",
        "input_summary",
        "output_summary",
        "entity_id",
        "status",
        "started_at",
        "completed_at",
        "duration_seconds",
        "metadata",
    }
)
