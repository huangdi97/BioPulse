import csv
import os
from datetime import datetime


EXPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "exports")


def export_csv(rows: list, columns: list, filename_prefix: str) -> str:
    os.makedirs(EXPORT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(EXPORT_DIR, f"{filename_prefix}_{timestamp}.csv")
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        for row in rows:
            writer.writerow([row.get(col, "") for col in columns])
    return filepath
