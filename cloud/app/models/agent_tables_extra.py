from sqlalchemy import Column, Float, ForeignKey, Integer, Table, Text, UniqueConstraint, text

from ..models import metadata

agent_brains = Table(
    "agent_brains",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("agent_key", Text, nullable=False),
    Column("user_id", Integer, server_default=text("'0'")),
    Column("key", Text, nullable=False),
    Column("value", Text, nullable=False),
    Column("value_type", Text, server_default=text("str")),
    Column("updated_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    UniqueConstraint("agent_key", "user_id", "key"),
)

agent_state_snapshots = Table(
    "agent_state_snapshots",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("agent_id", Text, nullable=False),
    Column("step_id", Integer, server_default=text("'0'")),
    Column("plan_json", Text, server_default=text("[]")),
    Column("results_json", Text, server_default=text("[]")),
    Column("context_json", Text, server_default=text("{}")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("status", Text, server_default=text("active")),
)

agent_skills = Table(
    "agent_skills",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("skill_name", Text, nullable=False),
    Column("agent_role", Text, nullable=False),
    Column("description", Text, server_default=text("")),
    Column("entity_types", Text, server_default=text("[]")),
    Column("capabilities", Text, server_default=text("[]")),
    Column("confidence", Float, server_default=text("'0.5'")),
    Column("priority", Integer, server_default=text("'100'")),
    Column("enabled", Integer, server_default=text("'1'")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text),
)

collaboration_sessions = Table(
    "collaboration_sessions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("session_id", Text, nullable=False, unique=True),
    Column("task_description", Text, server_default=text("")),
    Column("source_entity_id", Text),
    Column("source_agent_role", Text, server_default=text("")),
    Column("orchestrator_agent", Text, server_default=text("")),
    Column("status", Text, server_default=text("active")),
    Column("involved_agents", Text, server_default=text("[]")),
    Column("routing_strategy", Text, server_default=text("semantic")),
    Column("total_steps", Integer, server_default=text("'0'")),
    Column("completed_steps", Integer, server_default=text("'0'")),
    Column("started_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("completed_at", Text),
    Column("result_summary", Text, server_default=text("")),
)

collaboration_steps = Table(
    "collaboration_steps",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("session_id", Text, ForeignKey("collaboration_sessions.session_id"), nullable=False),
    Column("step_order", Integer, nullable=False),
    Column("agent_role", Text, nullable=False),
    Column("action_type", Text, server_default=text("process")),
    Column("input_summary", Text, server_default=text("")),
    Column("output_summary", Text, server_default=text("")),
    Column("entity_id", Text),
    Column("status", Text, server_default=text("pending")),
    Column("started_at", Text),
    Column("completed_at", Text),
    Column("duration_seconds", Integer, server_default=text("'0'")),
    Column("metadata", Text, server_default=text("{}")),
)

agent_execution_tasks = Table(
    "agent_execution_tasks",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("task_id", Text, unique=True),
    Column("source", Text, server_default=text("internal")),
    Column("session_id", Text, server_default=text("")),
    Column("agent_role", Text, server_default=text("")),
    Column("action_type", Text, server_default=text("process")),
    Column("input_data", Text, server_default=text("{}")),
    Column("output_data", Text, server_default=text("{}")),
    Column("status", Text, server_default=text("pending")),
    Column("retry_count", Integer, server_default=text("'0'")),
    Column("max_retries", Integer, server_default=text("'3'")),
    Column("result_verified", Integer, server_default=text("'0'")),
    Column("verification_detail", Text, server_default=text("")),
    Column("requires_human_approval", Integer, server_default=text("'0'")),
    Column("assigned_to", Text, server_default=text("")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("completed_at", Text),
    Column("duration_ms", Integer, server_default=text("'0'")),
)

mcp_tools = Table(
    "mcp_tools",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("tool_name", Text, unique=True),
    Column("description", Text, server_default=text("")),
    Column("tool_version", Text, server_default=text("1.0.0")),
    Column("endpoint_url", Text, server_default=text("")),
    Column("input_schema", Text, server_default=text("{}")),
    Column("output_schema", Text, server_default=text("{}")),
    Column("auth_required", Integer, server_default=text("'0'")),
    Column("enabled", Integer, server_default=text("'1'")),
    Column("created_by", Integer),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text),
)

mcp_audit_log = Table(
    "mcp_audit_log",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("tool_name", Text, nullable=False),
    Column("user_id", Integer, nullable=False),
    Column("user_role", Text, server_default=text("")),
    Column("params", Text, server_default=text("{}")),
    Column("result", Text, server_default=text("{}")),
    Column("granted", Integer, server_default=text("'0'")),
    Column("reason", Text, server_default=text("")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

orchestration_templates = Table(
    "orchestration_templates",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("template_name", Text, unique=True),
    Column("description", Text, server_default=text("")),
    Column("steps", Text, server_default=text("[]")),
    Column("version", Text, server_default=text("1.0.0")),
    Column("enabled", Integer, server_default=text("'1'")),
    Column("created_by", Integer),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text),
)
