from sqlalchemy import Column, Float, ForeignKey, Index, Integer, Table, Text, text

from ..models import metadata

audit_logs = Table(
    "audit_logs",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, nullable=False),
    Column("action", Text, nullable=False),
    Column("entity_type", Text, nullable=False),
    Column("entity_id", Integer),
    Column("detail", Text, server_default=text("")),
    Column("source_end", Text, nullable=False),
    Column("ip_address", Text, server_default=text("")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

compliance_audit_records = Table(
    "compliance_audit_records",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("message_type", Text, nullable=False, server_default=text("text")),
    Column("content", Text, nullable=False),
    Column("source_id", Text, server_default=text("")),
    Column("score", Float, server_default=text("'0.0'")),
    Column("risk_level", Text, nullable=False, server_default=text("low")),
    Column("passed", Integer, nullable=False, server_default=text("'1'")),
    Column("violations", Text, server_default=text("[]")),
    Column("ai_analysis", Text, server_default=text("")),
    Column("reviewed_by", Integer, ForeignKey("users.id")),
    Column("reviewed_at", Text),
    Column("created_by", Integer, ForeignKey("users.id")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

audit_chain_entries = Table(
    "audit_chain_entries",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("entity_type", Text, nullable=False),
    Column("entity_id", Text, nullable=False),
    Column("action", Text, nullable=False),
    Column("previous_hash", Text, server_default=text("")),
    Column("current_hash", Text, nullable=False),
    Column("payload", Text, server_default=text("{}")),
    Column("metadata", Text, server_default=text("{}")),
    Column("source", Text, server_default=text("")),
    Column("created_by", Integer, ForeignKey("users.id")),
    Column("performed_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

training_corrections = Table(
    "training_corrections",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("audit_record_id", Integer, ForeignKey("compliance_audit_records.id")),
    Column("title", Text, nullable=False),
    Column("description", Text, server_default=text("")),
    Column("category", Text, server_default=text("general")),
    Column("severity", Text, nullable=False, server_default=text("medium")),
    Column("status", Text, nullable=False, server_default=text("pending")),
    Column("assigned_to", Integer, ForeignKey("users.id")),
    Column("created_by", Integer, ForeignKey("users.id")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text),
)

compliance_rules = Table(
    "compliance_rules",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", Text, nullable=False),
    Column("category", Text, nullable=False),
    Column("keyword", Text, nullable=False),
    Column("max_value", Float),
    Column("created_by", Integer, ForeignKey("users.id")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

contents = Table(
    "contents",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("title", Text, nullable=False),
    Column("body", Text, nullable=False),
    Column("category", Text, nullable=False),
    Column("tags", Text, server_default=text("")),
    Column("status", Text, nullable=False, server_default=text("draft")),
    Column("compliance_score", Float),
    Column("created_by", Integer, ForeignKey("users.id")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

notification_templates = Table(
    "notification_templates",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", Text, nullable=False, unique=True),
    Column("title_template", Text, nullable=False),
    Column("body_template", Text, nullable=False),
    Column("category", Text, nullable=False),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

notifications = Table(
    "notifications",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, nullable=False),
    Column("template_id", Integer),
    Column("title", Text, nullable=False),
    Column("body", Text, nullable=False),
    Column("category", Text, nullable=False),
    Column("ref_type", Text, server_default=text("")),
    Column("ref_id", Integer),
    Column("context_json", Text, server_default=text("")),
    Column("is_read", Integer, server_default=text("'0'")),
    Column("read_at", Text),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

nmpa_compliance_logs = Table(
    "nmpa_compliance_logs",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("log_id", Text, unique=True),
    Column("document_type", Text),
    Column("content_summary", Text, server_default=text("")),
    Column("violations_found", Integer, server_default=text("'0'")),
    Column("violation_details", Text, server_default=text("[]")),
    Column("human_review_required", Integer, server_default=text("'0'")),
    Column("human_reviewer", Text, server_default=text("")),
    Column("human_reviewed_at", Text),
    Column("created_by", Integer, ForeignKey("users.id")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

soap_templates = Table(
    "soap_templates",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", Text, nullable=False),
    Column("category", Text, nullable=False, server_default=text("general")),
    Column("description", Text, server_default=text("")),
    Column("structure", Text, nullable=False, server_default=text("{}")),
    Column("is_active", Integer, server_default=text("'1'")),
    Column("created_by", Integer, ForeignKey("users.id")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

soap_decisions = Table(
    "soap_decisions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("title", Text, nullable=False),
    Column("template_id", Integer, ForeignKey("soap_templates.id")),
    Column("subjective", Text, server_default=text("")),
    Column("objective", Text, server_default=text("")),
    Column("assessment", Text, server_default=text("")),
    Column("plan", Text, server_default=text("")),
    Column("status", Text, nullable=False, server_default=text("draft")),
    Column("priority", Text, server_default=text("medium")),
    Column("tags", Text, server_default=text("[]")),
    Column("decision_summary", Text, server_default=text("")),
    Column("decided_by", Integer, ForeignKey("users.id")),
    Column("decided_at", Text),
    Column("is_active", Integer, server_default=text("'1'")),
    Column("created_by", Integer, ForeignKey("users.id")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

Index("idx_audit_entity", "entity_type", "entity_id")
Index("idx_audit_user", "user_id")
Index("idx_audit_action_time", "action", "created_at")
Index("idx_audit_records_type", "message_type")
Index("idx_audit_records_risk", "risk_level")
Index("idx_audit_records_time", "created_at")
Index("idx_chain_entity", "entity_type", "entity_id")
Index("idx_chain_action", "action")
Index("idx_chain_time", "performed_at")
Index("idx_corrections_audit", "audit_record_id")
Index("idx_corrections_status", "status")
Index("idx_corrections_severity", "severity")
Index("idx_notif_user", "user_id", "is_read")
Index("idx_notif_user_time", "user_id", "created_at")
Index("idx_ncl_log", "log_id")
Index("idx_ncl_type", "document_type")
Index("idx_soap_status", "status")
Index("idx_soap_priority", "priority")
