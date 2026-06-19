from sqlalchemy import Column, Float, ForeignKey, Index, Integer, Table, Text, text

from ..models import metadata

training_modules = Table(
    "training_modules",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("title", Text, nullable=False),
    Column("category", Text, nullable=False, server_default=text("compliance")),
    Column("difficulty", Text, nullable=False, server_default=text("medium")),
    Column("content", Text, server_default=text("")),
    Column("prerequisites", Text, server_default=text("[]")),
    Column("passing_score", Float, server_default=text("'0.7'")),
    Column("estimated_minutes", Integer, server_default=text("'15'")),
    Column("is_active", Integer, server_default=text("'1'")),
    Column("created_by", Integer, ForeignKey("users.id")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

training_sessions = Table(
    "training_sessions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("module_id", Integer, ForeignKey("training_modules.id"), nullable=False),
    Column("score", Float, server_default=text("'0.0'")),
    Column("passed", Integer, server_default=text("'0'")),
    Column("time_spent_seconds", Integer, server_default=text("'0'")),
    Column("answers", Text, server_default=text("[]")),
    Column("feedback", Text, server_default=text("")),
    Column("difficulty_used", Text, server_default=text("medium")),
    Column("next_difficulty", Text, server_default=text("")),
    Column("completed_at", Text),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

training_attributions = Table(
    "training_attributions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("training_session_id", Integer, ForeignKey("training_sessions.id")),
    Column("metric_name", Text, nullable=False),
    Column("metric_before", Float, server_default=text("'0.0'")),
    Column("metric_after", Float, server_default=text("'0.0'")),
    Column("change_pct", Float, server_default=text("'0.0'")),
    Column("attribution_score", Float, server_default=text("'0.0'")),
    Column("confidence", Float, server_default=text("'0.0'")),
    Column("analysis", Text, server_default=text("")),
    Column("period_days", Integer, server_default=text("'30'")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

training_scripts = Table(
    "training_scripts",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("script_id", Text, unique=True),
    Column("script_name", Text),
    Column("source_agent_role", Text),
    Column("source_collaboration_id", Text),
    Column("description", Text),
    Column("steps", Text, server_default=text("[]")),
    Column("difficulty", Text, server_default=text("mid")),
    Column("target_roles", Text, server_default=text("[]")),
    Column("score", Float),
    Column("created_by", Integer, ForeignKey("users.id")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text),
)

training_roi_analysis = Table(
    "training_roi_analysis",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("analysis_id", Text, unique=True),
    Column("period_start", Text),
    Column("period_end", Text),
    Column("training_hours", Float),
    Column("participants", Integer),
    Column("behavior_change_score", Float),
    Column("sales_impact", Float),
    Column("cost_savings", Float),
    Column("roi", Float),
    Column("metadata", Text, server_default=text("{}")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

supply_chain_items = Table(
    "supply_chain_items",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("item_id", Text, unique=True),
    Column("item_name", Text),
    Column("sku", Text),
    Column("category", Text),
    Column("current_stock", Integer),
    Column("min_stock", Integer),
    Column("max_stock", Integer),
    Column("unit_price", Float),
    Column("supplier", Text),
    Column("status", Text, server_default=text("active")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text),
)

sensor_sessions = Table(
    "sensor_sessions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("session_id", Text, unique=True),
    Column("session_name", Text),
    Column("event_type", Text, server_default=text("academic_meeting")),
    Column("location", Text),
    Column("start_time", Text),
    Column("end_time", Text),
    Column("data_summary", Text, server_default=text("{}")),
    Column("status", Text, server_default=text("active")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

user_profiles = Table(
    "user_profiles",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("persona_type", Text, server_default=text("")),
    Column("specialization", Text, server_default=text("")),
    Column("experience_level", Text, server_default=text("mid")),
    Column("preferred_content_types", Text, server_default=text("[]")),
    Column("custom_tags", Text, server_default=text("[]")),
    Column("embedding", Text, server_default=text("")),
    Column("updated_at", Text),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

user_behaviors = Table(
    "user_behaviors",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("action_type", Text, nullable=False),
    Column("target_type", Text, server_default=text("")),
    Column("target_id", Text, server_default=text("")),
    Column("metadata", Text, server_default=text("{}")),
    Column("session_id", Text, server_default=text("")),
    Column("duration_seconds", Integer, server_default=text("'0'")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

recommendations = Table(
    "recommendations",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("rec_type", Text, nullable=False),
    Column("rec_target_id", Text, server_default=text("")),
    Column("rec_title", Text, server_default=text("")),
    Column("rec_reason", Text, server_default=text("")),
    Column("score", Float, server_default=text("'0.0'")),
    Column("strategy_name", Text, server_default=text("")),
    Column("clicked", Integer, server_default=text("'0'")),
    Column("dismissed", Integer, server_default=text("'0'")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

Index("idx_tm_category", "category")
Index("idx_tm_difficulty", "difficulty")
Index("idx_ts_user", "user_id")
Index("idx_ts_module", "module_id")
Index("idx_ta_user", "user_id")
Index("idx_ta_metric", "metric_name")
Index("idx_ts_script", "script_id")
Index("idx_ts_role", "source_agent_role")
Index("idx_tra_id", "analysis_id")
Index("idx_sci_item", "item_id")
Index("idx_ss_session", "session_id")
Index("idx_up_user", "user_id", unique=True)
Index("idx_ub_user", "user_id")
Index("idx_ub_action", "action_type")
Index("idx_ub_target", "target_type")
Index("idx_rec_user", "user_id")
Index("idx_rec_type", "rec_type")
