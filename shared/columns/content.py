TABLE_COMPLIANCE_RULES_COLS = frozenset(
    {
        "id",
        "name",
        "category",
        "keyword",
        "max_value",
        "created_by",
        "created_at",
    }
)

TABLE_CONTENTS_COLS = frozenset(
    {
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
    }
)

TABLE_NOTIFICATIONS_COLS = frozenset(
    {
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
    }
)

TABLE_NOTIFICATION_TEMPLATES_COLS = frozenset(
    {
        "id",
        "name",
        "title_template",
        "body_template",
        "category",
        "created_at",
    }
)
