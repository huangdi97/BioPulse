"""Weight calculation and compliance helpers for federated node aggregation."""

import csv
import io
from datetime import datetime, timedelta


def since_datetime(days: int) -> str:
    return (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")


def audit_log_to_dict(r) -> dict:
    return {
        k: r[k]
        for k in (
            "id",
            "user_id",
            "action",
            "entity_type",
            "entity_id",
            "detail",
            "source_end",
            "ip_address",
            "created_at",
        )
    }


def contribution_to_dict(r) -> dict:
    return {
        k: r[k]
        for k in (
            "id",
            "contributor_did",
            "contribution_type",
            "payload_hash",
            "payload_summary",
            "weight",
            "verified",
            "verified_by",
            "audit_chain_hash",
            "created_at",
        )
    }


def to_csv(rows: list[dict], fieldnames: list[str]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def is_node_compliant(status: str, reliability_score: float | None) -> bool:
    return status == "online" and (reliability_score or 0) >= 0.8
