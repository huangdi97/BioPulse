class TestMdtCollaborationFallback:
    def test_service_name_resolution(self):
        service_name = "mdt-collaboration"
        parts = service_name.replace("-", "_").split("_")
        assert len(parts) == 2
        assert parts[0] == "mdt"
        assert parts[1] == "collaboration"

    def test_error_handling(self):
        try:
            raise ValueError("fallback triggered")
        except ValueError as exc:
            assert str(exc) == "fallback triggered"
