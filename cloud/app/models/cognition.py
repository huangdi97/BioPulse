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

from .cognition_tables_extra import *  # noqa: E402, F401, F403
