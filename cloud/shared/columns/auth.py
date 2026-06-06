TABLE_USERS_COLS = [
    "id",
    "username",
    "hashed_password",
    "role",
    "is_active",
    "created_at",
]

TABLE_USER_PROFILES_COLS = [
    "id",
    "user_id",
    "persona_type",
    "specialization",
    "experience_level",
    "preferred_content_types",
    "custom_tags",
    "embedding",
    "updated_at",
    "created_at",
]

TABLE_USER_BEHAVIORS_COLS = [
    "id",
    "user_id",
    "action_type",
    "target_type",
    "target_id",
    "metadata",
    "session_id",
    "duration_seconds",
    "created_at",
]

TABLE_USER_TEAM_COLS = ["id", "user_id", "team_id", "role", "created_at"]

TABLE_SYSTEM_CONFIGS_COLS = [
    "id",
    "key",
    "value",
    "description",
    "updated_by",
    "updated_at",
]

TABLE_DID_REGISTRY_COLS = [
    "id",
    "did",
    "entity_type",
    "entity_id",
    "public_key",
    "status",
    "metadata",
    "created_by",
    "created_at",
    "updated_at",
]

TABLE_VC_CREDENTIALS_COLS = [
    "id",
    "vc_id",
    "issuer_did",
    "subject_did",
    "credential_type",
    "claims",
    "issuance_date",
    "expiration_date",
    "proof",
    "status",
    "revoked_at",
    "created_at",
]

TABLE_DATA_MASKING_RULES_COLS = [
    "id",
    "rule_name",
    "field_pattern",
    "masking_type",
    "masking_config",
    "applies_to",
    "enabled",
    "created_by",
    "created_at",
    "updated_at",
]
