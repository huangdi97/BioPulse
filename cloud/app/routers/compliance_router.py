from fastapi import APIRouter, Depends
from pydantic import BaseModel

from cloud.app.dependencies import get_db
from cloud.app.services.compliance_service import ComplianceService

router = APIRouter(prefix="", tags=["compliance"])


class ScanRequest(BaseModel):
    content: str


@router.get("/compliance-v2/dashboard")
def dashboard(db=Depends(get_db)):
    service = ComplianceService(db)
    data = service.dashboard()
    return {"code": 0, "data": data, "message": "success"}


@router.post("/compliance-v2/scan")
def scan(request: ScanRequest, db=Depends(get_db)):
    content = request.content.strip()
    passed = bool(content)
    risk_level = "low" if passed else "high"
    violations = []
    score = 100.0 if passed else 0.0
    return {
        "code": 0,
        "data": {"passed": passed, "riskLevel": risk_level, "violations": violations, "score": score},
        "message": "success",
    }


@router.get("/compliance-v2/records")
def list_records():
    return {"code": 0, "data": [], "message": "success"}


@router.get("/compliance-v2/records/{record_id}")
def get_record(record_id: int):
    return {"code": 0, "data": None, "message": "success"}
