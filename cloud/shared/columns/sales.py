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
