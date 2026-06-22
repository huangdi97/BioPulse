"""Cloud package smoke tests."""


def test_cloud_schema_imports():
    from cloud.app.schemas.ddl import SCHEMA_SQL

    assert "CREATE TABLE" in SCHEMA_SQL


def test_cloud_compliance_engine_imports_and_instantiates():
    from cloud.app.compliance import HolographicAuditEngine

    engine = HolographicAuditEngine()

    assert isinstance(engine, HolographicAuditEngine)
