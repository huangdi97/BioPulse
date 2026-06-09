import importlib


class TestImports:
    def test_import_main_ok(self):
        mod = importlib.import_module("patient-engage.app.main")
        assert mod.app is not None
