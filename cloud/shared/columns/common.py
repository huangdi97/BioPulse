TABLE_AGENT_EXECUTION_TASKS_COLS = [
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
]

TABLE_AGENT_MARKETPLACE_COLS = [
    "id",
    "item_id",
    "item_name",
    "item_type",
    "description",
    "agent_config",
    "category",
    "price_model",
    "rating",
    "download_count",
    "enabled",
    "publisher",
    "created_at",
    "updated_at",
]

TABLE_AGENT_PIPELINES_COLS = [
    "id",
    "name",
    "description",
    "is_active",
    "created_by",
    "created_at",
    "updated_at",
]

TABLE_AGENT_ROLES_COLS = [
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
]

TABLE_AGENT_SKILLS_COLS = [
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
]

TABLE_PIPELINE_RUNS_COLS = [
    "id",
    "pipeline_id",
    "user_input",
    "status",
    "result",
    "error",
    "started_at",
    "completed_at",
    "created_by",
]

TABLE_PIPELINE_STEP_RUNS_COLS = [
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
]

TABLE_PIPELINE_STEPS_COLS = [
    "id",
    "pipeline_id",
    "step_order",
    "agent_role_id",
    "input_mapping",
    "custom_prompt_override",
    "created_at",
]

TABLE_COLLABORATION_SESSIONS_COLS = [
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
]

TABLE_COLLABORATION_STEPS_COLS = [
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
]

TABLE_ORCHESTRATION_TEMPLATES_COLS = [
    "id",
    "template_name",
    "description",
    "steps",
    "version",
    "enabled",
    "created_by",
    "created_at",
    "updated_at",
]

TABLE_EVENT_BUS_DEFINITIONS_COLS = [
    "id",
    "event_type",
    "display_name",
    "description",
    "source_end",
    "target_ends",
    "schema_template",
    "priority",
    "enabled",
    "created_at",
]

TABLE_EVENT_BUS_MESSAGES_COLS = [
    "id",
    "message_id",
    "event_type",
    "source_end",
    "source_entity_type",
    "source_entity_id",
    "payload",
    "correlation_id",
    "priority",
    "status",
    "retry_count",
    "max_retries",
    "created_at",
    "delivered_at",
]

TABLE_EVENT_DELIVERY_LOG_COLS = [
    "id",
    "message_id",
    "target_end",
    "delivery_status",
    "attempt",
    "response_summary",
    "duration_ms",
    "error_message",
    "created_at",
]

TABLE_DECISION_CASES_COLS = [
    "id",
    "name",
    "pipeline_run_id",
    "description",
    "outcome",
    "outcome_score",
    "context",
    "tags",
    "is_active",
    "created_by",
    "created_at",
    "updated_at",
]

TABLE_TASK_BOARDS_COLS = [
    "id",
    "name",
    "description",
    "owner_id",
    "is_active",
    "created_at",
    "updated_at",
]

TABLE_BOARD_TASKS_COLS = [
    "id",
    "board_id",
    "title",
    "description",
    "status",
    "priority",
    "assignee_id",
    "due_date",
    "sort_order",
    "is_active",
    "created_by",
    "created_at",
    "updated_at",
]

TABLE_TEAMS_COLS = [
    "id",
    "name",
    "description",
    "is_active",
    "created_by",
    "created_at",
    "updated_at",
]

TABLE_MEMORY_ENTRIES_COLS = [
    "id",
    "title",
    "content",
    "memory_type",
    "source_type",
    "source_id",
    "importance",
    "context_tags",
    "embedding",
    "access_count",
    "last_accessed",
    "is_active",
    "created_by",
    "created_at",
    "updated_at",
]

TABLE_MEMORY_GATES_COLS = [
    "id",
    "name",
    "source_type",
    "importance_threshold",
    "ttl_days",
    "retention_policy",
    "is_active",
    "created_at",
]

TABLE_MEMORY_RECALL_LOG_COLS = [
    "id",
    "query_text",
    "memory_ids",
    "result_count",
    "context",
    "created_at",
]

TABLE_MEMORY_UTILITY_SCORES_COLS = [
    "id",
    "memory_entry_id",
    "utility_score",
    "access_frequency",
    "recency_score",
    "importance_score",
    "connectivity_score",
    "decay_rate",
    "last_utility_update",
    "created_at",
]

TABLE_NODE_MEMORY_LINKS_COLS = [
    "id",
    "node_id",
    "memory_entry_id",
    "relevance_score",
    "created_at",
]

TABLE_MEMORY_CONSOLIDATION_LOG_COLS = [
    "id",
    "consolidation_type",
    "source_table",
    "item_count",
    "items_promoted",
    "items_pruned",
    "items_superseded",
    "duration_ms",
    "status",
    "details",
    "created_at",
]

TABLE_SLEEP_CONSOLIDATION_LOGS_COLS = [
    "id",
    "consolidation_type",
    "source_entry_ids",
    "target_entry_id",
    "action_detail",
    "utility_before",
    "utility_after",
    "created_at",
]

TABLE_WORKING_MEMORY_COLS = [
    "id",
    "session_id",
    "slot_key",
    "slot_value",
    "slot_type",
    "ttl_seconds",
    "created_at",
    "expires_at",
]

TABLE_EPISODIC_MEMORY_COLS = [
    "id",
    "event_type",
    "title",
    "description",
    "context",
    "outcome",
    "valence",
    "intensity",
    "involved_agents",
    "related_entity_type",
    "related_entity_id",
    "is_consolidated",
    "created_by",
    "created_at",
]

TABLE_WORLD_TREE_NODES_COLS = [
    "id",
    "name",
    "description",
    "parent_id",
    "path",
    "level",
    "node_type",
    "sort_order",
    "metadata",
    "is_active",
    "created_by",
    "created_at",
    "updated_at",
]

TABLE_WORLD_TREE_SNAPSHOTS_COLS = [
    "id",
    "node_id",
    "snapshot_type",
    "subtree_json",
    "memory_count",
    "version",
    "created_at",
    "expires_at",
]

TABLE_MCP_TOOLS_COLS = [
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
]

TABLE_FEDERATED_ROUNDS_COLS = [
    "id",
    "round_id",
    "model_name",
    "round_number",
    "participant_count",
    "aggregation_method",
    "global_metrics",
    "status",
    "created_at",
    "completed_at",
]

TABLE_FEDERATED_NODES_COLS = [
    "id",
    "node_id",
    "node_name",
    "node_type",
    "organization",
    "status",
    "endpoint_url",
    "public_key",
    "data_summary",
    "last_heartbeat",
    "round_count",
    "total_samples",
    "reliability_score",
    "is_active",
    "registered_at",
    "updated_at",
]

TABLE_PRIVACY_BUDGETS_COLS = [
    "id",
    "did",
    "epsilon_total",
    "epsilon_spent",
    "epsilon_remaining",
    "query_count",
    "last_query_at",
    "reset_at",
    "created_at",
]

TABLE_DP_AUDIT_LOG_COLS = [
    "id",
    "did",
    "operation_type",
    "epsilon_consumed",
    "data_category",
    "row_count",
    "noise_level",
    "approved",
    "details",
    "created_at",
]

TABLE_PRIVACY_COMPUTE_JOBS_COLS = [
    "id",
    "job_id",
    "compute_type",
    "sensitivity_level",
    "data_summary",
    "selected_scheme",
    "status",
    "epsilon_used",
    "noise_level",
    "result_summary",
    "created_by",
    "created_at",
    "completed_at",
]
