"""Soap module."""

TABLE_SOAP_DECISIONS_COLS = frozenset(
    {
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
    }
)

TABLE_SOAP_TEMPLATES_COLS = frozenset(
    {
        "id",
        "name",
        "category",
        "description",
        "structure",
        "is_active",
        "created_by",
        "created_at",
        "updated_at",
    }
)
