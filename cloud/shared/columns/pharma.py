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

TABLE_NOTIFICATION_TEMPLATES_COLS = [
    "id",
    "name",
    "title_template",
    "body_template",
    "category",
    "created_at",
]
