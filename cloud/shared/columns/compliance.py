# ruff: noqa: F822

import shared.columns as _columns

__all__ = (
    "TABLE_AUDIT_CHAIN_BLOCKS_COLS",
    "TABLE_AUDIT_CHAIN_ENTRIES_COLS",
    "TABLE_AUDIT_LOGS_COLS",
    "TABLE_BENCHMARK_REPORTS_COLS",
    "TABLE_COMPLIANCE_AUDIT_RECORDS_COLS",
    "TABLE_COMPLIANCE_RULES_COLS",
    "TABLE_FED_AUDIT_CONTRIBUTIONS_COLS",
    "TABLE_NMPA_COMPLIANCE_LOGS_COLS",
    "TABLE_SENSOR_SESSIONS_COLS",
)

globals().update({name: getattr(_columns, name) for name in __all__})
