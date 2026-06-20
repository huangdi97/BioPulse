"""Task module."""

TABLE_BOARD_TASKS_COLS = frozenset(
    {
        "id",
        "board_id",
        "title",
        "description",
        "status",
        "priority",
        "assignee_id",
        "due_date",
        "sort_order",
        "is_active",
        "created_by",
        "created_at",
        "updated_at",
    }
)

TABLE_TASK_BOARDS_COLS = frozenset(
    {
        "id",
        "name",
        "description",
        "owner_id",
        "is_active",
        "created_at",
        "updated_at",
    }
)
