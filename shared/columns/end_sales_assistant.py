"""End sales assistant module."""

TABLE_BIDDING_AGENT_CONFIG_COLS = frozenset(
    {
        "id",
        "name",
        "keywords",
        "regions",
        "auto_parse",
        "auto_notify",
        "notify_to",
        "schedule_interval",
        "is_active",
        "created_by",
        "created_at",
        "updated_at",
    }
)

TABLE_BIDDING_AGENT_LOG_COLS = frozenset(
    {
        "id",
        "config_id",
        "run_status",
        "items_found",
        "items_parsed",
        "error_message",
        "started_at",
        "completed_at",
        "created_at",
    }
)

TABLE_BIDDING_INFO_COLS = frozenset(
    {
        "id",
        "title",
        "hospital",
        "department",
        "product_category",
        "budget",
        "publish_date",
        "deadline",
        "status",
        "source_url",
        "summary",
        "analysis",
        "notes",
        "is_active",
        "created_by",
        "created_at",
        "updated_at",
    }
)

TABLE_CONTACT_RECORD_COLS = frozenset(
    {
        "id",
        "opportunity_id",
        "contact_type",
        "summary",
        "detail",
        "contact_date",
        "created_by",
        "created_at",
    }
)

TABLE_CONTENT_LIBRARY_COLS = frozenset(
    {
        "id",
        "title",
        "content_type",
        "category",
        "content",
        "tags",
        "summary",
        "file_reference",
        "is_active",
        "created_by",
        "created_at",
        "updated_at",
    }
)

TABLE_HCP_PRODUCT_RELATION_COLS = frozenset(
    {
        "id",
        "hcp_id",
        "product_id",
        "relation_type",
        "strength",
        "notes",
        "is_active",
        "created_by",
        "created_at",
        "updated_at",
    }
)

TABLE_MEETING_NOTE_COLS = frozenset(
    {
        "id",
        "schedule_id",
        "title",
        "content",
        "participants",
        "action_items",
        "created_by",
        "created_at",
        "updated_at",
    }
)

TABLE_OPPORTUNITY_COLS = frozenset(
    {
        "id",
        "name",
        "hcp_name",
        "hospital",
        "department",
        "product",
        "estimated_value",
        "stage",
        "probability",
        "expected_close_date",
        "notes",
        "is_active",
        "heat_score",
        "created_by",
        "created_at",
        "updated_at",
    }
)

TABLE_PRODUCT_COLS = frozenset(
    {
        "id",
        "name",
        "category",
        "specification",
        "company",
        "is_active",
        "created_by",
        "created_at",
        "updated_at",
    }
)

TABLE_SALES_ASSISTANT_HCP_COLS = frozenset(
    {
        "id",
        "name",
        "hospital",
        "department",
        "specialty",
        "tier",
        "city",
        "phone",
        "email",
        "wechat",
        "is_active",
        "created_by",
        "created_at",
        "updated_at",
    }
)

TABLE_SCHEDULE_COLS = frozenset(
    {
        "id",
        "title",
        "description",
        "event_type",
        "start_time",
        "end_time",
        "location",
        "is_completed",
        "created_by",
        "created_at",
        "updated_at",
    }
)

TABLE_STRATEGY_SIMULATION_COLS = frozenset(
    {
        "id",
        "hcp_name",
        "visit_date",
        "goal",
        "approach",
        "talking_points",
        "expected_outcome",
        "actual_outcome",
        "reflection",
        "effectiveness",
        "status",
        "is_active",
        "created_by",
        "created_at",
        "updated_at",
    }
)

TABLE_VISIT_HCP_COLS = frozenset(
    {
        "id",
        "schedule_id",
        "hcp_id",
        "products_discussed",
        "hcp_feedback",
        "follow_up_required",
        "created_at",
    }
)
