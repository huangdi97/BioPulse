"""Shared DB row-level security and schema-per-tenant isolation utilities."""

import base64
import json
import re
from contextvars import ContextVar
from typing import Any, Callable

try:
    from fastapi import APIRouter, Request
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.responses import Response
except ModuleNotFoundError:

    class APIRouter:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs) -> None:
            pass

        def get(self, *args, **kwargs):
            def decorator(func):
                return func

            return decorator

    class Request:  # type: ignore[no-redef]
        pass

    class Response:  # type: ignore[no-redef]
        pass

    class BaseHTTPMiddleware:  # type: ignore[no-redef]
        pass


CURRENT_TENANT: ContextVar[str | None] = ContextVar("current_tenant", default=None)
IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _validate_identifier(identifier: str) -> str:
    if not IDENTIFIER_PATTERN.match(identifier):
        raise ValueError(f"Invalid SQL identifier: {identifier}")
    return identifier


def _decode_jwt_payload(token: str) -> dict[str, Any]:
    parts = token.split(".")
    if len(parts) < 2:
        return {}
    payload = parts[1]
    padding = "=" * (-len(payload) % 4)
    try:
        raw = base64.urlsafe_b64decode(payload + padding)
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return {}


class TenantContextMiddleware(BaseHTTPMiddleware):
    """Extract tenant_id from JWT and bind it to request-local context."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        tenant_id = TenantIsolationService.extract_tenant_from_request(request)
        token = CURRENT_TENANT.set(tenant_id)
        request.state.tenant_id = tenant_id
        try:
            return await call_next(request)
        finally:
            CURRENT_TENANT.reset(token)


class TenantIsolationService:
    """Tenant isolation facade for shared DB RLS and compliance schemas."""

    DEFAULT_TENANT = "tenant-default"
    COMPLIANCE_TABLES = {
        "flying_inspection",
        "compliance_audit",
        "compliance_evidence",
        "inspection_remediation",
    }

    def __init__(self, current_tenant: str | None = None) -> None:
        if current_tenant:
            self.set_current_tenant(current_tenant)

    @staticmethod
    def current_tenant() -> str:
        return CURRENT_TENANT.get() or TenantIsolationService.DEFAULT_TENANT

    @staticmethod
    def set_current_tenant(tenant_id: str) -> None:
        CURRENT_TENANT.set(tenant_id)

    @staticmethod
    def extract_tenant_from_request(request: Request) -> str:
        auth_header = request.headers.get("authorization", "")
        if auth_header.lower().startswith("bearer "):
            claims = _decode_jwt_payload(auth_header.split(" ", 1)[1].strip())
            tenant_id = claims.get("tenant_id") or claims.get("tid") or claims.get("tenant")
            if tenant_id:
                return str(tenant_id)
        return request.headers.get("x-tenant-id", TenantIsolationService.DEFAULT_TENANT)

    def tenant_column_ddl(self, table_name: str, column_type: str = "TEXT") -> str:
        table_name = _validate_identifier(table_name)
        return f"ALTER TABLE {table_name} ADD COLUMN tenant_id {column_type} NOT NULL DEFAULT '{self.current_tenant()}';"

    def rls_policy_ddl(self, table_name: str) -> list[str]:
        table_name = _validate_identifier(table_name)
        return [
            f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;",
            (f"CREATE POLICY {table_name}_tenant_isolation ON {table_name} USING (tenant_id = current_setting('app.current_tenant')::text);"),
        ]

    def tenant_filter_clause(self, alias: str | None = None, placeholder: str = ":tenant_id") -> str:
        column = f"{_validate_identifier(alias)}.tenant_id" if alias else "tenant_id"
        return f"{column} = {placeholder}"

    def inject_tenant_filter(self, sql: str, alias: str | None = None) -> str:
        """Inject tenant predicate into a simple SELECT query."""

        predicate = self.tenant_filter_clause(alias=alias)
        stripped = sql.strip().rstrip(";")
        lowered = stripped.lower()
        if not lowered.startswith("select"):
            raise ValueError("Tenant filter injection only supports SELECT queries")
        boundary = self._first_clause_index(
            lowered,
            [" group by ", " having ", " order by ", " limit ", " offset "],
        )
        head = stripped[:boundary] if boundary is not None else stripped
        tail = stripped[boundary:] if boundary is not None else ""
        if " where " in lowered:
            return f"{head} AND {predicate}{tail}"
        if boundary is not None:
            return f"{head} WHERE {predicate}{tail}"
        return f"{stripped} WHERE {predicate}"

    @staticmethod
    def _first_clause_index(lowered_sql: str, clauses: list[str]) -> int | None:
        indexes = [lowered_sql.index(clause) for clause in clauses if clause in lowered_sql]
        return min(indexes) if indexes else None

    def scoped_params(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return {**(params or {}), "tenant_id": self.current_tenant()}

    def schema_name_for_tenant(self, tenant_id: str | None = None, purpose: str = "compliance") -> str:
        raw = tenant_id or self.current_tenant()
        normalized = re.sub(r"[^A-Za-z0-9_]", "_", raw).strip("_").lower()
        if not normalized:
            normalized = "default"
        return f"{purpose}_{normalized}"

    def compliance_schema_ddl(self, tenant_id: str | None = None) -> list[str]:
        schema = self.schema_name_for_tenant(tenant_id=tenant_id, purpose="compliance")
        statements = [f"CREATE SCHEMA IF NOT EXISTS {schema};"]
        statements.extend(
            f"CREATE TABLE IF NOT EXISTS {schema}.{table_name} ("
            "id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, payload JSONB, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            ");"
            for table_name in sorted(self.COMPLIANCE_TABLES)
        )
        return statements

    def isolation_status(self) -> dict[str, Any]:
        tenant_id = self.current_tenant()
        return {
            "tenant_id": tenant_id,
            "shared_db_rls": {
                "enabled": True,
                "strategy": "shared_database_row_level_security",
                "required_column": "tenant_id",
                "query_scope": self.tenant_filter_clause(),
            },
            "compliance_isolation": {
                "enabled": True,
                "strategy": "schema_per_tenant",
                "schema": self.schema_name_for_tenant(tenant_id),
                "tables": sorted(self.COMPLIANCE_TABLES),
            },
            "middleware": {
                "enabled": True,
                "tenant_source": "JWT claim tenant_id, tid, or tenant",
                "fallback_header": "x-tenant-id",
            },
        }


router = APIRouter(prefix="/api/tenant/isolation", tags=["多租户隔离"])


@router.get("/status", tags=["多租户隔离"])
def tenant_isolation_status():
    return TenantIsolationService().isolation_status()
