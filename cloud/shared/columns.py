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

TABLE_ASYNC_MDT_OPINIONS_COLS = [
    "id",
    "decision_id",
    "contributor_id",
    "contributor_role",
    "opinion",
    "supporting_data",
    "stance",
    "confidence",
    "attachments",
    "is_final",
    "created_at",
    "updated_at",
]

TABLE_AUDIT_CHAIN_ENTRIES_COLS = [
    "id",
    "entity_type",
    "entity_id",
    "action",
    "previous_hash",
    "current_hash",
    "payload",
    "metadata",
    "source",
    "created_by",
    "performed_at",
]

TABLE_AUDIT_LOGS_COLS = [
    "id",
    "user_id",
    "action",
    "entity_type",
    "entity_id",
    "detail",
    "source_end",
    "ip_address",
    "created_at",
]

TABLE_BENCHMARK_REPORTS_COLS = [
    "id",
    "report_id",
    "report_name",
    "report_type",
    "data_source",
    "summary",
    "metrics",
    "period",
    "created_at",
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

TABLE_CAUSAL_ANALYSES_COLS = [
    "id",
    "case_id",
    "analysis_type",
    "summary",
    "key_drivers",
    "causal_chain",
    "attribution_scores",
    "recommendations",
    "ai_response_raw",
    "tokens_used",
    "created_at",
]

TABLE_CAUSAL_GRAPHS_COLS = [
    "id",
    "graph_id",
    "decision_id",
    "graph_data",
    "summary",
    "node_count",
    "edge_count",
    "created_by",
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

TABLE_COMPLIANCE_AUDIT_RECORDS_COLS = [
    "id",
    "message_type",
    "content",
    "source_id",
    "score",
    "risk_level",
    "passed",
    "violations",
    "ai_analysis",
    "reviewed_by",
    "reviewed_at",
    "created_by",
    "created_at",
]

TABLE_COMPLIANCE_RULES_COLS = [
    "id",
    "name",
    "category",
    "keyword",
    "max_value",
    "created_by",
    "created_at",
]

TABLE_CONTENTS_COLS = [
    "id",
    "title",
    "body",
    "category",
    "tags",
    "status",
    "compliance_score",
    "created_by",
    "created_at",
    "updated_at",
]

TABLE_COUNTERFACTUAL_SCENARIOS_COLS = [
    "id",
    "scenario_id",
    "strategy_id",
    "base_description",
    "variable_changes",
    "predicted_outcome",
    "confidence",
    "created_by",
    "created_at",
]

TABLE_CROSS_CASE_INSIGHTS_COLS = [
    "id",
    "title",
    "insight_type",
    "summary",
    "detail",
    "evidence",
    "confidence",
    "applicability",
    "source_run_ids",
    "is_active",
    "created_by",
    "created_at",
    "updated_at",
]

TABLE_CUSTOMER_INTERACTIONS_COLS = [
    "id",
    "customer_id",
    "type",
    "summary",
    "outcome",
    "conducted_by",
    "conducted_at",
    "created_at",
]

TABLE_CUSTOMERS_COLS = [
    "id",
    "name",
    "title",
    "hospital",
    "department",
    "specialty",
    "phone",
    "email",
    "tags",
    "status",
    "created_by",
    "created_at",
    "updated_at",
]

TABLE_DATA_MASKING_RULES_COLS = [
    "id",
    "rule_name",
    "field_pattern",
    "masking_type",
    "masking_config",
    "applies_to",
    "enabled",
    "created_by",
    "created_at",
    "updated_at",
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

TABLE_DID_REGISTRY_COLS = [
    "id",
    "did",
    "entity_type",
    "entity_id",
    "public_key",
    "status",
    "metadata",
    "created_by",
    "created_at",
    "updated_at",
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

TABLE_EFFECT_METRICS_COLS = [
    "id",
    "metric_id",
    "agent_role",
    "metric_type",
    "metric_value",
    "metric_unit",
    "source_table",
    "source_row_id",
    "source_sub",
    "period_start",
    "period_end",
    "created_at",
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

TABLE_FED_AUDIT_CONTRIBUTIONS_COLS = [
    "id",
    "contributor_did",
    "contribution_type",
    "payload_hash",
    "payload_summary",
    "weight",
    "verified",
    "verified_by",
    "audit_chain_hash",
    "created_at",
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

TABLE_AUDIT_CHAIN_BLOCKS_COLS = [
    "id",
    "block_hash",
    "prev_block_hash",
    "block_data",
    "block_type",
    "created_by",
    "node_id",
    "timestamp",
]

TABLE_HCP_INTERACTIONS_COLS = [
    "id",
    "hcp_id",
    "interaction_type",
    "content",
    "response",
    "outcome",
    "strategy_used",
    "conducted_by",
    "conducted_at",
    "created_at",
]

TABLE_HCP_PROFILES_COLS = [
    "id",
    "name",
    "title",
    "hospital",
    "department",
    "specialty",
    "city",
    "tier",
    "traits",
    "prescription_volume",
    "influence_score",
    "digital_engagement",
    "is_active",
    "created_by",
    "created_at",
    "updated_at",
]

TABLE_HCP_SIMULATIONS_COLS = [
    "id",
    "hcp_id",
    "scenario",
    "strategy",
    "expected_outcome",
    "confidence",
    "suggested_approach",
    "key_concerns",
    "recommended_topics",
    "risk_factors",
    "simulation_data",
    "status",
    "created_by",
    "created_at",
]

TABLE_KG_ENTITIES_COLS = [
    "id",
    "entity_id",
    "entity_type",
    "name",
    "aliases",
    "properties",
    "source_table",
    "source_row_id",
    "status",
    "confidence",
    "created_by",
    "created_at",
    "updated_at",
]

TABLE_KG_RELATIONS_COLS = [
    "id",
    "source_entity_id",
    "target_entity_id",
    "relation_type",
    "weight",
    "properties",
    "direction",
    "confidence",
    "source",
    "created_at",
]

TABLE_KG_SEARCH_CACHE_COLS = [
    "id",
    "query_hash",
    "query_text",
    "result_summary",
    "result_count",
    "cache_ttl",
    "created_at",
]

TABLE_MARKET_INTEL_ITEMS_COLS = [
    "id",
    "source_id",
    "title",
    "summary",
    "content",
    "url",
    "item_type",
    "relevance_tags",
    "impact_level",
    "status",
    "ai_analysis",
    "collected_at",
    "created_by",
    "created_at",
    "updated_at",
]

TABLE_MARKET_INTEL_SOURCES_COLS = [
    "id",
    "name",
    "source_type",
    "target_keywords",
    "is_active",
    "created_by",
    "created_at",
    "updated_at",
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

TABLE_MDT_OPINIONS_COLS = [
    "id",
    "session_id",
    "participant_id",
    "round_number",
    "opinion",
    "summary",
    "sentiment",
    "confidence",
    "key_points",
    "ai_response_raw",
    "tokens_used",
    "created_at",
]

TABLE_MDT_PARTICIPANTS_COLS = [
    "id",
    "session_id",
    "agent_role_id",
    "role_name",
    "stance",
    "vote_weight",
    "created_at",
]

TABLE_MDT_SESSIONS_COLS = [
    "id",
    "title",
    "question",
    "context",
    "status",
    "consensus",
    "consensus_json",
    "round_count",
    "created_by",
    "created_at",
    "updated_at",
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

TABLE_NMPA_COMPLIANCE_LOGS_COLS = [
    "id",
    "log_id",
    "document_type",
    "content_summary",
    "check_result",
    "violations_found",
    "violation_details",
    "human_review_required",
    "human_reviewer",
    "human_reviewed_at",
    "created_by",
    "created_at",
]

TABLE_NODE_MEMORY_LINKS_COLS = [
    "id",
    "node_id",
    "memory_entry_id",
    "relevance_score",
    "created_at",
]

TABLE_NOTIFICATION_TEMPLATES_COLS = [
    "id",
    "name",
    "title_template",
    "body_template",
    "category",
    "created_at",
]

TABLE_NOTIFICATIONS_COLS = [
    "id",
    "user_id",
    "template_id",
    "title",
    "body",
    "category",
    "ref_type",
    "ref_id",
    "context_json",
    "is_read",
    "read_at",
    "created_at",
]

TABLE_OPPORTUNITIES_COLS = [
    "id",
    "customer_id",
    "name",
    "description",
    "stage",
    "probability",
    "estimated_value",
    "actual_value",
    "assigned_to",
    "close_date",
    "notes",
    "is_active",
    "created_by",
    "created_at",
    "updated_at",
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

TABLE_RECOMMENDATIONS_COLS = [
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
]

TABLE_ROUTE_LOGS_COLS = [
    "id",
    "input_text",
    "matched_rule_id",
    "matched_rule_name",
    "assigned_role_id",
    "assigned_role_name",
    "confidence",
    "response_summary",
    "tokens_used",
    "latency_ms",
    "source",
    "created_by",
    "created_at",
]

TABLE_ROUTE_RULES_COLS = [
    "id",
    "name",
    "priority",
    "condition_field",
    "condition_operator",
    "condition_value",
    "target_role_id",
    "fallback_role_id",
    "max_tokens",
    "temperature",
    "is_active",
    "created_by",
    "created_at",
    "updated_at",
]

TABLE_ROUTE_STATS_COLS = [
    "id",
    "role_id",
    "total_routed",
    "avg_confidence",
    "avg_tokens",
    "avg_latency_ms",
    "last_routed_at",
    "updated_at",
]

TABLE_SENSOR_SESSIONS_COLS = [
    "id",
    "session_id",
    "session_name",
    "event_type",
    "location",
    "start_time",
    "end_time",
    "data_summary",
    "status",
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

TABLE_SOAP_DECISIONS_COLS = [
    "id",
    "title",
    "template_id",
    "subjective",
    "objective",
    "assessment",
    "plan",
    "status",
    "priority",
    "tags",
    "decision_summary",
    "decided_by",
    "decided_at",
    "is_active",
    "created_by",
    "created_at",
    "updated_at",
]

TABLE_SOAP_TEMPLATES_COLS = [
    "id",
    "name",
    "category",
    "description",
    "structure",
    "is_active",
    "created_by",
    "created_at",
    "updated_at",
]

TABLE_SUPPLY_CHAIN_ITEMS_COLS = [
    "id",
    "item_id",
    "item_name",
    "sku",
    "category",
    "current_stock",
    "min_stock",
    "max_stock",
    "unit_price",
    "supplier",
    "status",
    "created_at",
    "updated_at",
]

TABLE_SYSTEM_CONFIGS_COLS = [
    "id",
    "key",
    "value",
    "description",
    "updated_by",
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

TABLE_TEAMS_COLS = [
    "id",
    "name",
    "description",
    "is_active",
    "created_by",
    "created_at",
    "updated_at",
]

TABLE_TRAINING_ATTRIBUTIONS_COLS = [
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
]

TABLE_TRAINING_CORRECTIONS_COLS = [
    "id",
    "audit_record_id",
    "title",
    "description",
    "category",
    "severity",
    "status",
    "assigned_to",
    "created_by",
    "created_at",
    "updated_at",
]

TABLE_TRAINING_MODULES_COLS = [
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
]

TABLE_TRAINING_ROI_ANALYSIS_COLS = [
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
]

TABLE_TRAINING_SCRIPTS_COLS = [
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
]

TABLE_TRAINING_SESSIONS_COLS = [
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
]

TABLE_USER_BEHAVIORS_COLS = [
    "id",
    "user_id",
    "action_type",
    "target_type",
    "target_id",
    "metadata",
    "session_id",
    "duration_seconds",
    "created_at",
]

TABLE_USER_PROFILES_COLS = [
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
]

TABLE_USER_TEAM_COLS = ["id", "user_id", "team_id", "role", "created_at"]

TABLE_USERS_COLS = [
    "id",
    "username",
    "hashed_password",
    "role",
    "is_active",
    "created_at",
]

TABLE_VC_CREDENTIALS_COLS = [
    "id",
    "vc_id",
    "issuer_did",
    "subject_did",
    "credential_type",
    "claims",
    "issuance_date",
    "expiration_date",
    "proof",
    "status",
    "revoked_at",
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
