"""Compatibility package for DDL schemas.

New code should import from ``cloud.app.schemas.ddl``. This package keeps
``cloud.app.schema`` and ``cloud.app.schema.<domain>`` imports working.
"""

import importlib
import sys

from cloud.app.schemas.ddl import *  # noqa: F401,F403

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
