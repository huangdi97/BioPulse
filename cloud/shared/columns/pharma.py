# ruff: noqa: F822

import shared.columns as _columns

__all__ = (
    "TABLE_CONTENTS_COLS",
    "TABLE_CUSTOMER_INTERACTIONS_COLS",
    "TABLE_CUSTOMERS_COLS",
    "TABLE_HCP_INTERACTIONS_COLS",
    "TABLE_HCP_PROFILES_COLS",
    "TABLE_HCP_SIMULATIONS_COLS",
    "TABLE_NOTIFICATION_TEMPLATES_COLS",
    "TABLE_NOTIFICATIONS_COLS",
    "TABLE_OPPORTUNITIES_COLS",
    "TABLE_SUPPLY_CHAIN_ITEMS_COLS",
)

globals().update({name: getattr(_columns, name) for name in __all__})
