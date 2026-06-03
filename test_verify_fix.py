# Verify the 3 bug fixes
import sqlite3
import sys

sys.path.insert(0, "/home/hermes/one-cloud-four-ends")

# 1. Export
print("=== 1. Export Test ===")
from cloud.app.services.export_service import ExportService

db1 = sqlite3.connect("/home/hermes/one-cloud-four-ends/data/cloud.db")
db1.row_factory = sqlite3.Row
svc = ExportService()
svc.db = db1
try:
    result = svc.export_customers()
    print(f"  ✅ Export OK: {result}")
except Exception as e:
    print(f"  ❌ Export Failed: {e}")

# 2. Opportunity Create
print("\n=== 2. Opportunity Create ===")
from typing import Optional

from pydantic import BaseModel

from opportunity.app.services.opportunity_service import OpportunityService


class MockOpp(BaseModel):
    name: str = "Verify-Opp"
    hospital: Optional[str] = "Test"
    product: Optional[str] = "Drug"
    estimated_value: Optional[float] = 50000
    stage: Optional[str] = "qualify"


db2 = sqlite3.connect("/home/hermes/one-cloud-four-ends/data/opportunity.db")
db2.row_factory = sqlite3.Row
svc2 = OpportunityService()
svc2.db = db2
try:
    opp_id = svc2.create_opportunity(MockOpp(), user_id=999)
    print(f"  ✅ Opportunity Created: id={opp_id}")
except Exception:
    import traceback

    traceback.print_exc()

# 3. SA HCP Create
print("\n=== 3. SA HCP Create ===")
from sales_assistant.app.services.hcp_service import HcpService


class MockHcp:
    def model_dump(self):
        return {"name": "Verify-HCP", "hospital": "Test", "specialty": "cardiology"}


db3 = sqlite3.connect("/home/hermes/one-cloud-four-ends/data/sales_assistant.db")
db3.row_factory = sqlite3.Row
svc3 = HcpService()
svc3.db = db3
try:
    hcp_id = svc3.create_hcp(MockHcp(), user_id=999)
    print(f"  ✅ HCP Created: id={hcp_id}")
except Exception:
    import traceback

    traceback.print_exc()

print("\n=== All tests done ===")
