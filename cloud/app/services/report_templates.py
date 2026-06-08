"""报表模板字符串与工具函数，供 ReportGenerator 使用。"""

import json
import urllib.request
from datetime import datetime, timedelta

from fastapi import HTTPException, Request
from starlette import status

from cloud.app.repositories import ComplianceAuditRecordsRepository, TrainingCorrectionsRepository
from shared.base import success
from shared.config import settings as config_settings


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
    payload = {"messages": messages, "temperature": 0.7, "max_tokens": 2048}
    req = urllib.request.Request(
        f"{config_settings.ai_chat_url}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": auth_header},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as rp:
        return json.loads(rp.read().decode("utf-8")).get("data", {})


TRAINING_SYS_PROMPT = (
    "你是一名医药合规培训教官。请根据以下合规审核违规记录，生成培训纠正方案。"
    '以JSON输出:{"title":"","description":"","category":"content_fix/training",'
    '"severity":"low/medium/high/critical","action_items":[string]}'
)


def build_dashboard_data(db, audit_repo, corrections_repo) -> dict:
    total_scans = audit_repo.count()
    passed = audit_repo.count(conditions=["passed=1"])
    pass_rate = round(passed / total_scans * 100, 1) if total_scans > 0 else 0.0
    today_str = datetime.now().strftime("%Y-%m-%d")
    today_violations = audit_repo.count(conditions=["passed=0", "DATE(created_at)=?"], params=[today_str])
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    weekly_total = audit_repo.count(conditions=["created_at >= ?"], params=[week_ago])
    high_risk_count = audit_repo.count(conditions=["risk_level='critical'"])
    by_type = db.execute(
        "SELECT message_type, COUNT(*) as cnt, AVG(score) as avg_score FROM compliance_audit_records GROUP BY message_type"
    ).fetchall()
    by_risk = db.execute(
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
    trend_7d = db.execute(
        "SELECT DATE(created_at) as d, COUNT(*) as cnt, SUM(passed) as passed_cnt FROM compliance_audit_records WHERE created_at >= ? GROUP BY d ORDER BY d",
        (week_ago,),
    ).fetchall()
    daily_trend = [{"date": (r["d"] or "")[-5:], "count": (r["cnt"] or 0) - (r["passed_cnt"] or 0)} for r in trend_7d]
    risk_map = {3: "critical", 2: "high", 1: "medium", 0: "low"}
    top_reps = []
    rep_rows = db.execute(
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
    return {
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


class ReportTemplateMixin:
    """AI 纠偏模板生成和报表统计方法。"""

    def train_correction(self, record_id: int, request: Request, uid: int) -> dict:
        """基于违规记录生成 AI 纠偏训练条目。

        Args:
            record_id: 审计记录 ID
            request: HTTP 请求对象（用于获取 Authorization）
            uid: 操作者 ID

        Returns:
            含 title、description、category、severity 的纠偏记录
        """
        audit_repo = ComplianceAuditRecordsRepository(self.db)
        corrections_repo = TrainingCorrectionsRepository(self.db)
        row = audit_repo.get_by_id(record_id)
        if not row:
            _n404("Record")
        violations = _parse_json(row["violations"], [])
        messages = [
            {"role": "system", "content": TRAINING_SYS_PROMPT},
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

    def dashboard(self) -> dict:
        """合规仪表盘，汇总审计与纠偏统计。

        Returns:
            仪表盘统计数据
        """
        audit_repo = ComplianceAuditRecordsRepository(self.db)
        corrections_repo = TrainingCorrectionsRepository(self.db)
        return success(data=build_dashboard_data(self.db, audit_repo, corrections_repo))
