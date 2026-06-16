from sqlalchemy import Column, Float, ForeignKey, Index, Integer, MetaData, Table, Text, UniqueConstraint, text

metadata = MetaData()

Table(
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


Table(
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


Table(
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


Table(
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


Table(
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


Table(
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


Table(
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


Table(
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


Table(
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


Table(
    "agent_runtime_snapshots",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("trace_id", Text, nullable=False),
    Column("step", Integer, nullable=False),
    Column("state_json", Text, nullable=False),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("expires_at", Text),
)


Table(
    "audit_logs",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, nullable=False),
    Column("action", Text, nullable=False),
    Column("entity_type", Text, nullable=False),
    Column("entity_id", Integer),
    Column("detail", Text, server_default=text("")),
    Column("source_end", Text, nullable=False),
    Column("ip_address", Text, server_default=text("")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
    "compliance_audit_records",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("message_type", Text, nullable=False, server_default=text("text")),
    Column("content", Text, nullable=False),
    Column("source_id", Text, server_default=text("")),
    Column("score", Float, server_default=text("'0.0'")),
    Column("risk_level", Text, nullable=False, server_default=text("low")),
    Column("passed", Integer, nullable=False, server_default=text("'1'")),
    Column("violations", Text, server_default=text("[]")),
    Column("ai_analysis", Text, server_default=text("")),
    Column("reviewed_by", Integer, ForeignKey("users.id")),
    Column("reviewed_at", Text),
    Column("created_by", Integer, ForeignKey("users.id")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
    "audit_chain_entries",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("entity_type", Text, nullable=False),
    Column("entity_id", Text, nullable=False),
    Column("action", Text, nullable=False),
    Column("previous_hash", Text, server_default=text("")),
    Column("current_hash", Text, nullable=False),
    Column("payload", Text, server_default=text("{}")),
    Column("metadata", Text, server_default=text("{}")),
    Column("source", Text, server_default=text("")),
    Column("created_by", Integer, ForeignKey("users.id")),
    Column("performed_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
    "training_corrections",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("audit_record_id", Integer, ForeignKey("compliance_audit_records.id")),
    Column("title", Text, nullable=False),
    Column("description", Text, server_default=text("")),
    Column("category", Text, server_default=text("general")),
    Column("severity", Text, nullable=False, server_default=text("medium")),
    Column("status", Text, nullable=False, server_default=text("pending")),
    Column("assigned_to", Integer, ForeignKey("users.id")),
    Column("created_by", Integer, ForeignKey("users.id")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text),
)


Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("username", Text, nullable=False, unique=True),
    Column("hashed_password", Text, nullable=False),
    Column("role", Text, server_default=text("user")),
    Column("is_active", Integer, server_default=text("'1'")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text),
)


Table(
    "api_tokens",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("token_hash", Text, nullable=False),
    Column("name", Text, nullable=False),
    Column("is_active", Integer, server_default=text("'1'")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
    "teams",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", Text, nullable=False),
    Column("description", Text),
    Column("is_active", Integer, server_default=text("'1'")),
    Column("created_by", Integer),
    Column("created_at", Text),
    Column("updated_at", Text),
)


Table(
    "user_team",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("team_id", Integer, ForeignKey("teams.id"), nullable=False),
    Column("role", Text, server_default=text("member")),
    Column("created_at", Text),
    UniqueConstraint("user_id", "team_id"),
)


Table(
    "system_configs",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("key", Text, nullable=False, unique=True),
    Column("value", Text, nullable=False),
    Column("description", Text, server_default=text("")),
    Column("updated_by", Integer),
    Column("updated_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
    "token_blacklist",
    metadata,
    Column("token_jti", Text, primary_key=True),
    Column("expires_at", Text, nullable=False),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
    "asr_tasks",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("task_id", Text, nullable=False, unique=True),
    Column("file_path", Text, server_default=text("")),
    Column("transcript", Text, server_default=text("")),
    Column("summary", Text, server_default=text("{}")),
    Column("status", Text, server_default=text("pending")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
    "admission_records",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("hospital_name", Text, nullable=False),
    Column("department", Text, server_default=text("")),
    Column("product", Text, nullable=False),
    Column("status", Text, server_default=text("待提交")),
    Column("meeting_date", Text),
    Column("notes", Text, server_default=text("")),
    Column("rep_id", Integer),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text),
)


Table(
    "quotation_approvals",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("quotation_id", Text, nullable=False, unique=True),
    Column("rep_id", Integer, nullable=False),
    Column("product", Text, nullable=False),
    Column("amount", Float, nullable=False),
    Column("limit_amount", Float, server_default=text("'0.0'")),
    Column("status", Text, server_default=text("pending_approval")),
    Column("compliance_passed", Integer, server_default=text("'0'")),
    Column("review_notes", Text, server_default=text("")),
    Column("reviewed_by", Integer),
    Column("reviewed_at", Text),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
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


Table(
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


Table(
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


Table(
    "compliance_rules",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", Text, nullable=False),
    Column("category", Text, nullable=False),
    Column("keyword", Text, nullable=False),
    Column("max_value", Float),
    Column("created_by", Integer, ForeignKey("users.id")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
    "contents",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("title", Text, nullable=False),
    Column("body", Text, nullable=False),
    Column("category", Text, nullable=False),
    Column("tags", Text, server_default=text("")),
    Column("status", Text, nullable=False, server_default=text("draft")),
    Column("compliance_score", Float),
    Column("created_by", Integer, ForeignKey("users.id")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
    "notification_templates",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", Text, nullable=False, unique=True),
    Column("title_template", Text, nullable=False),
    Column("body_template", Text, nullable=False),
    Column("category", Text, nullable=False),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
    "notifications",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, nullable=False),
    Column("template_id", Integer),
    Column("title", Text, nullable=False),
    Column("body", Text, nullable=False),
    Column("category", Text, nullable=False),
    Column("ref_type", Text, server_default=text("")),
    Column("ref_id", Integer),
    Column("context_json", Text, server_default=text("")),
    Column("is_read", Integer, server_default=text("'0'")),
    Column("read_at", Text),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
    "customers",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", Text, nullable=False),
    Column("title", Text, server_default=text("")),
    Column("hospital", Text, server_default=text("")),
    Column("department", Text, server_default=text("")),
    Column("specialty", Text, server_default=text("")),
    Column("phone", Text, server_default=text("")),
    Column("email", Text, server_default=text("")),
    Column("tags", Text, server_default=text("[]")),
    Column("status", Text, server_default=text("active")),
    Column("created_by", Integer),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text),
)


Table(
    "customer_interactions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("customer_id", Integer, nullable=False),
    Column("type", Text, nullable=False, server_default=text("visit")),
    Column("summary", Text, server_default=text("")),
    Column("outcome", Text, server_default=text("")),
    Column("conducted_by", Integer),
    Column("conducted_at", Text),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
    "opportunities",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("customer_id", Integer, ForeignKey("customers.id"), nullable=False),
    Column("name", Text, nullable=False),
    Column("description", Text, server_default=text("")),
    Column("stage", Text, nullable=False, server_default=text("lead")),
    Column("probability", Integer, server_default=text("'0'")),
    Column("estimated_value", Float, server_default=text("'0.0'")),
    Column("actual_value", Float, server_default=text("'0.0'")),
    Column("assigned_to", Integer, ForeignKey("users.id")),
    Column("close_date", Text),
    Column("notes", Text, server_default=text("")),
    Column("is_active", Integer, server_default=text("'1'")),
    Column("created_by", Integer),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text),
)


Table(
    "decision_cases",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", Text, nullable=False),
    Column("pipeline_run_id", Integer, ForeignKey("pipeline_runs.id")),
    Column("description", Text, server_default=text("")),
    Column("outcome", Text, server_default=text("")),
    Column("outcome_score", Float, server_default=text("'0.0'")),
    Column("context", Text, server_default=text("{}")),
    Column("tags", Text, server_default=text("[]")),
    Column("is_active", Integer, server_default=text("'1'")),
    Column("created_by", Integer, ForeignKey("users.id")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text),
)


Table(
    "causal_analyses",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("case_id", Integer, ForeignKey("decision_cases.id"), nullable=False),
    Column("analysis_type", Text, nullable=False, server_default=text("causal")),
    Column("summary", Text, server_default=text("")),
    Column("key_drivers", Text, server_default=text("[]")),
    Column("causal_chain", Text, server_default=text("[]")),
    Column("attribution_scores", Text, server_default=text("{}")),
    Column("recommendations", Text, server_default=text("[]")),
    Column("ai_response_raw", Text, server_default=text("")),
    Column("tokens_used", Integer, server_default=text("'0'")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
    "cross_case_insights",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("title", Text, nullable=False),
    Column("insight_type", Text, nullable=False, server_default=text("pattern")),
    Column("summary", Text, server_default=text("")),
    Column("detail", Text, server_default=text("")),
    Column("evidence", Text, server_default=text("[]")),
    Column("confidence", Float, server_default=text("'0.5'")),
    Column("applicability", Text, server_default=text("general")),
    Column("source_run_ids", Text, server_default=text("[]")),
    Column("is_active", Integer, server_default=text("'1'")),
    Column("created_by", Integer, ForeignKey("users.id")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text),
)


Table(
    "causal_graphs",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("graph_id", Text, unique=True),
    Column("decision_id", Text),
    Column("graph_data", Text, server_default=text("{}")),
    Column("summary", Text),
    Column("node_count", Integer),
    Column("edge_count", Integer),
    Column("created_by", Integer),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
    "counterfactual_scenarios",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("scenario_id", Text, unique=True),
    Column("strategy_id", Text),
    Column("base_description", Text),
    Column("variable_changes", Text, server_default=text("[]")),
    Column("predicted_outcome", Text, server_default=text("{}")),
    Column("confidence", Float),
    Column("created_by", Integer),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
    "did_registry",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("did", Text, nullable=False, unique=True),
    Column("entity_type", Text, server_default=text("user")),
    Column("entity_id", Integer),
    Column("public_key", Text, server_default=text("")),
    Column("status", Text, server_default=text("active")),
    Column("metadata", Text, server_default=text("{}")),
    Column("created_by", Integer, ForeignKey("users.id")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text),
)


Table(
    "vc_credentials",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("vc_id", Text, nullable=False, unique=True),
    Column("issuer_did", Text, ForeignKey("did_registry.did"), nullable=False),
    Column("subject_did", Text, ForeignKey("did_registry.did"), nullable=False),
    Column("credential_type", Text, nullable=False),
    Column("claims", Text, server_default=text("{}")),
    Column("issuance_date", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("expiration_date", Text),
    Column("proof", Text, server_default=text("")),
    Column("status", Text, server_default=text("active")),
    Column("revoked_at", Text),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
    "fed_audit_contributions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("contributor_did", Text, ForeignKey("did_registry.did"), nullable=False),
    Column("contribution_type", Text, nullable=False),
    Column("payload_hash", Text, server_default=text("")),
    Column("payload_summary", Text, server_default=text("")),
    Column("weight", Float, server_default=text("'1.0'")),
    Column("verified", Integer, server_default=text("'0'")),
    Column("verified_by", Text, server_default=text("")),
    Column("audit_chain_hash", Text, server_default=text("")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
    "privacy_budgets",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("did", Text, ForeignKey("did_registry.did"), nullable=False),
    Column("epsilon_total", Float, server_default=text("'1.0'")),
    Column("epsilon_spent", Float, server_default=text("'0.0'")),
    Column("epsilon_remaining", Float, server_default=text("'1.0'")),
    Column("query_count", Integer, server_default=text("'0'")),
    Column("last_query_at", Text),
    Column("reset_at", Text),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
    "data_masking_rules",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("rule_name", Text, nullable=False, unique=True),
    Column("field_pattern", Text, nullable=False),
    Column("masking_type", Text, nullable=False),
    Column("masking_config", Text, server_default=text("{}")),
    Column("applies_to", Text, server_default=text("all")),
    Column("enabled", Integer, server_default=text("'1'")),
    Column("created_by", Integer, ForeignKey("users.id")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text),
)


Table(
    "dp_audit_log",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("did", Text, ForeignKey("did_registry.did"), nullable=False),
    Column("operation_type", Text, nullable=False),
    Column("epsilon_consumed", Float, server_default=text("'0.0'")),
    Column("data_category", Text, server_default=text("")),
    Column("row_count", Integer, server_default=text("'0'")),
    Column("noise_level", Float, server_default=text("'0.0'")),
    Column("approved", Integer, server_default=text("'1'")),
    Column("details", Text, server_default=text("{}")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
    "event_bus_definitions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("event_type", Text, nullable=False, unique=True),
    Column("display_name", Text, server_default=text("")),
    Column("description", Text, server_default=text("")),
    Column("source_end", Text, server_default=text("cloud")),
    Column("target_ends", Text, server_default=text("[]")),
    Column("schema_template", Text, server_default=text("{}")),
    Column("priority", Integer, server_default=text("'100'")),
    Column("enabled", Integer, server_default=text("'1'")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
    "event_bus_messages",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("message_id", Text, nullable=False, unique=True),
    Column("event_type", Text, ForeignKey("event_bus_definitions.event_type"), nullable=False),
    Column("source_end", Text, server_default=text("cloud")),
    Column("source_entity_type", Text, server_default=text("")),
    Column("source_entity_id", Text, server_default=text("")),
    Column("payload", Text, server_default=text("{}")),
    Column("correlation_id", Text, server_default=text("")),
    Column("priority", Integer, server_default=text("'100'")),
    Column("status", Text, server_default=text("pending")),
    Column("retry_count", Integer, server_default=text("'0'")),
    Column("max_retries", Integer, server_default=text("'3'")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("delivered_at", Text),
)


Table(
    "event_delivery_log",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("message_id", Text, ForeignKey("event_bus_messages.message_id"), nullable=False),
    Column("target_end", Text, nullable=False),
    Column("delivery_status", Text, server_default=text("pending")),
    Column("attempt", Integer, server_default=text("'1'")),
    Column("response_summary", Text, server_default=text("")),
    Column("duration_ms", Integer, server_default=text("'0'")),
    Column("error_message", Text, server_default=text("")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
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


Table(
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


Table(
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


Table(
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


Table(
    "hcp_profiles",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", Text, nullable=False),
    Column("title", Text, server_default=text("")),
    Column("hospital", Text, server_default=text("")),
    Column("department", Text, server_default=text("")),
    Column("specialty", Text, server_default=text("")),
    Column("city", Text, server_default=text("")),
    Column("tier", Text, server_default=text("B")),
    Column("traits", Text, server_default=text("{}")),
    Column("prescription_volume", Float, server_default=text("'0'")),
    Column("influence_score", Float, server_default=text("'0.5'")),
    Column("digital_engagement", Float, server_default=text("'0.5'")),
    Column("is_active", Integer, server_default=text("'1'")),
    Column("created_by", Integer, ForeignKey("users.id")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
    "hcp_interactions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("hcp_id", Integer, ForeignKey("hcp_profiles.id"), nullable=False),
    Column("interaction_type", Text, nullable=False),
    Column("content", Text, server_default=text("")),
    Column("response", Text, server_default=text("")),
    Column("outcome", Text, server_default=text("")),
    Column("strategy_used", Text, server_default=text("")),
    Column("conducted_by", Integer, ForeignKey("users.id")),
    Column("conducted_at", Text),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
    "hcp_simulations",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("hcp_id", Integer, ForeignKey("hcp_profiles.id"), nullable=False),
    Column("scenario", Text, nullable=False),
    Column("strategy", Text, server_default=text("")),
    Column("expected_outcome", Text, server_default=text("")),
    Column("confidence", Float, server_default=text("'0.5'")),
    Column("suggested_approach", Text, server_default=text("")),
    Column("key_concerns", Text, server_default=text("")),
    Column("recommended_topics", Text, server_default=text("")),
    Column("risk_factors", Text, server_default=text("")),
    Column("simulation_data", Text, server_default=text("{}")),
    Column("status", Text, server_default=text("completed")),
    Column("created_by", Integer, ForeignKey("users.id")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
    "kg_entities",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("entity_id", Text, nullable=False, unique=True),
    Column("entity_type", Text, nullable=False),
    Column("name", Text, nullable=False),
    Column("aliases", Text, server_default=text("[]")),
    Column("properties", Text, server_default=text("{}")),
    Column("source_table", Text, server_default=text("")),
    Column("source_row_id", Integer),
    Column("status", Text, server_default=text("active")),
    Column("confidence", Float, server_default=text("'1.0'")),
    Column("created_by", Integer, ForeignKey("users.id")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text),
)


Table(
    "kg_relations",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("source_entity_id", Text, ForeignKey("kg_entities.entity_id"), nullable=False),
    Column("target_entity_id", Text, ForeignKey("kg_entities.entity_id"), nullable=False),
    Column("relation_type", Text, nullable=False),
    Column("weight", Float, server_default=text("'1.0'")),
    Column("properties", Text, server_default=text("{}")),
    Column("direction", Text, server_default=text("directed")),
    Column("confidence", Float, server_default=text("'1.0'")),
    Column("source", Text, server_default=text("manual")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
    "kg_search_cache",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("query_hash", Text, nullable=False),
    Column("query_text", Text, nullable=False),
    Column("result_summary", Text, server_default=text("")),
    Column("result_count", Integer, server_default=text("'0'")),
    Column("cache_ttl", Integer, server_default=text("'300'")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
    "market_intel_sources",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", Text, nullable=False),
    Column("source_type", Text, nullable=False, server_default=text("competitor")),
    Column("target_keywords", Text, server_default=text("[]")),
    Column("is_active", Integer, server_default=text("'1'")),
    Column("created_by", Integer, ForeignKey("users.id")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text),
)


Table(
    "market_intel_items",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("source_id", Integer, ForeignKey("market_intel_sources.id")),
    Column("title", Text, nullable=False),
    Column("summary", Text, server_default=text("")),
    Column("content", Text, server_default=text("")),
    Column("url", Text, server_default=text("")),
    Column("item_type", Text, nullable=False, server_default=text("competitor")),
    Column("relevance_tags", Text, server_default=text("[]")),
    Column("impact_level", Text, server_default=text("medium")),
    Column("status", Text, server_default=text("unread")),
    Column("ai_analysis", Text, server_default=text("")),
    Column("collected_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("created_by", Integer, ForeignKey("users.id")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text),
)


Table(
    "mdt_sessions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("title", Text, nullable=False),
    Column("question", Text, nullable=False),
    Column("context", Text, server_default=text("")),
    Column("status", Text, nullable=False, server_default=text("active")),
    Column("consensus", Text, server_default=text("")),
    Column("consensus_json", Text, server_default=text("{}")),
    Column("round_count", Integer, server_default=text("'0'")),
    Column("created_by", Integer, ForeignKey("users.id")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text),
)


Table(
    "mdt_participants",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("session_id", Integer, ForeignKey("mdt_sessions.id"), nullable=False),
    Column("agent_role_id", Integer, ForeignKey("agent_roles.id"), nullable=False),
    Column("role_name", Text, server_default=text("")),
    Column("stance", Text, server_default=text("neutral")),
    Column("vote_weight", Float, server_default=text("'1.0'")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
    "mdt_opinions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("session_id", Integer, ForeignKey("mdt_sessions.id"), nullable=False),
    Column("participant_id", Integer, ForeignKey("mdt_participants.id"), nullable=False),
    Column("round_number", Integer, nullable=False),
    Column("opinion", Text, server_default=text("")),
    Column("summary", Text, server_default=text("")),
    Column("sentiment", Text, server_default=text("neutral")),
    Column("confidence", Float, server_default=text("'0.5'")),
    Column("key_points", Text, server_default=text("[]")),
    Column("ai_response_raw", Text, server_default=text("")),
    Column("tokens_used", Integer, server_default=text("'0'")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
    "async_mdt_opinions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("decision_id", Integer, ForeignKey("soap_decisions.id"), nullable=False),
    Column("contributor_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("contributor_role", Text, server_default=text("")),
    Column("opinion", Text, nullable=False),
    Column("supporting_data", Text, server_default=text("")),
    Column("stance", Text, server_default=text("neutral")),
    Column("confidence", Float, server_default=text("'0.5'")),
    Column("attachments", Text, server_default=text("[]")),
    Column("is_final", Integer, server_default=text("'0'")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
    "memory_gates",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", Text, nullable=False),
    Column("source_type", Text, nullable=False),
    Column("importance_threshold", Float, server_default=text("'0.5'")),
    Column("ttl_days", Integer, server_default=text("'90'")),
    Column("retention_policy", Text, server_default=text("normal")),
    Column("is_active", Integer, server_default=text("'1'")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
    "memory_entries",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("title", Text, nullable=False),
    Column("content", Text, server_default=text("")),
    Column("memory_type", Text, nullable=False, server_default=text("insight")),
    Column("source_type", Text, server_default=text("")),
    Column("source_id", Text, server_default=text("")),
    Column("importance", Float, server_default=text("'0.5'")),
    Column("context_tags", Text, server_default=text("[]")),
    Column("embedding", Text, server_default=text("")),
    Column("access_count", Integer, server_default=text("'0'")),
    Column("last_accessed", Text),
    Column("is_active", Integer, server_default=text("'1'")),
    Column("created_by", Integer, ForeignKey("users.id")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
    "memory_recall_log",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("query_text", Text, server_default=text("")),
    Column("memory_ids", Text, server_default=text("[]")),
    Column("result_count", Integer, server_default=text("'0'")),
    Column("context", Text, server_default=text("{}")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
    "memory_utility_scores",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("memory_entry_id", Integer, ForeignKey("memory_entries.id"), nullable=False, unique=True),
    Column("utility_score", Float, server_default=text("'0.0'")),
    Column("access_frequency", Float, server_default=text("'0.0'")),
    Column("recency_score", Float, server_default=text("'0.0'")),
    Column("importance_score", Float, server_default=text("'0.0'")),
    Column("connectivity_score", Float, server_default=text("'0.0'")),
    Column("decay_rate", Float, server_default=text("'0.0'")),
    Column("last_utility_update", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
    "sleep_consolidation_logs",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("consolidation_type", Text, nullable=False),
    Column("source_entry_ids", Text, server_default=text("[]")),
    Column("target_entry_id", Integer, ForeignKey("memory_entries.id")),
    Column("action_detail", Text, server_default=text("")),
    Column("utility_before", Float, server_default=text("'0.0'")),
    Column("utility_after", Float, server_default=text("'0.0'")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
    "memory_consolidation_log",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("consolidation_type", Text, nullable=False),
    Column("source_table", Text, server_default=text("")),
    Column("item_count", Integer, server_default=text("'0'")),
    Column("items_promoted", Integer, server_default=text("'0'")),
    Column("items_pruned", Integer, server_default=text("'0'")),
    Column("items_superseded", Integer, server_default=text("'0'")),
    Column("duration_ms", Integer, server_default=text("'0'")),
    Column("status", Text, server_default=text("completed")),
    Column("details", Text, server_default=text("{}")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
    "memory_associations",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("memory_id_a", Integer, ForeignKey("memory_entries.id"), nullable=False),
    Column("memory_id_b", Integer, ForeignKey("memory_entries.id"), nullable=False),
    Column("relation_type", Text, nullable=False, server_default=text("related")),
    Column("weight", Float, server_default=text("'1.0'")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
    "effect_metrics",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("metric_id", Text, unique=True),
    Column("agent_role", Text),
    Column("metric_type", Text),
    Column("metric_value", Float),
    Column("metric_unit", Text),
    Column("source_table", Text),
    Column("source_row_id", Text),
    Column("source_sub", Text, server_default=text("")),
    Column("period_start", Text),
    Column("period_end", Text),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
    "benchmark_reports",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("report_id", Text, unique=True),
    Column("report_name", Text),
    Column("report_type", Text),
    Column("data_source", Text, server_default=text("aggregated")),
    Column("summary", Text),
    Column("metrics", Text, server_default=text("{}")),
    Column("period", Text),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
    "agent_marketplace",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("item_id", Text, unique=True),
    Column("item_name", Text),
    Column("item_type", Text, server_default=text("template")),
    Column("description", Text),
    Column("agent_config", Text, server_default=text("{}")),
    Column("category", Text),
    Column("price_model", Text, server_default=text("free")),
    Column("rating", Float),
    Column("download_count", Integer),
    Column("enabled", Integer),
    Column("publisher", Text),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text),
)


Table(
    "supply_chain_items",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("item_id", Text, unique=True),
    Column("item_name", Text),
    Column("sku", Text),
    Column("category", Text),
    Column("current_stock", Integer),
    Column("min_stock", Integer),
    Column("max_stock", Integer),
    Column("unit_price", Float),
    Column("supplier", Text),
    Column("status", Text, server_default=text("active")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text),
)


Table(
    "sensor_sessions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("session_id", Text, unique=True),
    Column("session_name", Text),
    Column("event_type", Text, server_default=text("academic_meeting")),
    Column("location", Text),
    Column("start_time", Text),
    Column("end_time", Text),
    Column("data_summary", Text, server_default=text("{}")),
    Column("status", Text, server_default=text("active")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
    "settings",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("key", Text, nullable=False, unique=True),
    Column("value", Text, nullable=False, server_default=text("")),
    Column("updated_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
    "token_budget",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, nullable=False),
    Column("model", Text, nullable=False),
    Column("daily_used", Integer, nullable=False, server_default=text("'0'")),
    Column("alert_sent", Integer, nullable=False, server_default=text("'0'")),
    Column("updated_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
    "token_usage",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, nullable=False),
    Column("model", Text, nullable=False),
    Column("tokens", Integer, nullable=False, server_default=text("'0'")),
    Column("cost", Float, nullable=False, server_default=text("'0.0'")),
    Column("usage_date", Text, nullable=False),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
    "privacy_compute_jobs",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("job_id", Text, unique=True),
    Column("compute_type", Text),
    Column("sensitivity_level", Text, server_default=text("medium")),
    Column("data_summary", Text, server_default=text("")),
    Column("selected_scheme", Text, server_default=text("")),
    Column("status", Text, server_default=text("pending")),
    Column("epsilon_used", Float, server_default=text("'0.0'")),
    Column("noise_level", Float, server_default=text("'0.0'")),
    Column("result_summary", Text, server_default=text("")),
    Column("created_by", Integer, ForeignKey("users.id")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("completed_at", Text),
)


Table(
    "federated_rounds",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("round_id", Text, unique=True),
    Column("model_name", Text),
    Column("round_number", Integer),
    Column("participant_count", Integer, server_default=text("'0'")),
    Column("aggregation_method", Text, server_default=text("fed_avg")),
    Column("global_metrics", Text, server_default=text("{}")),
    Column("status", Text, server_default=text("pending")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("completed_at", Text),
)


Table(
    "nmpa_compliance_logs",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("log_id", Text, unique=True),
    Column("document_type", Text),
    Column("content_summary", Text, server_default=text("")),
    Column("violations_found", Integer, server_default=text("'0'")),
    Column("violation_details", Text, server_default=text("[]")),
    Column("human_review_required", Integer, server_default=text("'0'")),
    Column("human_reviewer", Text, server_default=text("")),
    Column("human_reviewed_at", Text),
    Column("created_by", Integer, ForeignKey("users.id")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
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


Table(
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


Table(
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


Table(
    "soap_templates",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", Text, nullable=False),
    Column("category", Text, nullable=False, server_default=text("general")),
    Column("description", Text, server_default=text("")),
    Column("structure", Text, nullable=False, server_default=text("{}")),
    Column("is_active", Integer, server_default=text("'1'")),
    Column("created_by", Integer, ForeignKey("users.id")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
    "soap_decisions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("title", Text, nullable=False),
    Column("template_id", Integer, ForeignKey("soap_templates.id")),
    Column("subjective", Text, server_default=text("")),
    Column("objective", Text, server_default=text("")),
    Column("assessment", Text, server_default=text("")),
    Column("plan", Text, server_default=text("")),
    Column("status", Text, nullable=False, server_default=text("draft")),
    Column("priority", Text, server_default=text("medium")),
    Column("tags", Text, server_default=text("[]")),
    Column("decision_summary", Text, server_default=text("")),
    Column("decided_by", Integer, ForeignKey("users.id")),
    Column("decided_at", Text),
    Column("is_active", Integer, server_default=text("'1'")),
    Column("created_by", Integer, ForeignKey("users.id")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
    "task_boards",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", Text, nullable=False),
    Column("description", Text, server_default=text("")),
    Column("owner_id", Integer, nullable=False),
    Column("is_active", Integer, server_default=text("'1'")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text),
)


Table(
    "board_tasks",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("board_id", Integer, nullable=False),
    Column("title", Text, nullable=False),
    Column("description", Text, server_default=text("")),
    Column("status", Text, nullable=False, server_default=text("todo")),
    Column("priority", Text, server_default=text("medium")),
    Column("assignee_id", Integer),
    Column("due_date", Text),
    Column("sort_order", Integer, server_default=text("'0'")),
    Column("is_active", Integer, server_default=text("'1'")),
    Column("created_by", Integer),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text),
)


Table(
    "training_modules",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("title", Text, nullable=False),
    Column("category", Text, nullable=False, server_default=text("compliance")),
    Column("difficulty", Text, nullable=False, server_default=text("medium")),
    Column("content", Text, server_default=text("")),
    Column("prerequisites", Text, server_default=text("[]")),
    Column("passing_score", Float, server_default=text("'0.7'")),
    Column("estimated_minutes", Integer, server_default=text("'15'")),
    Column("is_active", Integer, server_default=text("'1'")),
    Column("created_by", Integer, ForeignKey("users.id")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
    "training_sessions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("module_id", Integer, ForeignKey("training_modules.id"), nullable=False),
    Column("score", Float, server_default=text("'0.0'")),
    Column("passed", Integer, server_default=text("'0'")),
    Column("time_spent_seconds", Integer, server_default=text("'0'")),
    Column("answers", Text, server_default=text("[]")),
    Column("feedback", Text, server_default=text("")),
    Column("difficulty_used", Text, server_default=text("medium")),
    Column("next_difficulty", Text, server_default=text("")),
    Column("completed_at", Text),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
    "training_attributions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("training_session_id", Integer, ForeignKey("training_sessions.id")),
    Column("metric_name", Text, nullable=False),
    Column("metric_before", Float, server_default=text("'0.0'")),
    Column("metric_after", Float, server_default=text("'0.0'")),
    Column("change_pct", Float, server_default=text("'0.0'")),
    Column("attribution_score", Float, server_default=text("'0.0'")),
    Column("confidence", Float, server_default=text("'0.0'")),
    Column("analysis", Text, server_default=text("")),
    Column("period_days", Integer, server_default=text("'30'")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
    "training_scripts",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("script_id", Text, unique=True),
    Column("script_name", Text),
    Column("source_agent_role", Text),
    Column("source_collaboration_id", Text),
    Column("description", Text),
    Column("steps", Text, server_default=text("[]")),
    Column("difficulty", Text, server_default=text("mid")),
    Column("target_roles", Text, server_default=text("[]")),
    Column("score", Float),
    Column("created_by", Integer, ForeignKey("users.id")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text),
)


Table(
    "training_roi_analysis",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("analysis_id", Text, unique=True),
    Column("period_start", Text),
    Column("period_end", Text),
    Column("training_hours", Float),
    Column("participants", Integer),
    Column("behavior_change_score", Float),
    Column("sales_impact", Float),
    Column("cost_savings", Float),
    Column("roi", Float),
    Column("metadata", Text, server_default=text("{}")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
    "user_profiles",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("persona_type", Text, server_default=text("")),
    Column("specialization", Text, server_default=text("")),
    Column("experience_level", Text, server_default=text("mid")),
    Column("preferred_content_types", Text, server_default=text("[]")),
    Column("custom_tags", Text, server_default=text("[]")),
    Column("embedding", Text, server_default=text("")),
    Column("updated_at", Text),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
    "user_behaviors",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("action_type", Text, nullable=False),
    Column("target_type", Text, server_default=text("")),
    Column("target_id", Text, server_default=text("")),
    Column("metadata", Text, server_default=text("{}")),
    Column("session_id", Text, server_default=text("")),
    Column("duration_seconds", Integer, server_default=text("'0'")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
    "recommendations",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("rec_type", Text, nullable=False),
    Column("rec_target_id", Text, server_default=text("")),
    Column("rec_title", Text, server_default=text("")),
    Column("rec_reason", Text, server_default=text("")),
    Column("score", Float, server_default=text("'0.0'")),
    Column("strategy_name", Text, server_default=text("")),
    Column("clicked", Integer, server_default=text("'0'")),
    Column("dismissed", Integer, server_default=text("'0'")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
    "working_memory",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("session_id", Text, nullable=False),
    Column("slot_key", Text, nullable=False),
    Column("slot_value", Text, server_default=text("")),
    Column("slot_type", Text, server_default=text("string")),
    Column("ttl_seconds", Integer, server_default=text("'1800'")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("expires_at", Text),
    UniqueConstraint("session_id", "slot_key"),
)


Table(
    "episodic_memory",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("event_type", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("description", Text, server_default=text("")),
    Column("context", Text, server_default=text("{}")),
    Column("outcome", Text, server_default=text("")),
    Column("valence", Float, server_default=text("'0.0'")),
    Column("intensity", Float, server_default=text("'0.5'")),
    Column("involved_agents", Text, server_default=text("[]")),
    Column("related_entity_type", Text, server_default=text("")),
    Column("related_entity_id", Integer),
    Column("is_consolidated", Integer, server_default=text("'0'")),
    Column("created_by", Text, server_default=text("")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
    "world_tree_nodes",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", Text, nullable=False),
    Column("description", Text, server_default=text("")),
    Column("parent_id", Integer, ForeignKey("world_tree_nodes.id")),
    Column("path", Text, server_default=text("")),
    Column("level", Integer, server_default=text("'0'")),
    Column("node_type", Text, server_default=text("tag")),
    Column("sort_order", Integer, server_default=text("'0'")),
    Column("metadata", Text, server_default=text("{}")),
    Column("is_active", Integer, server_default=text("'1'")),
    Column("created_by", Integer, ForeignKey("users.id")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)


Table(
    "node_memory_links",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("node_id", Integer, ForeignKey("world_tree_nodes.id"), nullable=False),
    Column("memory_entry_id", Integer, ForeignKey("memory_entries.id"), nullable=False),
    Column("relevance_score", Float, server_default=text("'0.5'")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    UniqueConstraint("node_id", "memory_entry_id"),
)


Table(
    "world_tree_snapshots",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("node_id", Integer, ForeignKey("world_tree_nodes.id"), nullable=False),
    Column("snapshot_type", Text, server_default=text("full")),
    Column("subtree_json", Text, server_default=text("{}")),
    Column("memory_count", Integer, server_default=text("'0'")),
    Column("version", Integer, server_default=text("'1'")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("expires_at", Text),
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

Index("idx_audit_entity", "entity_type", "entity_id")

Index("idx_audit_user", "user_id")

Index("idx_audit_action_time", "action", "created_at")

Index("idx_audit_records_type", "message_type")

Index("idx_audit_records_risk", "risk_level")

Index("idx_audit_records_time", "created_at")

Index("idx_chain_entity", "entity_type", "entity_id")

Index("idx_chain_action", "action")

Index("idx_chain_time", "performed_at")

Index("idx_corrections_audit", "audit_record_id")

Index("idx_corrections_status", "status")

Index("idx_corrections_severity", "severity")

Index("idx_blacklist_expires", "expires_at")

Index("idx_asr_task_id", "task_id")

Index("idx_admission_rep", "rep_id")

Index("idx_admission_status", "status")

Index("idx_qa_status", "status")

Index("idx_ask_role", "agent_role")

Index("idx_ask_entity", "entity_types")

Index("idx_cs_session", "session_id")

Index("idx_cs_status", "status")

Index("idx_cstep_session", "session_id")

Index("idx_notif_user", "user_id", "is_read")

Index("idx_notif_user_time", "user_id", "created_at")

Index("idx_customers_name", "name")

Index("idx_customers_hospital", "hospital")

Index("idx_interactions_customer", "customer_id")

Index("idx_interactions_time", "conducted_at")

Index("idx_opps_customer", "customer_id")

Index("idx_opps_stage", "stage")

Index("idx_opps_assigned", "assigned_to")

Index("idx_dec_cases_outcome", "outcome_score")

Index("idx_dec_cases_run", "pipeline_run_id")

Index("idx_causal_case", "case_id")

Index("idx_insights_type", "insight_type")

Index("idx_insights_confidence", "confidence")

Index("idx_cg_graph", "graph_id")

Index("idx_cg_decision", "decision_id")

Index("idx_cs_scenario", "scenario_id")

Index("idx_did_did", "did")

Index("idx_did_status", "status")

Index("idx_vc_issuer", "issuer_did")

Index("idx_vc_subject", "subject_did")

Index("idx_vc_type", "credential_type")

Index("idx_fed_contributor", "contributor_did")

Index("idx_fed_type", "contribution_type")

Index("idx_pb_did", "did")

Index("idx_dpal_did", "did")

Index("idx_dpal_type", "operation_type")

Index("idx_ebd_type", "event_type")

Index("idx_ebd_source", "source_end")

Index("idx_ebm_type", "event_type")

Index("idx_ebm_status", "status")

Index("idx_ebm_corr", "correlation_id")

Index("idx_edl_msg", "message_id")

Index("idx_edl_target", "target_end")

Index("idx_aet_task", "task_id")

Index("idx_aet_status", "status")

Index("idx_aet_session", "session_id")

Index("idx_mcp_name", "tool_name")

Index("idx_mcp_audit_tool", "tool_name")

Index("idx_mcp_audit_user", "user_id")

Index("idx_mcp_audit_at", "created_at")

Index("idx_ot_name", "template_name")

Index("idx_hcp_tier", "tier")

Index("idx_hcp_specialty", "specialty")

Index("idx_hcp_int_hcp", "hcp_id")

Index("idx_hcp_int_time", "conducted_at")

Index("idx_hcp_sim_hcp", "hcp_id")

Index("idx_kge_type", "entity_type")

Index("idx_kge_name", "name")

Index("idx_kgr_source", "source_entity_id")

Index("idx_kgr_target", "target_entity_id")

Index("idx_kgr_type", "relation_type")

Index("idx_kgq_hash", "query_hash")

Index("idx_intel_sources_type", "source_type")

Index("idx_intel_sources_active", "is_active")

Index("idx_intel_items_type", "item_type")

Index("idx_intel_items_status", "status")

Index("idx_intel_items_impact", "impact_level")

Index("idx_intel_items_time", "collected_at")

Index("idx_mdt_status", "status")

Index("idx_mdt_participant_session", "session_id")

Index("idx_mdt_opinions_session", "session_id")

Index("idx_async_mdt_decision", "decision_id")

Index("idx_async_mdt_contributor", "contributor_id")

Index("idx_memory_type", "memory_type")

Index("idx_memory_importance", "importance")

Index("idx_memory_accessed", "last_accessed")

Index("idx_mus_score", "utility_score")

Index("idx_mus_decay", "decay_rate")

Index("idx_mema_a", "memory_id_a")

Index("idx_mema_b", "memory_id_b")

Index("idx_mema_pair", "MIN(memory_id_a, memory_id_b)", "MAX(memory_id_a, memory_id_b)", unique=True)

Index("idx_em_agent", "agent_role")

Index("idx_em_source_sub", "source_sub")

Index("idx_br_report", "report_id")

Index("idx_am_item", "item_id")

Index("idx_am_cat", "category")

Index("idx_sci_item", "item_id")

Index("idx_ss_session", "session_id")

Index("idx_token_budget_user", "user_id", "model")

Index("idx_token_usage_user", "user_id", "model", "usage_date")

Index("idx_pcj_job", "job_id")

Index("idx_pcj_type", "compute_type")

Index("idx_fr_round", "round_id")

Index("idx_fr_type", "model_name")

Index("idx_ncl_log", "log_id")

Index("idx_ncl_type", "document_type")

Index("idx_route_priority", "priority")

Index("idx_route_logs_role", "assigned_role_id")

Index("idx_route_logs_time", "created_at")

Index("idx_route_stats_role", "role_id", unique=True)

Index("idx_soap_status", "status")

Index("idx_soap_priority", "priority")

Index("idx_board_tasks_board", "board_id", "status")

Index("idx_board_tasks_assignee", "assignee_id")

Index("idx_tm_category", "category")

Index("idx_tm_difficulty", "difficulty")

Index("idx_ts_user", "user_id")

Index("idx_ts_module", "module_id")

Index("idx_ta_user", "user_id")

Index("idx_ta_metric", "metric_name")

Index("idx_ts_script", "script_id")

Index("idx_ts_role", "source_agent_role")

Index("idx_tra_id", "analysis_id")

Index("idx_up_user", "user_id", unique=True)

Index("idx_ub_user", "user_id")

Index("idx_ub_action", "action_type")

Index("idx_ub_target", "target_type")

Index("idx_rec_user", "user_id")

Index("idx_rec_type", "rec_type")

Index("idx_wm_session", "session_id")

Index("idx_wm_expires", "expires_at")

Index("idx_em_event", "event_type")

Index("idx_em_outcome", "outcome")

Index("idx_em_time", "created_at")

Index("idx_tree_parent", "parent_id")

Index("idx_tree_path", "path")

Index("idx_tree_type", "node_type")

Index("idx_nml_node", "node_id")

Index("idx_nml_memory", "memory_entry_id")

Index("idx_snapshot_node", "node_id")
