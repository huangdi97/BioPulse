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
