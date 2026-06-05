import hashlib
import json
import math
from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException, Request
from starlette import status

from cloud.app.repositories import (
    AuditChainEntriesRepository,
    ComplianceAuditRecordsRepository,
    TrainingCorrectionsRepository,
)
from cloud.app.services.base import BaseService
from shared.base import PaginatedResponse, success


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _n404(name="Resource"):
    raise HTTPException(status.HTTP_404_NOT_FOUND, f"{name} not found")


def _parse_json(raw: str, default=None):
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return default if default is not None else raw


def _call_ai(messages: list[dict], auth_header: str) -> dict:
    import urllib.request

    payload = {"messages": messages, "temperature": 0.7, "max_tokens": 2048}
    req = urllib.request.Request(
        "http://localhost:8000/ai/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": auth_header},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as rp:
        return json.loads(rp.read().decode("utf-8")).get("data", {})


class ReportGenerator(BaseService):
    def __init__(self, db):
        super().__init__(db)

    def review_record(self, record_id: int, body, uid: int) -> dict:
        audit_repo = ComplianceAuditRecordsRepository(self.db)
        chain_repo = AuditChainEntriesRepository(self.db)
        row = audit_repo.get_by_id(record_id)
        if not row:
            _n404("Record")
        n = _now()
        audit_repo.update(record_id, {"reviewed_by": uid, "reviewed_at": n})
        chain_repo.create(
            {
                "entity_type": "compliance_audit",
                "entity_id": str(record_id),
                "action": "review",
                "previous_hash": "",
                "current_hash": hashlib.sha256(
                    json.dumps(
                        {
                            "action": "review",
                            "record_id": record_id,
                            "notes": body.review_notes,
                        }
                    ).encode()
                ).hexdigest(),
                "payload": json.dumps(
                    {
                        "override_passed": body.override_passed,
                        "review_notes": body.review_notes,
                    },
                    ensure_ascii=False,
                ),
                "source": "",
                "created_by": uid,
                "performed_at": n,
            }
        )
        return success(data=audit_repo.get_by_id(record_id))

    def create_audit_chain(self, body, uid: int) -> dict:
        repo = AuditChainEntriesRepository(self.db)
        n = _now()
        prev_hash = ""
        latest_rows = repo.list_all(
            conditions=["entity_type=?", "entity_id=?"],
            params=[body.entity_type, body.entity_id],
            order_by="performed_at DESC",
        )
        if latest_rows:
            prev_hash = latest_rows[0]["current_hash"]
        current_hash = hashlib.sha256((prev_hash + json.dumps(body.payload, ensure_ascii=False, sort_keys=True)).encode("utf-8")).hexdigest()
        repo.create(
            {
                "entity_type": body.entity_type,
                "entity_id": body.entity_id,
                "action": body.action,
                "previous_hash": prev_hash,
                "current_hash": current_hash,
                "payload": json.dumps(body.payload, ensure_ascii=False),
                "metadata": json.dumps(body.metadata, ensure_ascii=False),
                "source": body.source,
                "created_by": uid,
                "performed_at": n,
            }
        )
        return success(
            data={
                "entity_type": body.entity_type,
                "entity_id": body.entity_id,
                "current_hash": current_hash,
                "previous_hash": prev_hash,
            }
        )

    def get_audit_chain(self, entity_type: str, entity_id: str) -> dict:
        repo = AuditChainEntriesRepository(self.db)
        rows = repo.list_all(
            conditions=["entity_type=?", "entity_id=?"],
            params=[entity_type, entity_id],
            order_by="performed_at ASC",
        )
        return success(data=rows)

    def verify_audit_chain(self, entity_type: str, entity_id: str) -> dict:
        repo = AuditChainEntriesRepository(self.db)
        rows = repo.list_all(
            conditions=["entity_type=?", "entity_id=?"],
            params=[entity_type, entity_id],
            order_by="performed_at ASC",
        )
        valid = True
        broken_at = None
        for i, row in enumerate(rows):
            expected_prev = rows[i - 1]["current_hash"] if i > 0 else ""
            if row["previous_hash"] != expected_prev:
                valid = False
                broken_at = row["id"]
                break
            payload = _parse_json(row["payload"], {}) if isinstance(row["payload"], str) else row["payload"]
            recomputed = hashlib.sha256((row["previous_hash"] + json.dumps(payload, ensure_ascii=False, sort_keys=True)).encode("utf-8")).hexdigest()
            if recomputed != row["current_hash"]:
                valid = False
                broken_at = row["id"]
                break
        return success(
            data={
                "entity_type": entity_type,
                "entity_id": entity_id,
                "valid": valid,
                "total_entries": len(rows),
                "broken_at": broken_at,
            }
        )

    def train_correction(self, record_id: int, request: Request, uid: int) -> dict:
        audit_repo = ComplianceAuditRecordsRepository(self.db)
        corrections_repo = TrainingCorrectionsRepository(self.db)
        row = audit_repo.get_by_id(record_id)
        if not row:
            _n404("Record")
        violations = _parse_json(row["violations"], [])
        sys_prompt = '你是一名医药合规培训教官。请根据以下合规审核违规记录，生成培训纠正方案。以JSON输出:{"title":"","description":"","category":"content_fix/training","severity":"low/medium/high/critical","action_items":[string]}'
        messages = [
            {"role": "system", "content": sys_prompt},
            {
                "role": "user",
                "content": f"内容类型: {row['message_type']}\n内容: {row['content']}\n违规: {json.dumps(violations, ensure_ascii=False)}\n风险等级: {row['risk_level']}",
            },
        ]
        auth = request.headers.get("Authorization", "")
        ai_data = _call_ai(messages, auth)
        ai_reply = ai_data.get("reply", "")
        parsed = _parse_json(ai_reply, {})
        if isinstance(parsed, dict):
            title = parsed.get("title", "培训纠正")
            desc = parsed.get("description", ai_reply[:300])
            cat = parsed.get("category", "general")
            sev = parsed.get("severity", "medium")
        else:
            title = "培训纠正"
            desc = ai_reply[:300]
            cat = "general"
            sev = "medium"
        n = _now()
        corrections_repo.create(
            {
                "audit_record_id": record_id,
                "title": title,
                "description": desc,
                "category": cat,
                "severity": sev,
                "status": "pending",
                "created_by": uid,
                "created_at": n,
            }
        )
        return success(
            data={
                "audit_record_id": record_id,
                "title": title,
                "description": desc,
                "category": cat,
                "severity": sev,
            }
        )

    def list_corrections(
        self,
        category: Optional[str],
        severity: Optional[str],
        status: Optional[str],
        page: int,
        page_size: int,
    ) -> dict:
        repo = TrainingCorrectionsRepository(self.db)
        conditions, params = [], []
        if category:
            conditions.append("category=?")
            params.append(category)
        if severity:
            conditions.append("severity=?")
            params.append(severity)
        if status:
            conditions.append("status=?")
            params.append(status)
        total, _, rows = repo.paginate(
            page=page,
            page_size=page_size,
            conditions=conditions or None,
            params=params or None,
            order_by="created_at DESC",
        )
        total_pages = math.ceil(total / max(page_size, 1))
        return success(
            data=PaginatedResponse(
                items=rows,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
            )
        )

    def update_correction(self, correction_id: int, body) -> dict:
        repo = TrainingCorrectionsRepository(self.db)
        row = repo.get_by_id(correction_id)
        if not row:
            _n404("Correction")
        updates = {}
        if body.status is not None:
            updates["status"] = body.status
        if body.assigned_to is not None:
            updates["assigned_to"] = body.assigned_to
        if updates:
            repo.update(correction_id, updates)
        return success(data=repo.get_by_id(correction_id))

    def dashboard(self) -> dict:
        audit_repo = ComplianceAuditRecordsRepository(self.db)
        corrections_repo = TrainingCorrectionsRepository(self.db)
        total_scans = audit_repo.count()
        passed = audit_repo.count(conditions=["passed=1"])
        pass_rate = round(passed / total_scans * 100, 1) if total_scans > 0 else 0.0
        today_str = datetime.now().strftime("%Y-%m-%d")
        today_violations = audit_repo.count(conditions=["passed=0", "DATE(created_at)=?"], params=[today_str])
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        weekly_total = audit_repo.count(conditions=["created_at >= ?"], params=[week_ago])
        high_risk_count = audit_repo.count(conditions=["risk_level='critical'"])
        by_type = self.db.execute(
            "SELECT message_type, COUNT(*) as cnt, AVG(score) as avg_score FROM compliance_audit_records GROUP BY message_type"
        ).fetchall()
        by_risk = self.db.execute(
            "SELECT risk_level, COUNT(*) as cnt FROM compliance_audit_records GROUP BY risk_level ORDER BY CASE risk_level WHEN 'critical' THEN 0 WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END"
        ).fetchall()
        all_failed = audit_repo.list_all(conditions=["passed=0"], order_by="created_at DESC")[:50]
        vcounts: dict[str, int] = {}
        for r in all_failed:
            for v in _parse_json(r["violations"], []):
                vcounts[v] = vcounts.get(v, 0) + 1
        top_v = sorted(vcounts.items(), key=lambda x: x[1], reverse=True)[:3]
        total_v = sum(vcounts.values()) or 1
        top_categories = [{"category": v, "count": c, "percentage": round(c / total_v * 100, 1)} for v, c in top_v]
        trend_7d = self.db.execute(
            "SELECT DATE(created_at) as d, COUNT(*) as cnt, SUM(passed) as passed_cnt FROM compliance_audit_records WHERE created_at >= ? GROUP BY d ORDER BY d",
            (week_ago,),
        ).fetchall()
        daily_trend = [{"date": (r["d"] or "")[-5:], "count": (r["cnt"] or 0) - (r["passed_cnt"] or 0)} for r in trend_7d]
        risk_map = {3: "critical", 2: "high", 1: "medium", 0: "low"}
        top_reps = []
        rep_rows = self.db.execute(
            "SELECT u.username, COUNT(*) as violation_count, MAX(CASE car.risk_level WHEN 'critical' THEN 3 WHEN 'high' THEN 2 WHEN 'medium' THEN 1 ELSE 0 END) as max_risk FROM compliance_audit_records car JOIN users u ON car.created_by = u.id WHERE car.passed = 0 GROUP BY car.created_by ORDER BY violation_count DESC LIMIT 3"
        ).fetchall()
        for r in rep_rows:
            top_reps.append(
                {
                    "repName": r["username"],
                    "violationCount": r["violation_count"],
                    "riskLevel": risk_map.get(r["max_risk"], "low"),
                }
            )
        recent_corrections = corrections_repo.list_all(order_by="created_at DESC")[:5]
        return success(
            data={
                "todayViolations": today_violations,
                "weeklyTotal": weekly_total,
                "processedRate": pass_rate,
                "highRiskCount": high_risk_count,
                "dailyTrend": daily_trend,
                "topCategories": top_categories,
                "topReps": top_reps,
                "by_type": [
                    {
                        "message_type": r["message_type"],
                        "count": r["cnt"],
                        "avg_score": round(r["avg_score"] or 0, 2),
                    }
                    for r in by_type
                ],
                "by_risk": [{"risk_level": r["risk_level"], "count": r["cnt"]} for r in by_risk],
                "top_violations": [{"violation": v, "count": c} for v, c in top_v],
                "recent_corrections": recent_corrections,
            }
        )
