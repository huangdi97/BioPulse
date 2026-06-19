from sqlalchemy import Column, Float, ForeignKey, Index, Integer, Table, Text, UniqueConstraint, text

from ..models import metadata

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("username", Text, nullable=False, unique=True),
    Column("hashed_password", Text, nullable=False),
    Column("role", Text, server_default=text("user")),
    Column("is_active", Integer, server_default=text("'1'")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text),
)

api_tokens = Table(
    "api_tokens",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("token_hash", Text, nullable=False),
    Column("name", Text, nullable=False),
    Column("is_active", Integer, server_default=text("'1'")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

teams = Table(
    "teams",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", Text, nullable=False),
    Column("description", Text),
    Column("is_active", Integer, server_default=text("'1'")),
    Column("created_by", Integer),
    Column("created_at", Text),
    Column("updated_at", Text),
)

user_team = Table(
    "user_team",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("team_id", Integer, ForeignKey("teams.id"), nullable=False),
    Column("role", Text, server_default=text("member")),
    Column("created_at", Text),
    UniqueConstraint("user_id", "team_id"),
)

system_configs = Table(
    "system_configs",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("key", Text, nullable=False, unique=True),
    Column("value", Text, nullable=False),
    Column("description", Text, server_default=text("")),
    Column("updated_by", Integer),
    Column("updated_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

token_blacklist = Table(
    "token_blacklist",
    metadata,
    Column("token_jti", Text, primary_key=True),
    Column("expires_at", Text, nullable=False),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

settings = Table(
    "settings",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("key", Text, nullable=False, unique=True),
    Column("value", Text, nullable=False, server_default=text("")),
    Column("updated_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

token_budget = Table(
    "token_budget",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, nullable=False),
    Column("model", Text, nullable=False),
    Column("daily_used", Integer, nullable=False, server_default=text("'0'")),
    Column("alert_sent", Integer, nullable=False, server_default=text("'0'")),
    Column("updated_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

token_usage = Table(
    "token_usage",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, nullable=False),
    Column("model", Text, nullable=False),
    Column("tokens", Integer, nullable=False, server_default=text("'0'")),
    Column("cost", Float, nullable=False, server_default=text("'0.0'")),
    Column("usage_date", Text, nullable=False),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

Index("idx_blacklist_expires", "expires_at")
Index("idx_token_budget_user", "user_id", "model")
Index("idx_token_usage_user", "user_id", "model", "usage_date")
