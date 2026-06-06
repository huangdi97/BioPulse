TABLE_CAUSAL_ANALYSES_COLS = frozenset(
    {
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
    }
)

TABLE_CAUSAL_GRAPHS_COLS = frozenset(
    {
        "id",
        "graph_id",
        "decision_id",
        "graph_data",
        "summary",
        "node_count",
        "edge_count",
        "created_by",
        "created_at",
    }
)

TABLE_COUNTERFACTUAL_SCENARIOS_COLS = frozenset(
    {
        "id",
        "scenario_id",
        "strategy_id",
        "base_description",
        "variable_changes",
        "predicted_outcome",
        "confidence",
        "created_by",
        "created_at",
    }
)

TABLE_CROSS_CASE_INSIGHTS_COLS = frozenset(
    {
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
    }
)

TABLE_DECISION_CASES_COLS = frozenset(
    {
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
    }
)
