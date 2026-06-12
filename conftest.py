import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

_SUBPROJECT_APPS = [
    "sales-assistant",
    "sales-coach",
    "assistant",
    "management",
    "opportunity",
    "pharma_intel",
    "clinical-ops",
    "market-access",
    "patient-engage",
    "competitor-intel",
    "academic-conference",
    "flying-inspection",
    "board",
]
for _sub in _SUBPROJECT_APPS:
    _app_dir = os.path.join(PROJECT_ROOT, _sub, "app")
    if os.path.isdir(_app_dir) and _app_dir not in sys.path:
        sys.path.insert(0, _app_dir)
