import importlib.util
import os

_OLD_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "schema.py")


def _load_old_schema():
    """spec = importlib.util.spec_from_file_location("cloud.app.schema_old", _OLD_FILE)"""
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_old_mod = _load_old_schema()
for _name in dir(_old_mod):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_old_mod, _name)

__all__ = [_n for _n in dir() if not _n.startswith("_")]
