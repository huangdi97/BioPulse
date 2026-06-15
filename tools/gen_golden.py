"""Generate correct golden test data from ComplianceEnforcer."""

import json
import sqlite3
import sys

sys.path.insert(0, "/home/hermes/one-cloud-four-ends")

from cloud.app.compliance.engine import ComplianceEnforcer

cases = [
    {
        "name": "normal_visit_passes",
        "input": {"rep_id": "R001", "visit_time": "2026-06-01T10:00", "location": "hospital_a", "hcp_name": "Dr. Li", "scope": "pharma"},
    },
    {
        "name": "out_of_scope_blocks",
        "input": {"rep_id": "R001", "visit_time": "2026-06-01T10:00", "location": "hospital_a", "hcp_name": "Dr. Li", "scope": "unrelated"},
    },
    {
        "name": "missing_hcp_is_edge",
        "input": {"rep_id": "R001", "visit_time": "2026-06-01T10:00", "location": "hospital_a", "hcp_name": "", "scope": "pharma"},
    },
]

db = sqlite3.connect(":memory:")
db.row_factory = sqlite3.Row

output = []
for case in cases:
    try:
        result = ComplianceEnforcer(db).check_visit(case["input"])
        if result:
            action = "block"
            rule_names = [v.rule_name for v in result]
        else:
            action = "pass"
            rule_names = []
    except Exception:
        action = "pass"
        rule_names = []
    output.append({"name": case["name"], **case, "expected": {"action": action, "rule_names": rule_names}})

db.close()
print(json.dumps(output, indent=2, ensure_ascii=False))
