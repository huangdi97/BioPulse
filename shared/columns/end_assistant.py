"""End assistant module."""

TABLE_ASSISTANT_HCP_COLS = frozenset(
    {
        "id",
        "name",
        "hospital",
        "department",
        "title",
        "specialty",
        "phone",
        "wechat",
        "email",
        "level",
        "is_active",
        "created_by",
        "created_at",
        "updated_at",
    }
)

TABLE_HCP_LOCATION_COLS = frozenset(
    {
        "id",
        "hcp_id",
        "address",
        "latitude",
        "longitude",
        "is_primary",
        "notes",
        "is_active",
        "created_by",
        "created_at",
        "updated_at",
    }
)

TABLE_HEALTH_RADAR_COLS = frozenset(
    {
        "id",
        "patient_name",
        "age",
        "gender",
        "diagnosis",
        "risk_factors",
        "medication_history",
        "score",
        "assessment_date",
        "notes",
        "is_active",
        "created_by",
        "created_at",
        "updated_at",
    }
)

TABLE_KNOWLEDGE_BASE_COLS = frozenset(
    {
        "id",
        "title",
        "category",
        "content",
        "tags",
        "source",
        "difficulty",
        "is_active",
        "created_by",
        "created_at",
        "updated_at",
    }
)

TABLE_MEDIA_FILE_COLS = frozenset(
    {
        "id",
        "file_type",
        "original_name",
        "storage_path",
        "mime_type",
        "file_size",
        "transcript",
        "analysis_result",
        "is_active",
        "created_by",
        "created_at",
    }
)

TABLE_PAPER_INTEGRITY_COLS = frozenset(
    {
        "id",
        "pubmed_id",
        "doi",
        "title",
        "integrity_score",
        "retraction_warning",
        "concerns",
        "flags",
        "checked_at",
        "check_count",
        "is_active",
        "created_by",
        "created_at",
        "updated_at",
    }
)

TABLE_RESEARCH_TRAIL_COLS = frozenset(
    {
        "id",
        "hcp_name",
        "topic",
        "paper_title",
        "authors",
        "journal",
        "pub_date",
        "pubmed_id",
        "url",
        "summary",
        "relevance",
        "is_active",
        "created_by",
        "created_at",
        "updated_at",
    }
)

TABLE_SURGERY_REMINDER_COLS = frozenset(
    {
        "id",
        "patient_name",
        "surgery_type",
        "surgery_date",
        "hospital",
        "department",
        "surgeon_name",
        "pre_op_notes",
        "post_op_notes",
        "status",
        "reminder_before",
        "last_notified_at",
        "notification_status",
        "is_active",
        "created_by",
        "created_at",
        "updated_at",
    }
)

TABLE_SYNC_QUEUE_COLS = frozenset(
    {
        "id",
        "client_id",
        "action",
        "entity_type",
        "entity_id",
        "payload",
        "status",
        "client_created_at",
        "synced_at",
        "created_by",
        "created_at",
    }
)

TABLE_TASK_COLS = frozenset(
    {
        "id",
        "hcp_id",
        "title",
        "description",
        "priority",
        "status",
        "due_date",
        "created_by",
        "created_at",
    }
)

TABLE_TREND_ANALYSIS_COLS = frozenset(
    {
        "id",
        "topic",
        "analysis_type",
        "period",
        "data_summary",
        "result",
        "confidence",
        "analyzed_at",
        "created_by",
        "created_at",
    }
)

TABLE_USER_BOOKMARK_COLS = frozenset(
    {
        "id",
        "entity_type",
        "entity_id",
        "title",
        "notes",
        "created_by",
        "created_at",
    }
)

TABLE_VISIT_RECORD_COLS = frozenset(
    {
        "id",
        "hcp_id",
        "visit_type",
        "summary",
        "detail",
        "feedback",
        "next_action",
        "mood",
        "is_completed",
        "visit_date",
        "created_by",
        "created_at",
    }
)
