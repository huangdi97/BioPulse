import importlib

import pytest

SHARED_COLUMN_MODULES = (
    "agent",
    "audit",
    "auth",
    "coach",
    "collab",
    "content",
    "customer",
    "decision",
    "did",
    "end_assistant",
    "end_sales_assistant",
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
)

CLOUD_SHARED_COLUMN_MODULES = (
    "auth",
    "common",
    "compliance",
    "pharma",
    "research",
    "sales",
)


def _public_exports(module):
    names = getattr(module, "__all__", None)
    if names is None:
        names = [name for name in vars(module) if not name.startswith("_")]
    return {name: getattr(module, name) for name in names}


def _expected_star_exports(package_name, module_names):
    exports = {}
    for module_name in module_names:
        module = importlib.import_module(f"{package_name}.{module_name}")
        exports.update(_public_exports(module))
    return exports


@pytest.mark.parametrize(
    ("package_name", "module_names"),
    (
        ("shared.columns", SHARED_COLUMN_MODULES),
        ("cloud.shared.columns", CLOUD_SHARED_COLUMN_MODULES),
    ),
)
def test_columns_package_exports_match_previous_star_imports(package_name, module_names):
    package = importlib.import_module(package_name)
    expected_exports = _expected_star_exports(package_name, module_names)

    assert set(package.__all__) == set(expected_exports)

    namespace = {}
    exec(f"from {package_name} import *", namespace)

    for name, value in expected_exports.items():
        assert getattr(package, name) is value
        assert namespace[name] is value
