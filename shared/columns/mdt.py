"""Mdt module."""

TABLE_ASYNC_MDT_OPINIONS_COLS = frozenset(
    {
        "id",
        "decision_id",
        "contributor_id",
        "contributor_role",
        "opinion",
        "supporting_data",
        "stance",
        "confidence",
        "attachments",
        "is_final",
        "created_at",
        "updated_at",
    }
)

TABLE_MDT_OPINIONS_COLS = frozenset(
    {
        "id",
        "session_id",
        "participant_id",
        "round_number",
        "opinion",
        "summary",
        "sentiment",
        "confidence",
        "key_points",
        "ai_response_raw",
        "tokens_used",
        "created_at",
    }
)

TABLE_MDT_PARTICIPANTS_COLS = frozenset(
    {
        "id",
        "session_id",
        "agent_role_id",
        "role_name",
        "stance",
        "vote_weight",
        "created_at",
    }
)

TABLE_MDT_SESSIONS_COLS = frozenset(
    {
        "id",
        "title",
        "question",
        "context",
        "status",
        "consensus",
        "consensus_json",
        "round_count",
        "created_by",
        "created_at",
        "updated_at",
    }
)
