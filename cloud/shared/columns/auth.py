# ruff: noqa: F822

import shared.columns as _columns

__all__ = (
    "TABLE_DATA_MASKING_RULES_COLS",
    "TABLE_DID_REGISTRY_COLS",
    "TABLE_SYSTEM_CONFIGS_COLS",
    "TABLE_USER_BEHAVIORS_COLS",
    "TABLE_USER_PROFILES_COLS",
    "TABLE_USER_TEAM_COLS",
    "TABLE_USERS_COLS",
    "TABLE_VC_CREDENTIALS_COLS",
)

globals().update({name: getattr(_columns, name) for name in __all__})
