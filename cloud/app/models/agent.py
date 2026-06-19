from sqlalchemy import Column, Float, ForeignKey, Index, Integer, Table, Text, UniqueConstraint, text

from ..models import metadata

agent_roles = Table(
    "agent_roles",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", Text, nullable=False),
    Column("role_type", Text, nullable=False, server_default=text("sales_rep")),
    Column("description", Text, server_default=text("")),
    Column("system_prompt", Text, nullable=False),
    Column("input_schema", Text, server_default=text("{}")),
    Column("output_schema", Text, server_default=text("{}")),
    Column("temperature", Float, server_default=text("'0.7'")),
    Column("max_tokens", Integer, server_default=text("'2048'")),
    Column("allowed_tools", Text, server_default=text("[]")),
    Column("is_active", Integer, server_default=text("'1'")),
    Column("created_by", Integer, ForeignKey("users.id")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text),
)

agent_pipelines = Table(
    "agent_pipelines",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", Text, nullable=False),
    Column("description", Text, server_default=text("")),
    Column("is_active", Integer, server_default=text("'1'")),
    Column("created_by", Integer, ForeignKey("users.id")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text),
)

pipeline_steps = Table(
    "pipeline_steps",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("pipeline_id", Integer, ForeignKey("agent_pipelines.id"), nullable=False),
    Column("step_order", Integer, nullable=False),
    Column("agent_role_id", Integer, ForeignKey("agent_roles.id"), nullable=False),
    Column("input_mapping", Text, server_default=text("{}")),
    Column("custom_prompt_override", Text, server_default=text("")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

pipeline_runs = Table(
    "pipeline_runs",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("pipeline_id", Integer, ForeignKey("agent_pipelines.id"), nullable=False),
    Column("user_input", Text, server_default=text("")),
    Column("status", Text, server_default=text("running")),
    Column("result", Text, server_default=text("{}")),
    Column("error", Text, server_default=text("")),
    Column("started_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("completed_at", Text),
    Column("created_by", Integer, ForeignKey("users.id")),
)

pipeline_step_runs = Table(
    "pipeline_step_runs",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("run_id", Integer, ForeignKey("pipeline_runs.id"), nullable=False),
    Column("step_order", Integer, nullable=False),
    Column("agent_role_id", Integer, nullable=False),
    Column("agent_role_name", Text, server_default=text("")),
    Column("input_data", Text, server_default=text("{}")),
    Column("output_data", Text, server_default=text("{}")),
    Column("ai_response_raw", Text, server_default=text("")),
    Column("tokens_used", Integer, server_default=text("'0'")),
    Column("started_at", Text),
    Column("completed_at", Text),
    Column("status", Text, server_default=text("pending")),
)

agent_runtime_logs = Table(
    "agent_runtime_logs",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("agent_key", Text, nullable=False),
    Column("goal", Text, nullable=False),
    Column("status", Text, server_default=text("pending")),
    Column("iterations", Integer, server_default=text("'0'")),
    Column("tool_calls", Integer, server_default=text("'0'")),
    Column("result", Text),
    Column("error_message", Text),
    Column("started_at", Text),
    Column("completed_at", Text),
    Column("log_detail", Text, server_default=text("[]")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("trace_id", Text, server_default=text("")),
    Column("cost_data", Text, server_default=text("{}")),
)

agent_runtime_approvals = Table(
    "agent_runtime_approvals",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("trace_id", Text, nullable=False),
    Column("agent_key", Text, nullable=False),
    Column("goal", Text, nullable=False),
    Column("step", Integer, server_default=text("'0'")),
    Column("tool", Text, nullable=False),
    Column("params", Text, server_default=text("{}")),
    Column("reasoning", Text, server_default=text("")),
    Column("status", Text, server_default=text("pending")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("responded_at", Text),
    Column("responded_by", Text, server_default=text("")),
)

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

agent_runtime_snapshots = Table(
    "agent_runtime_snapshots",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("trace_id", Text, nullable=False),
    Column("step", Integer, nullable=False),
    Column("state_json", Text, nullable=False),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("expires_at", Text),
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

route_rules = Table(
    "route_rules",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", Text, nullable=False),
    Column("priority", Integer, nullable=False, server_default=text("'100'")),
    Column("condition_field", Text, nullable=False, server_default=text("keyword")),
    Column("condition_operator", Text, nullable=False, server_default=text("contains")),
    Column("condition_value", Text, nullable=False),
    Column("target_role_id", Integer, ForeignKey("agent_roles.id")),
    Column("fallback_role_id", Integer),
    Column("max_tokens", Integer, server_default=text("'2048'")),
    Column("temperature", Float, server_default=text("'0.7'")),
    Column("is_active", Integer, server_default=text("'1'")),
    Column("created_by", Integer, ForeignKey("users.id")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

route_logs = Table(
    "route_logs",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("input_text", Text, nullable=False),
    Column("matched_rule_id", Integer),
    Column("matched_rule_name", Text, server_default=text("")),
    Column("assigned_role_id", Integer),
    Column("assigned_role_name", Text, server_default=text("")),
    Column("confidence", Float, server_default=text("'0.0'")),
    Column("response_summary", Text, server_default=text("")),
    Column("tokens_used", Integer, server_default=text("'0'")),
    Column("latency_ms", Integer, server_default=text("'0'")),
    Column("source", Text, server_default=text("")),
    Column("created_by", Integer, ForeignKey("users.id")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

route_stats = Table(
    "route_stats",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("role_id", Integer, ForeignKey("agent_roles.id"), unique=True),
    Column("total_routed", Integer, server_default=text("'0'")),
    Column("avg_confidence", Float, server_default=text("'0.0'")),
    Column("avg_tokens", Float, server_default=text("'0.0'")),
    Column("avg_latency_ms", Float, server_default=text("'0.0'")),
    Column("last_routed_at", Text),
    Column("updated_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

Index("idx_agent_roles_type", "role_type")
Index("idx_pipeline_steps_order", "pipeline_id", "step_order")
Index("idx_step_runs_run", "run_id")
Index("idx_runtime_logs_agent", "agent_key")
Index("idx_runtime_logs_status", "status")
Index("idx_runtime_logs_trace", "trace_id")
Index("idx_approvals_status", "status")
Index("idx_approvals_trace", "trace_id")
Index("idx_state_snapshots_agent", "agent_id")
Index("idx_state_snapshots_status", "status")
Index("idx_agent_runtime_snapshots_trace_step", "trace_id", "step")
Index("idx_ask_role", "agent_role")
Index("idx_ask_entity", "entity_types")
Index("idx_cs_session", "session_id")
Index("idx_cs_status", "status")
Index("idx_cstep_session", "session_id")
Index("idx_aet_task", "task_id")
Index("idx_aet_status", "status")
Index("idx_aet_session", "session_id")
Index("idx_mcp_name", "tool_name")
Index("idx_mcp_audit_tool", "tool_name")
Index("idx_mcp_audit_user", "user_id")
Index("idx_mcp_audit_at", "created_at")
Index("idx_ot_name", "template_name")
Index("idx_route_priority", "priority")
Index("idx_route_logs_role", "assigned_role_id")
Index("idx_route_logs_time", "created_at")
Index("idx_route_stats_role", "role_id", unique=True)
