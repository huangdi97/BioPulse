"""Auth module."""

TABLE_SYSTEM_CONFIGS_COLS = frozenset(
    {
        "id",
        "key",
        "value",
        "description",
        "updated_by",
        "updated_at",
    }
)

TABLE_TEAMS_COLS = frozenset(
    {
        "id",
        "name",
        "description",
        "is_active",
        "created_by",
        "created_at",
        "updated_at",
    }
)

TABLE_USERS_COLS = frozenset(
    {
        "id",
        "username",
        "hashed_password",
        "role",
        "is_active",
        "created_at",
    }
)

TABLE_USER_TEAM_COLS = frozenset(
    {
        "id",
        "user_id",
        "team_id",
        "role",
        "created_at",
    }
)
