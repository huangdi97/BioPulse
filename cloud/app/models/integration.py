from sqlalchemy import Column, Float, ForeignKey, Index, Integer, Table, Text, text

from ..models import metadata

event_bus_definitions = Table(
    "event_bus_definitions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("event_type", Text, nullable=False, unique=True),
    Column("display_name", Text, server_default=text("")),
    Column("description", Text, server_default=text("")),
    Column("source_end", Text, server_default=text("cloud")),
    Column("target_ends", Text, server_default=text("[]")),
    Column("schema_template", Text, server_default=text("{}")),
    Column("priority", Integer, server_default=text("'100'")),
    Column("enabled", Integer, server_default=text("'1'")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

event_bus_messages = Table(
    "event_bus_messages",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("message_id", Text, nullable=False, unique=True),
    Column("event_type", Text, ForeignKey("event_bus_definitions.event_type"), nullable=False),
    Column("source_end", Text, server_default=text("cloud")),
    Column("source_entity_type", Text, server_default=text("")),
    Column("source_entity_id", Text, server_default=text("")),
    Column("payload", Text, server_default=text("{}")),
    Column("correlation_id", Text, server_default=text("")),
    Column("priority", Integer, server_default=text("'100'")),
    Column("status", Text, server_default=text("pending")),
    Column("retry_count", Integer, server_default=text("'0'")),
    Column("max_retries", Integer, server_default=text("'3'")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("delivered_at", Text),
)

event_delivery_log = Table(
    "event_delivery_log",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("message_id", Text, ForeignKey("event_bus_messages.message_id"), nullable=False),
    Column("target_end", Text, nullable=False),
    Column("delivery_status", Text, server_default=text("pending")),
    Column("attempt", Integer, server_default=text("'1'")),
    Column("response_summary", Text, server_default=text("")),
    Column("duration_ms", Integer, server_default=text("'0'")),
    Column("error_message", Text, server_default=text("")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

kg_entities = Table(
    "kg_entities",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("entity_id", Text, nullable=False, unique=True),
    Column("entity_type", Text, nullable=False),
    Column("name", Text, nullable=False),
    Column("aliases", Text, server_default=text("[]")),
    Column("properties", Text, server_default=text("{}")),
    Column("source_table", Text, server_default=text("")),
    Column("source_row_id", Integer),
    Column("status", Text, server_default=text("active")),
    Column("confidence", Float, server_default=text("'1.0'")),
    Column("created_by", Integer, ForeignKey("users.id")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text),
)

kg_relations = Table(
    "kg_relations",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("source_entity_id", Text, ForeignKey("kg_entities.entity_id"), nullable=False),
    Column("target_entity_id", Text, ForeignKey("kg_entities.entity_id"), nullable=False),
    Column("relation_type", Text, nullable=False),
    Column("weight", Float, server_default=text("'1.0'")),
    Column("properties", Text, server_default=text("{}")),
    Column("direction", Text, server_default=text("directed")),
    Column("confidence", Float, server_default=text("'1.0'")),
    Column("source", Text, server_default=text("manual")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

kg_search_cache = Table(
    "kg_search_cache",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("query_hash", Text, nullable=False),
    Column("query_text", Text, nullable=False),
    Column("result_summary", Text, server_default=text("")),
    Column("result_count", Integer, server_default=text("'0'")),
    Column("cache_ttl", Integer, server_default=text("'300'")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

market_intel_sources = Table(
    "market_intel_sources",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", Text, nullable=False),
    Column("source_type", Text, nullable=False, server_default=text("competitor")),
    Column("target_keywords", Text, server_default=text("[]")),
    Column("is_active", Integer, server_default=text("'1'")),
    Column("created_by", Integer, ForeignKey("users.id")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text),
)

market_intel_items = Table(
    "market_intel_items",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("source_id", Integer, ForeignKey("market_intel_sources.id")),
    Column("title", Text, nullable=False),
    Column("summary", Text, server_default=text("")),
    Column("content", Text, server_default=text("")),
    Column("url", Text, server_default=text("")),
    Column("item_type", Text, nullable=False, server_default=text("competitor")),
    Column("relevance_tags", Text, server_default=text("[]")),
    Column("impact_level", Text, server_default=text("medium")),
    Column("status", Text, server_default=text("unread")),
    Column("ai_analysis", Text, server_default=text("")),
    Column("collected_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("created_by", Integer, ForeignKey("users.id")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text),
)

mdt_sessions = Table(
    "mdt_sessions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("title", Text, nullable=False),
    Column("question", Text, nullable=False),
    Column("context", Text, server_default=text("")),
    Column("status", Text, nullable=False, server_default=text("active")),
    Column("consensus", Text, server_default=text("")),
    Column("consensus_json", Text, server_default=text("{}")),
    Column("round_count", Integer, server_default=text("'0'")),
    Column("created_by", Integer, ForeignKey("users.id")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text),
)

mdt_participants = Table(
    "mdt_participants",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("session_id", Integer, ForeignKey("mdt_sessions.id"), nullable=False),
    Column("agent_role_id", Integer, ForeignKey("agent_roles.id"), nullable=False),
    Column("role_name", Text, server_default=text("")),
    Column("stance", Text, server_default=text("neutral")),
    Column("vote_weight", Float, server_default=text("'1.0'")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

mdt_opinions = Table(
    "mdt_opinions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("session_id", Integer, ForeignKey("mdt_sessions.id"), nullable=False),
    Column("participant_id", Integer, ForeignKey("mdt_participants.id"), nullable=False),
    Column("round_number", Integer, nullable=False),
    Column("opinion", Text, server_default=text("")),
    Column("summary", Text, server_default=text("")),
    Column("sentiment", Text, server_default=text("neutral")),
    Column("confidence", Float, server_default=text("'0.5'")),
    Column("key_points", Text, server_default=text("[]")),
    Column("ai_response_raw", Text, server_default=text("")),
    Column("tokens_used", Integer, server_default=text("'0'")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

async_mdt_opinions = Table(
    "async_mdt_opinions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("decision_id", Integer, ForeignKey("soap_decisions.id"), nullable=False),
    Column("contributor_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("contributor_role", Text, server_default=text("")),
    Column("opinion", Text, nullable=False),
    Column("supporting_data", Text, server_default=text("")),
    Column("stance", Text, server_default=text("neutral")),
    Column("confidence", Float, server_default=text("'0.5'")),
    Column("attachments", Text, server_default=text("[]")),
    Column("is_final", Integer, server_default=text("'0'")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

task_boards = Table(
    "task_boards",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", Text, nullable=False),
    Column("description", Text, server_default=text("")),
    Column("owner_id", Integer, nullable=False),
    Column("is_active", Integer, server_default=text("'1'")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text),
)

board_tasks = Table(
    "board_tasks",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("board_id", Integer, nullable=False),
    Column("title", Text, nullable=False),
    Column("description", Text, server_default=text("")),
    Column("status", Text, nullable=False, server_default=text("todo")),
    Column("priority", Text, server_default=text("medium")),
    Column("assignee_id", Integer),
    Column("due_date", Text),
    Column("sort_order", Integer, server_default=text("'0'")),
    Column("is_active", Integer, server_default=text("'1'")),
    Column("created_by", Integer),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text),
)

Index("idx_ebd_type", "event_type")
Index("idx_ebd_source", "source_end")
Index("idx_ebm_type", "event_type")
Index("idx_ebm_status", "status")
Index("idx_ebm_corr", "correlation_id")
Index("idx_edl_msg", "message_id")
Index("idx_edl_target", "target_end")
Index("idx_kge_type", "entity_type")
Index("idx_kge_name", "name")
Index("idx_kgr_source", "source_entity_id")
Index("idx_kgr_target", "target_entity_id")
Index("idx_kgr_type", "relation_type")
Index("idx_kgq_hash", "query_hash")
Index("idx_intel_sources_type", "source_type")
Index("idx_intel_sources_active", "is_active")
Index("idx_intel_items_type", "item_type")
Index("idx_intel_items_status", "status")
Index("idx_intel_items_impact", "impact_level")
Index("idx_intel_items_time", "collected_at")
Index("idx_mdt_status", "status")
Index("idx_mdt_participant_session", "session_id")
Index("idx_mdt_opinions_session", "session_id")
Index("idx_async_mdt_decision", "decision_id")
Index("idx_async_mdt_contributor", "contributor_id")
Index("idx_board_tasks_board", "board_id", "status")
Index("idx_board_tasks_assignee", "assignee_id")
