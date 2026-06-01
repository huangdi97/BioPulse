"""Research export service for PI profiles and quotations.

Provides separated export pipelines for the research mode, with distinct
watermarks and output directories to satisfy identity isolation requirement ⑤.
"""

import os
import json
import csv
import io
from typing import Any
from cloud.app.research_database import get_research_db

EXPORT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data",
    "exports",
    "research",
)


def _ensure_export_dir():
    """Create the research export directory if it does not exist."""
    os.makedirs(EXPORT_DIR, exist_ok=True)


def export_pi_csv() -> str:
    """Export all PI profiles as a CSV string with a research watermark header.

    The first line is a comment marking the data as research-related,
    satisfying the identity separation requirement for audit trails.

    Returns:
        The CSV content as a string.
    """
    _ensure_export_dir()
    db = get_research_db()
    try:
        rows = db.execute("SELECT * FROM research_pi_profiles").fetchall()
        output = io.StringIO()
        output.write("# 科研服务记录-学术合规\n")
        if rows:
            writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            for row in rows:
                writer.writerow(dict(row))
        content = output.getvalue()
        filepath = os.path.join(EXPORT_DIR, "pi_export.csv")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return content
    finally:
        db.close()


def export_quotation(quotation_id: int) -> dict[str, Any]:
    """Export a quotation record as a JSON dict with a research watermark.

    The watermark field is added to the output data to distinguish
    research-mode exports from pharma-mode exports.

    Args:
        quotation_id: The ID of the quotation to export.

    Returns:
        The quotation data dict including the watermark field.

    Raises:
        ValueError: If no quotation with the given ID exists.
    """
    _ensure_export_dir()
    db = get_research_db()
    try:
        row = db.execute(
            "SELECT * FROM research_quotations WHERE quotation_id = ?",
            (quotation_id,),
        ).fetchone()
        if not row:
            raise ValueError(f"Quotation {quotation_id} not found")
        data = dict(row)
        data["watermark"] = "科研服务记录-学术合规"
        filepath = os.path.join(EXPORT_DIR, f"quotation_{quotation_id}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return data
    finally:
        db.close()
