from sqlalchemy import Column, Float, ForeignKey, Integer, Table, Text, text

from ..models import metadata

memory_gates = Table(
    "memory_gates",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", Text, nullable=False),
    Column("source_type", Text, nullable=False),
    Column("importance_threshold", Float, server_default=text("'0.5'")),
    Column("ttl_days", Integer, server_default=text("'90'")),
    Column("retention_policy", Text, server_default=text("normal")),
    Column("is_active", Integer, server_default=text("'1'")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

memory_entries = Table(
    "memory_entries",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("title", Text, nullable=False),
    Column("content", Text, server_default=text("")),
    Column("memory_type", Text, nullable=False, server_default=text("insight")),
    Column("source_type", Text, server_default=text("")),
    Column("source_id", Text, server_default=text("")),
    Column("importance", Float, server_default=text("'0.5'")),
    Column("context_tags", Text, server_default=text("[]")),
    Column("embedding", Text, server_default=text("")),
    Column("access_count", Integer, server_default=text("'0'")),
    Column("last_accessed", Text),
    Column("is_active", Integer, server_default=text("'1'")),
    Column("created_by", Integer, ForeignKey("users.id")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

memory_recall_log = Table(
    "memory_recall_log",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("query_text", Text, server_default=text("")),
    Column("memory_ids", Text, server_default=text("[]")),
    Column("result_count", Integer, server_default=text("'0'")),
    Column("context", Text, server_default=text("{}")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

memory_utility_scores = Table(
    "memory_utility_scores",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("memory_entry_id", Integer, ForeignKey("memory_entries.id"), nullable=False, unique=True),
    Column("utility_score", Float, server_default=text("'0.0'")),
    Column("access_frequency", Float, server_default=text("'0.0'")),
    Column("recency_score", Float, server_default=text("'0.0'")),
    Column("importance_score", Float, server_default=text("'0.0'")),
    Column("connectivity_score", Float, server_default=text("'0.0'")),
    Column("decay_rate", Float, server_default=text("'0.0'")),
    Column("last_utility_update", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

sleep_consolidation_logs = Table(
    "sleep_consolidation_logs",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("consolidation_type", Text, nullable=False),
    Column("source_entry_ids", Text, server_default=text("[]")),
    Column("target_entry_id", Integer, ForeignKey("memory_entries.id")),
    Column("action_detail", Text, server_default=text("")),
    Column("utility_before", Float, server_default=text("'0.0'")),
    Column("utility_after", Float, server_default=text("'0.0'")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

memory_consolidation_log = Table(
    "memory_consolidation_log",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("consolidation_type", Text, nullable=False),
    Column("source_table", Text, server_default=text("")),
    Column("item_count", Integer, server_default=text("'0'")),
    Column("items_promoted", Integer, server_default=text("'0'")),
    Column("items_pruned", Integer, server_default=text("'0'")),
    Column("items_superseded", Integer, server_default=text("'0'")),
    Column("duration_ms", Integer, server_default=text("'0'")),
    Column("status", Text, server_default=text("completed")),
    Column("details", Text, server_default=text("{}")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

memory_associations = Table(
    "memory_associations",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("memory_id_a", Integer, ForeignKey("memory_entries.id"), nullable=False),
    Column("memory_id_b", Integer, ForeignKey("memory_entries.id"), nullable=False),
    Column("relation_type", Text, nullable=False, server_default=text("related")),
    Column("weight", Float, server_default=text("'1.0'")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

effect_metrics = Table(
    "effect_metrics",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("metric_id", Text, unique=True),
    Column("agent_role", Text),
    Column("metric_type", Text),
    Column("metric_value", Float),
    Column("metric_unit", Text),
    Column("source_table", Text),
    Column("source_row_id", Text),
    Column("source_sub", Text, server_default=text("")),
    Column("period_start", Text),
    Column("period_end", Text),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

benchmark_reports = Table(
    "benchmark_reports",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("report_id", Text, unique=True),
    Column("report_name", Text),
    Column("report_type", Text),
    Column("data_source", Text, server_default=text("aggregated")),
    Column("summary", Text),
    Column("metrics", Text, server_default=text("{}")),
    Column("period", Text),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

agent_marketplace = Table(
    "agent_marketplace",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("item_id", Text, unique=True),
    Column("item_name", Text),
    Column("item_type", Text, server_default=text("template")),
    Column("description", Text),
    Column("agent_config", Text, server_default=text("{}")),
    Column("category", Text),
    Column("price_model", Text, server_default=text("free")),
    Column("rating", Float),
    Column("download_count", Integer),
    Column("enabled", Integer),
    Column("publisher", Text),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text),
)
