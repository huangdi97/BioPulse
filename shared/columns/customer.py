TABLE_CUSTOMERS_COLS = frozenset(
    {
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
    }
)

TABLE_CUSTOMER_INTERACTIONS_COLS = frozenset(
    {
        "id",
        "customer_id",
        "type",
        "summary",
        "outcome",
        "conducted_by",
        "conducted_at",
        "created_at",
    }
)

TABLE_OPPORTUNITIES_COLS = frozenset(
    {
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
    }
)
