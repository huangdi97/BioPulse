from sqlalchemy import Column, Float, ForeignKey, Index, Integer, Table, Text, UniqueConstraint, text

from ..models import metadata

decision_cases = Table(
    "decision_cases",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", Text, nullable=False),
    Column("pipeline_run_id", Integer, ForeignKey("pipeline_runs.id")),
    Column("description", Text, server_default=text("")),
    Column("outcome", Text, server_default=text("")),
    Column("outcome_score", Float, server_default=text("'0.0'")),
    Column("context", Text, server_default=text("{}")),
    Column("tags", Text, server_default=text("[]")),
    Column("is_active", Integer, server_default=text("'1'")),
    Column("created_by", Integer, ForeignKey("users.id")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text),
)

causal_analyses = Table(
    "causal_analyses",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("case_id", Integer, ForeignKey("decision_cases.id"), nullable=False),
    Column("analysis_type", Text, nullable=False, server_default=text("causal")),
    Column("summary", Text, server_default=text("")),
    Column("key_drivers", Text, server_default=text("[]")),
    Column("causal_chain", Text, server_default=text("[]")),
    Column("attribution_scores", Text, server_default=text("{}")),
    Column("recommendations", Text, server_default=text("[]")),
    Column("ai_response_raw", Text, server_default=text("")),
    Column("tokens_used", Integer, server_default=text("'0'")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

cross_case_insights = Table(
    "cross_case_insights",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("title", Text, nullable=False),
    Column("insight_type", Text, nullable=False, server_default=text("pattern")),
    Column("summary", Text, server_default=text("")),
    Column("detail", Text, server_default=text("")),
    Column("evidence", Text, server_default=text("[]")),
    Column("confidence", Float, server_default=text("'0.5'")),
    Column("applicability", Text, server_default=text("general")),
    Column("source_run_ids", Text, server_default=text("[]")),
    Column("is_active", Integer, server_default=text("'1'")),
    Column("created_by", Integer, ForeignKey("users.id")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text),
)

causal_graphs = Table(
    "causal_graphs",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("graph_id", Text, unique=True),
    Column("decision_id", Text),
    Column("graph_data", Text, server_default=text("{}")),
    Column("summary", Text),
    Column("node_count", Integer),
    Column("edge_count", Integer),
    Column("created_by", Integer),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

counterfactual_scenarios = Table(
    "counterfactual_scenarios",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("scenario_id", Text, unique=True),
    Column("strategy_id", Text),
    Column("base_description", Text),
    Column("variable_changes", Text, server_default=text("[]")),
    Column("predicted_outcome", Text, server_default=text("{}")),
    Column("confidence", Float),
    Column("created_by", Integer),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

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

working_memory = Table(
    "working_memory",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("session_id", Text, nullable=False),
    Column("slot_key", Text, nullable=False),
    Column("slot_value", Text, server_default=text("")),
    Column("slot_type", Text, server_default=text("string")),
    Column("ttl_seconds", Integer, server_default=text("'1800'")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("expires_at", Text),
    UniqueConstraint("session_id", "slot_key"),
)

episodic_memory = Table(
    "episodic_memory",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("event_type", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("description", Text, server_default=text("")),
    Column("context", Text, server_default=text("{}")),
    Column("outcome", Text, server_default=text("")),
    Column("valence", Float, server_default=text("'0.0'")),
    Column("intensity", Float, server_default=text("'0.5'")),
    Column("involved_agents", Text, server_default=text("[]")),
    Column("related_entity_type", Text, server_default=text("")),
    Column("related_entity_id", Integer),
    Column("is_consolidated", Integer, server_default=text("'0'")),
    Column("created_by", Text, server_default=text("")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

world_tree_nodes = Table(
    "world_tree_nodes",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", Text, nullable=False),
    Column("description", Text, server_default=text("")),
    Column("parent_id", Integer, ForeignKey("world_tree_nodes.id")),
    Column("path", Text, server_default=text("")),
    Column("level", Integer, server_default=text("'0'")),
    Column("node_type", Text, server_default=text("tag")),
    Column("sort_order", Integer, server_default=text("'0'")),
    Column("metadata", Text, server_default=text("{}")),
    Column("is_active", Integer, server_default=text("'1'")),
    Column("created_by", Integer, ForeignKey("users.id")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

node_memory_links = Table(
    "node_memory_links",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("node_id", Integer, ForeignKey("world_tree_nodes.id"), nullable=False),
    Column("memory_entry_id", Integer, ForeignKey("memory_entries.id"), nullable=False),
    Column("relevance_score", Float, server_default=text("'0.5'")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    UniqueConstraint("node_id", "memory_entry_id"),
)

world_tree_snapshots = Table(
    "world_tree_snapshots",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("node_id", Integer, ForeignKey("world_tree_nodes.id"), nullable=False),
    Column("snapshot_type", Text, server_default=text("full")),
    Column("subtree_json", Text, server_default=text("{}")),
    Column("memory_count", Integer, server_default=text("'0'")),
    Column("version", Integer, server_default=text("'1'")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("expires_at", Text),
)

Index("idx_dec_cases_outcome", "outcome_score")
Index("idx_dec_cases_run", "pipeline_run_id")
Index("idx_causal_case", "case_id")
Index("idx_insights_type", "insight_type")
Index("idx_insights_confidence", "confidence")
Index("idx_cg_graph", "graph_id")
Index("idx_cg_decision", "decision_id")
Index("idx_cs_scenario", "scenario_id")
Index("idx_memory_type", "memory_type")
Index("idx_memory_importance", "importance")
Index("idx_memory_accessed", "last_accessed")
Index("idx_mus_score", "utility_score")
Index("idx_mus_decay", "decay_rate")
Index("idx_mema_a", "memory_id_a")
Index("idx_mema_b", "memory_id_b")
Index("idx_mema_pair", "MIN(memory_id_a, memory_id_b)", "MAX(memory_id_a, memory_id_b)", unique=True)
Index("idx_em_agent", "agent_role")
Index("idx_em_source_sub", "source_sub")
Index("idx_br_report", "report_id")
Index("idx_am_item", "item_id")
Index("idx_am_cat", "category")
Index("idx_wm_session", "session_id")
Index("idx_wm_expires", "expires_at")
Index("idx_em_event", "event_type")
Index("idx_em_outcome", "outcome")
Index("idx_em_time", "created_at")
Index("idx_tree_parent", "parent_id")
Index("idx_tree_path", "path")
Index("idx_tree_type", "node_type")
Index("idx_nml_node", "node_id")
Index("idx_nml_memory", "memory_entry_id")
Index("idx_snapshot_node", "node_id")
