TABLE_HCP_INTERACTIONS_COLS = frozenset(
    {
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
    }
)

TABLE_HCP_PROFILES_COLS = frozenset(
    {
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
    }
)

TABLE_HCP_SIMULATIONS_COLS = frozenset(
    {
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
    }
)
