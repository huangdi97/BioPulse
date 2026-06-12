"""Compatibility package for DDL schemas.

New code should import from ``cloud.app.schemas.ddl``. This package keeps
``cloud.app.schema`` and ``cloud.app.schema.<domain>`` imports working.
"""

import importlib
import sys

from cloud.app.schemas.ddl import *  # noqa: F401,F403

__all__ = [
    "AGENT_SQL",
    "AUDIT_SQL",
    "AUTH_SQL",
    "COLLAB_SQL",
    "CONTENT_SQL",
    "CUSTOMER_SQL",
    "DECISION_SQL",
    "DID_SQL",
    "EVENTBUS_SQL",
    "EXEC_SQL",
    "HCP_SQL",
    "KG_SQL",
    "MARKET_SQL",
    "MDT_SQL",
    "MEMORY_SQL",
    "MISC_SQL",
    "PRIVACY_SQL",
    "ROUTE_SQL",
    "SCHEMA_SQL",
    "SOAP_SQL",
    "TASK_SQL",
    "TRAINING_SQL",
    "USERPROFILE_SQL",
    "WORKINGMEM_SQL",
    "WORLDTREE_SQL",
]

_DDL_MODULES = [
    "agent",
    "audit",
    "auth",
    "collab",
    "content",
    "customer",
    "decision",
    "did",
    "eventbus",
    "exec",
    "hcp",
    "kg",
    "market",
    "mdt",
    "memory",
    "misc",
    "privacy",
    "route",
    "soap",
    "task",
    "training",
    "userprofile",
    "workingmem",
    "worldtree",
]

for _module_name in _DDL_MODULES:
    sys.modules[f"{__name__}.{_module_name}"] = importlib.import_module(f"cloud.app.schemas.ddl.{_module_name}")

del importlib, sys, _module_name
