TABLE_USERS_COLS = frozenset({
    "id", "username", "hashed_password", "role", "is_active", "created_at",
})

TABLE_API_TOKENS_COLS = frozenset({
    "id", "user_id", "token_hash", "name", "is_active", "created_at",
})

TABLE_COMPLIANCE_RULES_COLS = frozenset({
    "id", "name", "category", "keyword", "max_value", "created_by", "created_at",
})

TABLE_CONTENTS_COLS = frozenset({
    "id", "title", "body", "category", "tags", "status", "compliance_score",
    "created_by", "created_at", "updated_at",
})

TABLE_TEAMS_COLS = frozenset({
    "id", "name", "description", "is_active", "created_by", "created_at", "updated_at",
})

TABLE_USER_TEAM_COLS = frozenset({
    "id", "user_id", "team_id", "role", "created_at",
})

TABLE_AUDIT_LOGS_COLS = frozenset({
    "id", "user_id", "action", "entity_type", "entity_id", "detail",
    "source_end", "ip_address", "created_at",
})

TABLE_NOTIFICATION_TEMPLATES_COLS = frozenset({
    "id", "name", "title_template", "body_template", "category", "created_at",
})

TABLE_NOTIFICATIONS_COLS = frozenset({
    "id", "user_id", "template_id", "title", "body", "category",
    "ref_type", "ref_id", "context_json", "is_read", "read_at", "created_at",
})

TABLE_TASK_BOARDS_COLS = frozenset({
    "id", "name", "description", "owner_id", "is_active", "created_at", "updated_at",
})

TABLE_BOARD_TASKS_COLS = frozenset({
    "id", "board_id", "title", "description", "status", "priority",
    "assignee_id", "due_date", "sort_order", "is_active", "created_by",
    "created_at", "updated_at",
})

TABLE_CUSTOMERS_COLS = frozenset({
    "id", "name", "title", "hospital", "department", "specialty",
    "phone", "email", "tags", "status", "created_by", "created_at", "updated_at",
})

TABLE_CUSTOMER_INTERACTIONS_COLS = frozenset({
    "id", "customer_id", "type", "summary", "outcome", "conducted_by",
    "conducted_at", "created_at",
})

TABLE_SYSTEM_CONFIGS_COLS = frozenset({
    "id", "key", "value", "description", "updated_by", "updated_at",
})

TABLE_OPPORTUNITIES_COLS = frozenset({
    "id", "customer_id", "name", "description", "stage", "probability",
    "estimated_value", "actual_value", "assigned_to", "close_date", "notes",
    "is_active", "created_by", "created_at", "updated_at",
})

TABLE_MARKET_INTEL_SOURCES_COLS = frozenset({
    "id", "name", "source_type", "target_keywords", "is_active",
    "created_by", "created_at", "updated_at",
})

TABLE_MARKET_INTEL_ITEMS_COLS = frozenset({
    "id", "source_id", "title", "summary", "content", "url", "item_type",
    "relevance_tags", "impact_level", "status", "ai_analysis", "collected_at",
    "created_by", "created_at", "updated_at",
})

TABLE_AGENT_ROLES_COLS = frozenset({
    "id", "name", "role_type", "description", "system_prompt", "input_schema",
    "output_schema", "temperature", "max_tokens", "allowed_tools", "is_active",
    "created_by", "created_at", "updated_at",
})

TABLE_AGENT_PIPELINES_COLS = frozenset({
    "id", "name", "description", "is_active", "created_by", "created_at", "updated_at",
})

TABLE_PIPELINE_STEPS_COLS = frozenset({
    "id", "pipeline_id", "step_order", "agent_role_id", "input_mapping",
    "custom_prompt_override", "created_at",
})

TABLE_PIPELINE_RUNS_COLS = frozenset({
    "id", "pipeline_id", "user_input", "status", "result", "error",
    "started_at", "completed_at", "created_by",
})

TABLE_PIPELINE_STEP_RUNS_COLS = frozenset({
    "id", "run_id", "step_order", "agent_role_id", "agent_role_name",
    "input_data", "output_data", "ai_response_raw", "tokens_used",
    "started_at", "completed_at", "status",
})

TABLE_DECISION_CASES_COLS = frozenset({
    "id", "name", "pipeline_run_id", "description", "outcome", "outcome_score",
    "context", "tags", "is_active", "created_by", "created_at", "updated_at",
})

TABLE_CAUSAL_ANALYSES_COLS = frozenset({
    "id", "case_id", "analysis_type", "summary", "key_drivers", "causal_chain",
    "attribution_scores", "recommendations", "ai_response_raw", "tokens_used",
    "created_at",
})

TABLE_CROSS_CASE_INSIGHTS_COLS = frozenset({
    "id", "title", "insight_type", "summary", "detail", "evidence",
    "confidence", "applicability", "source_run_ids", "is_active",
    "created_by", "created_at", "updated_at",
})

TABLE_COMPLIANCE_AUDIT_RECORDS_COLS = frozenset({
    "id", "message_type", "content", "source_id", "score", "risk_level",
    "passed", "violations", "ai_analysis", "reviewed_by", "reviewed_at",
    "created_by", "created_at",
})

TABLE_AUDIT_CHAIN_ENTRIES_COLS = frozenset({
    "id", "entity_type", "entity_id", "action", "previous_hash", "current_hash",
    "payload", "metadata", "source", "created_by", "performed_at",
})

TABLE_TRAINING_CORRECTIONS_COLS = frozenset({
    "id", "audit_record_id", "title", "description", "category", "severity",
    "status", "assigned_to", "created_by", "created_at", "updated_at",
})

TABLE_MDT_SESSIONS_COLS = frozenset({
    "id", "title", "question", "context", "status", "consensus",
    "consensus_json", "round_count", "created_by", "created_at", "updated_at",
})

TABLE_MDT_PARTICIPANTS_COLS = frozenset({
    "id", "session_id", "agent_role_id", "role_name", "stance",
    "vote_weight", "created_at",
})

TABLE_MDT_OPINIONS_COLS = frozenset({
    "id", "session_id", "participant_id", "round_number", "opinion",
    "summary", "sentiment", "confidence", "key_points", "ai_response_raw",
    "tokens_used", "created_at",
})

TABLE_MEMORY_GATES_COLS = frozenset({
    "id", "name", "source_type", "importance_threshold", "ttl_days",
    "retention_policy", "is_active", "created_at",
})

TABLE_MEMORY_ENTRIES_COLS = frozenset({
    "id", "title", "content", "memory_type", "source_type", "source_id",
    "importance", "context_tags", "embedding", "access_count", "last_accessed",
    "is_active", "created_by", "created_at", "updated_at",
})

TABLE_MEMORY_RECALL_LOG_COLS = frozenset({
    "id", "query_text", "memory_ids", "result_count", "context", "created_at",
})

TABLE_WORLD_TREE_NODES_COLS = frozenset({
    "id", "name", "description", "parent_id", "path", "level", "node_type",
    "sort_order", "metadata", "is_active", "created_by", "created_at", "updated_at",
})

TABLE_NODE_MEMORY_LINKS_COLS = frozenset({
    "id", "node_id", "memory_entry_id", "relevance_score", "created_at",
})

TABLE_WORLD_TREE_SNAPSHOTS_COLS = frozenset({
    "id", "node_id", "snapshot_type", "subtree_json", "memory_count",
    "version", "created_at", "expires_at",
})

TABLE_ROUTE_RULES_COLS = frozenset({
    "id", "name", "priority", "condition_field", "condition_operator",
    "condition_value", "target_role_id", "fallback_role_id", "max_tokens",
    "temperature", "is_active", "created_by", "created_at", "updated_at",
})

TABLE_ROUTE_LOGS_COLS = frozenset({
    "id", "input_text", "matched_rule_id", "matched_rule_name",
    "assigned_role_id", "assigned_role_name", "confidence", "response_summary",
    "tokens_used", "latency_ms", "source", "created_by", "created_at",
})

TABLE_ROUTE_STATS_COLS = frozenset({
    "id", "role_id", "total_routed", "avg_confidence", "avg_tokens",
    "avg_latency_ms", "last_routed_at", "updated_at",
})

TABLE_HCP_PROFILES_COLS = frozenset({
    "id", "name", "title", "hospital", "department", "specialty", "city",
    "tier", "traits", "prescription_volume", "influence_score",
    "digital_engagement", "is_active", "created_by", "created_at", "updated_at",
})

TABLE_HCP_INTERACTIONS_COLS = frozenset({
    "id", "hcp_id", "interaction_type", "content", "response", "outcome",
    "strategy_used", "conducted_by", "conducted_at", "created_at",
})

TABLE_HCP_SIMULATIONS_COLS = frozenset({
    "id", "hcp_id", "scenario", "strategy", "expected_outcome", "confidence",
    "suggested_approach", "key_concerns", "recommended_topics", "risk_factors",
    "simulation_data", "status", "created_by", "created_at",
})

TABLE_TRAINING_MODULES_COLS = frozenset({
    "id", "title", "category", "difficulty", "content", "prerequisites",
    "passing_score", "estimated_minutes", "is_active", "created_by",
    "created_at", "updated_at",
})

TABLE_TRAINING_SESSIONS_COLS = frozenset({
    "id", "user_id", "module_id", "score", "passed", "time_spent_seconds",
    "answers", "feedback", "difficulty_used", "next_difficulty",
    "completed_at", "created_at",
})

TABLE_TRAINING_ATTRIBUTIONS_COLS = frozenset({
    "id", "user_id", "training_session_id", "metric_name", "metric_before",
    "metric_after", "change_pct", "attribution_score", "confidence",
    "analysis", "period_days", "created_at",
})

TABLE_SOAP_TEMPLATES_COLS = frozenset({
    "id", "name", "category", "description", "structure", "is_active",
    "created_by", "created_at", "updated_at",
})

TABLE_SOAP_DECISIONS_COLS = frozenset({
    "id", "title", "template_id", "subjective", "objective", "assessment",
    "plan", "status", "priority", "tags", "decision_summary", "decided_by",
    "decided_at", "is_active", "created_by", "created_at", "updated_at",
})

TABLE_ASYNC_MDT_OPINIONS_COLS = frozenset({
    "id", "decision_id", "contributor_id", "contributor_role", "opinion",
    "supporting_data", "stance", "confidence", "attachments", "is_final",
    "created_at", "updated_at",
})

TABLE_MEMORY_UTILITY_SCORES_COLS = frozenset({
    "id", "memory_entry_id", "utility_score", "access_frequency",
    "recency_score", "importance_score", "connectivity_score", "decay_rate",
    "last_utility_update", "created_at",
})

TABLE_SLEEP_CONSOLIDATION_LOGS_COLS = frozenset({
    "id", "consolidation_type", "source_entry_ids", "target_entry_id",
    "action_detail", "utility_before", "utility_after", "created_at",
})

TABLE_WORKING_MEMORY_COLS = frozenset({
    "id", "session_id", "slot_key", "slot_value", "slot_type",
    "ttl_seconds", "created_at", "expires_at",
})

TABLE_EPISODIC_MEMORY_COLS = frozenset({
    "id", "event_type", "title", "description", "context", "outcome",
    "valence", "intensity", "involved_agents", "related_entity_type",
    "related_entity_id", "is_consolidated", "created_by", "created_at",
})

TABLE_DID_REGISTRY_COLS = frozenset({
    "id", "did", "entity_type", "entity_id", "public_key", "status",
    "metadata", "created_by", "created_at", "updated_at",
})

TABLE_VC_CREDENTIALS_COLS = frozenset({
    "id", "vc_id", "issuer_did", "subject_did", "credential_type", "claims",
    "issuance_date", "expiration_date", "proof", "status", "revoked_at",
    "created_at",
})

TABLE_FED_AUDIT_CONTRIBUTIONS_COLS = frozenset({
    "id", "contributor_did", "contribution_type", "payload_hash",
    "payload_summary", "weight", "verified", "verified_by", "audit_chain_hash",
    "created_at",
})

TABLE_PRIVACY_BUDGETS_COLS = frozenset({
    "id", "did", "epsilon_total", "epsilon_spent", "epsilon_remaining",
    "query_count", "last_query_at", "reset_at", "created_at",
})

TABLE_DATA_MASKING_RULES_COLS = frozenset({
    "id", "rule_name", "field_pattern", "masking_type", "masking_config",
    "applies_to", "enabled", "created_by", "created_at", "updated_at",
})

TABLE_DP_AUDIT_LOG_COLS = frozenset({
    "id", "did", "operation_type", "epsilon_consumed", "data_category",
    "row_count", "noise_level", "approved", "details", "created_at",
})

TABLE_KG_ENTITIES_COLS = frozenset({
    "id", "entity_id", "entity_type", "name", "aliases", "properties",
    "source_table", "source_row_id", "status", "confidence", "created_by",
    "created_at", "updated_at",
})

TABLE_KG_RELATIONS_COLS = frozenset({
    "id", "source_entity_id", "target_entity_id", "relation_type", "weight",
    "properties", "direction", "confidence", "source", "created_at",
})

TABLE_KG_SEARCH_CACHE_COLS = frozenset({
    "id", "query_hash", "query_text", "result_summary", "result_count",
    "cache_ttl", "created_at",
})

TABLE_USER_PROFILES_COLS = frozenset({
    "id", "user_id", "persona_type", "specialization", "experience_level",
    "preferred_content_types", "custom_tags", "embedding", "updated_at",
    "created_at",
})

TABLE_USER_BEHAVIORS_COLS = frozenset({
    "id", "user_id", "action_type", "target_type", "target_id", "metadata",
    "session_id", "duration_seconds", "created_at",
})

TABLE_RECOMMENDATIONS_COLS = frozenset({
    "id", "user_id", "rec_type", "rec_target_id", "rec_title", "rec_reason",
    "score", "strategy_name", "clicked", "dismissed", "created_at",
})

TABLE_AGENT_SKILLS_COLS = frozenset({
    "id", "skill_name", "agent_role", "description", "entity_types",
    "capabilities", "confidence", "priority", "enabled", "created_at",
    "updated_at",
})

TABLE_COLLABORATION_SESSIONS_COLS = frozenset({
    "id", "session_id", "task_description", "source_entity_id",
    "source_agent_role", "orchestrator_agent", "status", "involved_agents",
    "routing_strategy", "total_steps", "completed_steps", "started_at",
    "completed_at", "result_summary",
})

TABLE_COLLABORATION_STEPS_COLS = frozenset({
    "id", "session_id", "step_order", "agent_role", "action_type",
    "input_summary", "output_summary", "entity_id", "status", "started_at",
    "completed_at", "duration_seconds", "metadata",
})

TABLE_EVENT_BUS_DEFINITIONS_COLS = frozenset({
    "id", "event_type", "display_name", "description", "source_end",
    "target_ends", "schema_template", "priority", "enabled", "created_at",
})

TABLE_EVENT_BUS_MESSAGES_COLS = frozenset({
    "id", "message_id", "event_type", "source_end", "source_entity_type",
    "source_entity_id", "payload", "correlation_id", "priority", "status",
    "retry_count", "max_retries", "created_at", "delivered_at",
})

TABLE_EVENT_DELIVERY_LOG_COLS = frozenset({
    "id", "message_id", "target_end", "delivery_status", "attempt",
    "response_summary", "duration_ms", "error_message", "created_at",
})

TABLE_MEMORY_CONSOLIDATION_LOG_COLS = frozenset({
    "id", "consolidation_type", "source_table", "item_count",
    "items_promoted", "items_pruned", "items_superseded", "duration_ms",
    "status", "details", "created_at",
})

TABLE_AGENT_EXECUTION_TASKS_COLS = frozenset({
    "id", "task_id", "source", "session_id", "agent_role", "action_type",
    "input_data", "output_data", "status", "retry_count", "max_retries",
    "result_verified", "verification_detail", "requires_human_approval",
    "assigned_to", "created_at", "completed_at", "duration_ms",
})

TABLE_MCP_TOOLS_COLS = frozenset({
    "id", "tool_name", "description", "tool_version", "endpoint_url",
    "input_schema", "output_schema", "auth_required", "enabled",
    "created_by", "created_at", "updated_at",
})

TABLE_MCP_AUDIT_LOG_COLS = frozenset({
    "id", "tool_name", "user_id", "user_role", "params", "result",
    "granted", "reason", "created_at",
})

TABLE_ORCHESTRATION_TEMPLATES_COLS = frozenset({
    "id", "template_name", "description", "steps", "version", "enabled",
    "created_by", "created_at", "updated_at",
})

TABLE_CAUSAL_GRAPHS_COLS = frozenset({
    "id", "graph_id", "decision_id", "graph_data", "summary",
    "node_count", "edge_count", "created_by", "created_at",
})

TABLE_COUNTERFACTUAL_SCENARIOS_COLS = frozenset({
    "id", "scenario_id", "strategy_id", "base_description",
    "variable_changes", "predicted_outcome", "confidence",
    "created_by", "created_at",
})

TABLE_PRIVACY_COMPUTE_JOBS_COLS = frozenset({
    "id", "job_id", "compute_type", "sensitivity_level", "data_summary",
    "selected_scheme", "status", "epsilon_used", "noise_level",
    "result_summary", "created_by", "created_at", "completed_at",
})

TABLE_FEDERATED_ROUNDS_COLS = frozenset({
    "id", "round_id", "model_name", "round_number", "participant_count",
    "aggregation_method", "global_metrics", "status", "created_at",
    "completed_at",
})

TABLE_NMPA_COMPLIANCE_LOGS_COLS = frozenset({
    "id", "log_id", "document_type", "content_summary", "check_result",
    "violations_found", "violation_details", "human_review_required",
    "human_reviewer", "human_reviewed_at", "created_by", "created_at",
})

TABLE_TRAINING_SCRIPTS_COLS = frozenset({
    "id", "script_id", "script_name", "source_agent_role",
    "source_collaboration_id", "description", "steps", "difficulty",
    "target_roles", "score", "created_by", "created_at", "updated_at",
})

TABLE_TRAINING_ROI_ANALYSIS_COLS = frozenset({
    "id", "analysis_id", "period_start", "period_end", "training_hours",
    "participants", "behavior_change_score", "sales_impact", "cost_savings",
    "roi", "metadata", "created_at",
})

TABLE_EFFECT_METRICS_COLS = frozenset({
    "id", "metric_id", "agent_role", "metric_type", "metric_value",
    "metric_unit", "source_table", "source_row_id", "period_start",
    "period_end", "created_at",
})

TABLE_BENCHMARK_REPORTS_COLS = frozenset({
    "id", "report_id", "report_name", "report_type", "data_source",
    "summary", "metrics", "period", "created_at",
})

TABLE_AGENT_MARKETPLACE_COLS = frozenset({
    "id", "item_id", "item_name", "item_type", "description", "agent_config",
    "category", "price_model", "rating", "download_count", "enabled",
    "publisher", "created_at", "updated_at",
})

TABLE_SUPPLY_CHAIN_ITEMS_COLS = frozenset({
    "id", "item_id", "item_name", "sku", "category", "current_stock",
    "min_stock", "max_stock", "unit_price", "supplier", "status",
    "created_at", "updated_at",
})

TABLE_SENSOR_SESSIONS_COLS = frozenset({
    "id", "session_id", "session_name", "event_type", "location",
    "start_time", "end_time", "data_summary", "status", "created_at",
})

TABLE_ASSISTANT_HCP_COLS = frozenset({
    "id", "name", "hospital", "department", "title", "specialty",
    "phone", "wechat", "email", "level", "is_active", "created_by",
    "created_at", "updated_at",
})

TABLE_VISIT_RECORD_COLS = frozenset({
    "id", "hcp_id", "visit_type", "summary", "detail", "feedback",
    "next_action", "mood", "is_completed", "visit_date", "created_by",
    "created_at",
})

TABLE_TASK_COLS = frozenset({
    "id", "hcp_id", "title", "description", "priority", "status",
    "due_date", "created_by", "created_at",
})

TABLE_HEALTH_RADAR_COLS = frozenset({
    "id", "patient_name", "age", "gender", "diagnosis", "risk_factors",
    "medication_history", "score", "assessment_date", "notes", "is_active",
    "created_by", "created_at", "updated_at",
})

TABLE_SURGERY_REMINDER_COLS = frozenset({
    "id", "patient_name", "surgery_type", "surgery_date", "hospital",
    "department", "surgeon_name", "pre_op_notes", "post_op_notes",
    "status", "reminder_before", "last_notified_at", "notification_status",
    "is_active", "created_by", "created_at", "updated_at",
})

TABLE_KNOWLEDGE_BASE_COLS = frozenset({
    "id", "title", "category", "content", "tags", "source", "difficulty",
    "is_active", "created_by", "created_at", "updated_at",
})

TABLE_HCP_LOCATION_COLS = frozenset({
    "id", "hcp_id", "address", "latitude", "longitude", "is_primary",
    "notes", "is_active", "created_by", "created_at", "updated_at",
})

TABLE_SYNC_QUEUE_COLS = frozenset({
    "id", "client_id", "action", "entity_type", "entity_id", "payload",
    "status", "client_created_at", "synced_at", "created_by", "created_at",
})

TABLE_MEDIA_FILE_COLS = frozenset({
    "id", "file_type", "original_name", "storage_path", "mime_type",
    "file_size", "transcript", "analysis_result", "is_active",
    "created_by", "created_at",
})

TABLE_OPPORTUNITY_COLS = frozenset({
    "id", "name", "hcp_name", "hospital", "department", "product",
    "estimated_value", "stage", "probability", "expected_close_date",
    "notes", "is_active", "heat_score", "created_by", "created_at",
    "updated_at",
})

TABLE_CONTACT_RECORD_COLS = frozenset({
    "id", "opportunity_id", "contact_type", "summary", "detail",
    "contact_date", "created_by", "created_at",
})

TABLE_BIDDING_INFO_COLS = frozenset({
    "id", "title", "hospital", "department", "product_category", "budget",
    "publish_date", "deadline", "status", "source_url", "summary",
    "analysis", "notes", "is_active", "created_by", "created_at",
    "updated_at",
})

TABLE_RESEARCH_TRAIL_COLS = frozenset({
    "id", "hcp_name", "topic", "paper_title", "authors", "journal",
    "pub_date", "pubmed_id", "url", "summary", "relevance", "is_active",
    "created_by", "created_at", "updated_at",
})

TABLE_USER_BOOKMARK_COLS = frozenset({
    "id", "entity_type", "entity_id", "title", "notes", "created_by",
    "created_at",
})

TABLE_PAPER_INTEGRITY_COLS = frozenset({
    "id", "pubmed_id", "doi", "title", "integrity_score",
    "retraction_warning", "concerns", "flags", "checked_at", "check_count",
    "is_active", "created_by", "created_at", "updated_at",
})

TABLE_TREND_ANALYSIS_COLS = frozenset({
    "id", "topic", "analysis_type", "period", "data_summary", "result",
    "confidence", "analyzed_at", "created_by", "created_at",
})

TABLE_BIDDING_AGENT_CONFIG_COLS = frozenset({
    "id", "name", "keywords", "regions", "auto_parse", "auto_notify",
    "notify_to", "schedule_interval", "is_active", "created_by",
    "created_at", "updated_at",
})

TABLE_BIDDING_AGENT_LOG_COLS = frozenset({
    "id", "config_id", "run_status", "items_found", "items_parsed",
    "error_message", "started_at", "completed_at", "created_at",
})

TABLE_SCHEDULE_COLS = frozenset({
    "id", "title", "description", "event_type", "start_time", "end_time",
    "location", "is_completed", "created_by", "created_at", "updated_at",
})

TABLE_MEETING_NOTE_COLS = frozenset({
    "id", "schedule_id", "title", "content", "participants",
    "action_items", "created_by", "created_at", "updated_at",
})

TABLE_CONTENT_LIBRARY_COLS = frozenset({
    "id", "title", "content_type", "category", "content", "tags",
    "summary", "file_reference", "is_active", "created_by", "created_at",
    "updated_at",
})

TABLE_STRATEGY_SIMULATION_COLS = frozenset({
    "id", "hcp_name", "visit_date", "goal", "approach", "talking_points",
    "expected_outcome", "actual_outcome", "reflection", "effectiveness",
    "status", "is_active", "created_by", "created_at", "updated_at",
})

TABLE_SALES_ASSISTANT_HCP_COLS = frozenset({
    "id", "name", "hospital", "department", "specialty", "tier", "city",
    "phone", "email", "wechat", "is_active", "created_by", "created_at",
    "updated_at",
})

TABLE_PRODUCT_COLS = frozenset({
    "id", "name", "category", "specification", "company", "is_active",
    "created_by", "created_at", "updated_at",
})

TABLE_HCP_PRODUCT_RELATION_COLS = frozenset({
    "id", "hcp_id", "product_id", "relation_type", "strength", "notes",
    "is_active", "created_by", "created_at", "updated_at",
})

TABLE_VISIT_HCP_COLS = frozenset({
    "id", "schedule_id", "hcp_id", "products_discussed", "hcp_feedback",
    "follow_up_required", "created_at",
})

TABLE_COACHING_PROMPT_COLS = frozenset({
    "id", "trigger_type", "trigger_keywords", "scenario",
    "prompt_template", "priority", "category", "is_active", "created_by",
    "created_at", "updated_at",
})

TABLE_COACHING_SESSION_COLS = frozenset({
    "id", "schedule_id", "hcp_name", "current_scenario", "status",
    "started_at", "ended_at", "notes", "created_by", "created_at",
})

TABLE_ANOMALY_RULE_COLS = frozenset({
    "id", "rule_name", "metric", "operator", "threshold", "severity",
    "description", "is_active", "created_by", "created_at", "updated_at",
})

TABLE_ANOMALY_ALERT_COLS = frozenset({
    "id", "rule_id", "entity_type", "entity_id", "detected_value",
    "severity", "message", "status", "detected_at", "resolved_at",
    "resolved_by", "created_at",
})

TABLE_TRAINING_MODULE_COLS = frozenset({
    "id", "title", "description", "category", "content", "difficulty",
    "is_active", "created_by", "created_at", "updated_at",
})

TABLE_COACH_SESSION_COLS = frozenset({
    "id", "module_id", "trainee_name", "score", "feedback", "strengths",
    "improvements", "session_date", "created_by", "created_at",
    "session_type", "scenario_id", "dialogue_log", "role",
    "compliance_violations", "auto_assessment", "reflection_report",
})

TABLE_COACH_SCENARIO_COLS = frozenset({
    "id", "title", "role_setting", "goal", "difficulty", "category",
    "content", "tips", "is_active", "created_by", "created_at",
    "updated_at",
})

TABLE_EDUCATION_ASSESSMENT_COLS = frozenset({
    "id", "trainee_name", "assessment_date", "current_level",
    "target_level", "strengths", "weaknesses", "recommended_modules",
    "notes", "is_active", "created_by", "created_at", "updated_at",
})
