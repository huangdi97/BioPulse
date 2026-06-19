from sqlalchemy import Column, Float, ForeignKey, Index, Integer, Table, Text, text

from ..models import metadata

customers = Table(
    "customers",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", Text, nullable=False),
    Column("title", Text, server_default=text("")),
    Column("hospital", Text, server_default=text("")),
    Column("department", Text, server_default=text("")),
    Column("specialty", Text, server_default=text("")),
    Column("phone", Text, server_default=text("")),
    Column("email", Text, server_default=text("")),
    Column("tags", Text, server_default=text("[]")),
    Column("status", Text, server_default=text("active")),
    Column("created_by", Integer),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text),
)

customer_interactions = Table(
    "customer_interactions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("customer_id", Integer, nullable=False),
    Column("type", Text, nullable=False, server_default=text("visit")),
    Column("summary", Text, server_default=text("")),
    Column("outcome", Text, server_default=text("")),
    Column("conducted_by", Integer),
    Column("conducted_at", Text),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

opportunities = Table(
    "opportunities",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("customer_id", Integer, ForeignKey("customers.id"), nullable=False),
    Column("name", Text, nullable=False),
    Column("description", Text, server_default=text("")),
    Column("stage", Text, nullable=False, server_default=text("lead")),
    Column("probability", Integer, server_default=text("'0'")),
    Column("estimated_value", Float, server_default=text("'0.0'")),
    Column("actual_value", Float, server_default=text("'0.0'")),
    Column("assigned_to", Integer, ForeignKey("users.id")),
    Column("close_date", Text),
    Column("notes", Text, server_default=text("")),
    Column("is_active", Integer, server_default=text("'1'")),
    Column("created_by", Integer),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text),
)

asr_tasks = Table(
    "asr_tasks",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("task_id", Text, nullable=False, unique=True),
    Column("file_path", Text, server_default=text("")),
    Column("transcript", Text, server_default=text("")),
    Column("summary", Text, server_default=text("{}")),
    Column("status", Text, server_default=text("pending")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

admission_records = Table(
    "admission_records",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("hospital_name", Text, nullable=False),
    Column("department", Text, server_default=text("")),
    Column("product", Text, nullable=False),
    Column("status", Text, server_default=text("待提交")),
    Column("meeting_date", Text),
    Column("notes", Text, server_default=text("")),
    Column("rep_id", Integer),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text),
)

quotation_approvals = Table(
    "quotation_approvals",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("quotation_id", Text, nullable=False, unique=True),
    Column("rep_id", Integer, nullable=False),
    Column("product", Text, nullable=False),
    Column("amount", Float, nullable=False),
    Column("limit_amount", Float, server_default=text("'0.0'")),
    Column("status", Text, server_default=text("pending_approval")),
    Column("compliance_passed", Integer, server_default=text("'0'")),
    Column("review_notes", Text, server_default=text("")),
    Column("reviewed_by", Integer),
    Column("reviewed_at", Text),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

hcp_profiles = Table(
    "hcp_profiles",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", Text, nullable=False),
    Column("title", Text, server_default=text("")),
    Column("hospital", Text, server_default=text("")),
    Column("department", Text, server_default=text("")),
    Column("specialty", Text, server_default=text("")),
    Column("city", Text, server_default=text("")),
    Column("tier", Text, server_default=text("B")),
    Column("traits", Text, server_default=text("{}")),
    Column("prescription_volume", Float, server_default=text("'0'")),
    Column("influence_score", Float, server_default=text("'0.5'")),
    Column("digital_engagement", Float, server_default=text("'0.5'")),
    Column("is_active", Integer, server_default=text("'1'")),
    Column("created_by", Integer, ForeignKey("users.id")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("updated_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

hcp_interactions = Table(
    "hcp_interactions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("hcp_id", Integer, ForeignKey("hcp_profiles.id"), nullable=False),
    Column("interaction_type", Text, nullable=False),
    Column("content", Text, server_default=text("")),
    Column("response", Text, server_default=text("")),
    Column("outcome", Text, server_default=text("")),
    Column("strategy_used", Text, server_default=text("")),
    Column("conducted_by", Integer, ForeignKey("users.id")),
    Column("conducted_at", Text),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

hcp_simulations = Table(
    "hcp_simulations",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("hcp_id", Integer, ForeignKey("hcp_profiles.id"), nullable=False),
    Column("scenario", Text, nullable=False),
    Column("strategy", Text, server_default=text("")),
    Column("expected_outcome", Text, server_default=text("")),
    Column("confidence", Float, server_default=text("'0.5'")),
    Column("suggested_approach", Text, server_default=text("")),
    Column("key_concerns", Text, server_default=text("")),
    Column("recommended_topics", Text, server_default=text("")),
    Column("risk_factors", Text, server_default=text("")),
    Column("simulation_data", Text, server_default=text("{}")),
    Column("status", Text, server_default=text("completed")),
    Column("created_by", Integer, ForeignKey("users.id")),
    Column("created_at", Text, server_default=text("CURRENT_TIMESTAMP")),
)

Index("idx_customers_name", "name")
Index("idx_customers_hospital", "hospital")
Index("idx_interactions_customer", "customer_id")
Index("idx_interactions_time", "conducted_at")
Index("idx_opps_customer", "customer_id")
Index("idx_opps_stage", "stage")
Index("idx_opps_assigned", "assigned_to")
Index("idx_hcp_tier", "tier")
Index("idx_hcp_specialty", "specialty")
Index("idx_hcp_int_hcp", "hcp_id")
Index("idx_hcp_int_time", "conducted_at")
Index("idx_hcp_sim_hcp", "hcp_id")
Index("idx_asr_task_id", "task_id")
Index("idx_admission_rep", "rep_id")
Index("idx_admission_status", "status")
Index("idx_qa_status", "status")
