from sqlalchemy import Column, Float, ForeignKey, Index, Integer, Table, Text, text

from ..models import metadata

did_registry = Table(
    "did_registry",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("did", Text, nullable=False, unique=True),
    Column("entity_type", Text, server_default=text("user")),
    Column("entity_id", Integer),
    Column("public_key", Text, server_default=text("")),
    Column("status", Text, server_default=text("active")),
    Column("metadata", Text, server_default=text("{}")),
    Column("created_by", Integer, ForeignKey("users.id")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text),
)

vc_credentials = Table(
    "vc_credentials",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("vc_id", Text, nullable=False, unique=True),
    Column("issuer_did", Text, ForeignKey("did_registry.did"), nullable=False),
    Column("subject_did", Text, ForeignKey("did_registry.did"), nullable=False),
    Column("credential_type", Text, nullable=False),
    Column("claims", Text, server_default=text("{}")),
    Column("issuance_date", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("expiration_date", Text),
    Column("proof", Text, server_default=text("")),
    Column("status", Text, server_default=text("active")),
    Column("revoked_at", Text),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

fed_audit_contributions = Table(
    "fed_audit_contributions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("contributor_did", Text, ForeignKey("did_registry.did"), nullable=False),
    Column("contribution_type", Text, nullable=False),
    Column("payload_hash", Text, server_default=text("")),
    Column("payload_summary", Text, server_default=text("")),
    Column("weight", Float, server_default=text("'1.0'")),
    Column("verified", Integer, server_default=text("'0'")),
    Column("verified_by", Text, server_default=text("")),
    Column("audit_chain_hash", Text, server_default=text("")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

privacy_budgets = Table(
    "privacy_budgets",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("did", Text, ForeignKey("did_registry.did"), nullable=False),
    Column("epsilon_total", Float, server_default=text("'1.0'")),
    Column("epsilon_spent", Float, server_default=text("'0.0'")),
    Column("epsilon_remaining", Float, server_default=text("'1.0'")),
    Column("query_count", Integer, server_default=text("'0'")),
    Column("last_query_at", Text),
    Column("reset_at", Text),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

data_masking_rules = Table(
    "data_masking_rules",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("rule_name", Text, nullable=False, unique=True),
    Column("field_pattern", Text, nullable=False),
    Column("masking_type", Text, nullable=False),
    Column("masking_config", Text, server_default=text("{}")),
    Column("applies_to", Text, server_default=text("all")),
    Column("enabled", Integer, server_default=text("'1'")),
    Column("created_by", Integer, ForeignKey("users.id")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text),
)

dp_audit_log = Table(
    "dp_audit_log",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("did", Text, ForeignKey("did_registry.did"), nullable=False),
    Column("operation_type", Text, nullable=False),
    Column("epsilon_consumed", Float, server_default=text("'0.0'")),
    Column("data_category", Text, server_default=text("")),
    Column("row_count", Integer, server_default=text("'0'")),
    Column("noise_level", Float, server_default=text("'0.0'")),
    Column("approved", Integer, server_default=text("'1'")),
    Column("details", Text, server_default=text("{}")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

privacy_compute_jobs = Table(
    "privacy_compute_jobs",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("job_id", Text, unique=True),
    Column("compute_type", Text),
    Column("sensitivity_level", Text, server_default=text("medium")),
    Column("data_summary", Text, server_default=text("")),
    Column("selected_scheme", Text, server_default=text("")),
    Column("status", Text, server_default=text("pending")),
    Column("epsilon_used", Float, server_default=text("'0.0'")),
    Column("noise_level", Float, server_default=text("'0.0'")),
    Column("result_summary", Text, server_default=text("")),
    Column("created_by", Integer, ForeignKey("users.id")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("completed_at", Text),
)

federated_rounds = Table(
    "federated_rounds",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("round_id", Text, unique=True),
    Column("model_name", Text),
    Column("round_number", Integer),
    Column("participant_count", Integer, server_default=text("'0'")),
    Column("aggregation_method", Text, server_default=text("fed_avg")),
    Column("global_metrics", Text, server_default=text("{}")),
    Column("status", Text, server_default=text("pending")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("completed_at", Text),
)

Index("idx_did_did", "did")
Index("idx_did_status", "status")
Index("idx_vc_issuer", "issuer_did")
Index("idx_vc_subject", "subject_did")
Index("idx_vc_type", "credential_type")
Index("idx_fed_contributor", "contributor_did")
Index("idx_fed_type", "contribution_type")
Index("idx_pb_did", "did")
Index("idx_dpal_did", "did")
Index("idx_dpal_type", "operation_type")
Index("idx_pcj_job", "job_id")
Index("idx_pcj_type", "compute_type")
Index("idx_fr_round", "round_id")
Index("idx_fr_type", "model_name")
