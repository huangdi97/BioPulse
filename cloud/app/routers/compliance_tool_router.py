"""Compliance/Agent tool endpoints — stub implementations for P2 agent activation.

Each endpoint returns plausible mock data for the corresponding gateway tool route.
The RuntimeCore execution loop calls these through ToolBridge → Gateway → HTTP forward.
Once real compliance services are fixed, replace the stubs with actual business logic.
"""

from __future__ import annotations

import logging
import random
import time
from datetime import datetime

from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/cloud", tags=["Compliance Tools"])

_SINCE = time.time()


def _ts() -> str:
    return datetime.now().isoformat()


def _ok(data: dict) -> dict:
    return {"success": True, "data": data, "error": None}


# ── Expense ──────────────────────────────────────────────────────────────


@router.post("/compliance/expense/check")
def expense_check(params: dict = {}):
    rep_id = params.get("rep_id", 1)
    return _ok(
        {
            "rep_id": rep_id,
            "status": "pass" if random.random() > 0.15 else "flag",
            "flagged_items": [],
            "total_claimed": round(random.uniform(500, 5000), 2),
            "total_allowed": round(random.uniform(500, 5000), 2),
            "checks": [
                {"rule": "receipt_exists", "passed": True},
                {"rule": "within_budget", "passed": True},
                {"rule": "date_in_range", "passed": True},
            ],
            "checked_at": _ts(),
        }
    )


# ── Visit ────────────────────────────────────────────────────────────────


@router.post("/compliance/visit/check")
def visit_check(params: dict = {}):
    visit_id = params.get("visit_id", 1)
    return _ok(
        {
            "visit_id": visit_id,
            "status": "pass",
            "verification": {
                "doctor_confirmed": True,
                "location_matches": True,
                "duration_plausible": True,
                "materials_provided": True,
            },
            "issues": [],
            "checked_at": _ts(),
        }
    )


# ── Distribution ─────────────────────────────────────────────────────────


@router.post("/compliance/distribution/trace")
def distribution_trace(params: dict = {}):
    product_id = params.get("product_id", "PROD-001")
    return _ok(
        {
            "product_id": product_id,
            "batch": ["BATCH-2026-01", "BATCH-2026-02"],
            "trace": [
                {"node": "manufacturer", "qty": 10000, "ts": "2026-05-01T00:00:00"},
                {"node": "distributor", "qty": 8000, "ts": "2026-05-10T00:00:00"},
                {"node": "hospital", "qty": 1200, "ts": "2026-05-20T00:00:00"},
            ],
            "anomalies": [],
            "traced_at": _ts(),
        }
    )


# ── Triangulation ────────────────────────────────────────────────────────


@router.post("/compliance/triangulation/check")
def triangulation_check(params: dict = {}):
    rep_id = params.get("rep_id", random.randint(1, 5))
    score = random.uniform(0.6, 1.0)
    decision = "pass" if score > 0.7 else ("flag" if score > 0.4 else "red_light")
    return _ok(
        {
            "rep_id": rep_id,
            "decision": decision,
            "confidence": round(score, 2),
            "dimensions": {
                "expense_consistency": round(random.uniform(0.6, 1.0), 2),
                "visit_consistency": round(random.uniform(0.6, 1.0), 2),
                "distribution_consistency": round(random.uniform(0.6, 1.0), 2),
            },
            "patterns_detected": [],
            "checked_at": _ts(),
        }
    )


# ── Audit Log ────────────────────────────────────────────────────────────


@router.post("/compliance/audit/log")
def audit_log(params: dict = {}):
    return _ok(
        {
            "log_id": random.randint(1000, 9999),
            "action": params.get("action", "check"),
            "status": "recorded",
            "timestamp": _ts(),
        }
    )


# ── HCP ──────────────────────────────────────────────────────────────────


_HCP_PROFILES = {
    1: {"name": "张伟", "specialty": "心内科", "hospital": "北京协和医院", "score": 85},
    2: {"name": "李娜", "specialty": "肿瘤科", "hospital": "上海瑞金医院", "score": 72},
    3: {"name": "王强", "specialty": "神经内科", "hospital": "广州中山医院", "score": 91},
}


@router.post("/hcp/profile/query")
def hcp_profile_query(params: dict = {}):
    hcp_id = params.get("hcp_id", 1)
    profile = _HCP_PROFILES.get(hcp_id)
    if not profile:
        return _ok({"found": False, "hcp_id": hcp_id})
    return _ok({"found": True, **profile, "preferences": {"contact_channel": "微信", "preferred_time": "上午"}, "last_visit": "2026-06-01T10:00:00"})


@router.post("/visit/history/query")
def visit_history_query(params: dict = {}):
    hcp_id = params.get("hcp_id", 1)
    return _ok(
        {
            "hcp_id": hcp_id,
            "total_visits": random.randint(3, 20),
            "last_30_days": random.randint(1, 5),
            "recent_visits": [
                {"date": "2026-06-01", "type": "学术推广", "duration_min": 25},
                {"date": "2026-05-20", "type": "信息沟通", "duration_min": 15},
            ],
        }
    )


# ── Competitor Intel ─────────────────────────────────────────────────────


@router.post("/competitor/intel/query")
def competitor_intel_query(params: dict = {}):
    company = params.get("company", "竞品A")
    return _ok(
        {
            "company": company,
            "recent_activities": [
                {"type": "新品上市", "product": "XX注射液", "date": "2026-05-15"},
                {"type": "会议赞助", "event": "全国心内年会", "date": "2026-06-01"},
            ],
            "market_share_change": -2.5,
            "last_updated": _ts(),
        }
    )


# ── Causal Attribution ───────────────────────────────────────────────────


@router.post("/causal/attribution/run")
def causal_attribution_run(params: dict = {}):
    return _ok(
        {
            "factors": [
                {"factor": "拜访频率变化", "contribution": 0.45, "direction": "positive"},
                {"factor": "竞品活动", "contribution": 0.30, "direction": "negative"},
                {"factor": "学术资料更新", "contribution": 0.25, "direction": "positive"},
            ],
            "root_cause": "拜访频率提升带动处方量增长",
            "confidence": round(random.uniform(0.7, 0.95), 2),
        }
    )


# ── Generate Brief ───────────────────────────────────────────────────────


@router.post("/visit/brief/generate")
def generate_brief(params: dict = {}):
    hcp_id = params.get("hcp_id", 1)
    hcp = _HCP_PROFILES.get(hcp_id, {"name": "未知", "specialty": "综合"})
    return _ok(
        {
            "hcp_name": hcp["name"],
            "specialty": hcp["specialty"],
            "brief_type": params.get("brief_type", "pre_call"),
            "key_points": [
                f"上次拜访讨论了{hcp['specialty']}领域最新进展",
                "建议推荐产品A的临床优势数据",
                "注意竞品B最近的促销活动",
            ],
            "suggested_materials": ["产品A临床指南摘要", "对比研究文献"],
            "generated_at": _ts(),
        }
    )


# ── Analysis Data Collection ─────────────────────────────────────────────


@router.post("/analysis/collect")
def analysis_collect(params: dict = {}):
    return _ok(
        {
            "records_collected": random.randint(10, 100),
            "date_range": {"from": "2026-05-01", "to": "2026-06-01"},
            "sources": ["expense", "visit", "distribution"],
            "collection_status": "complete",
        }
    )


@router.post("/analysis/pattern")
def analysis_pattern(params: dict = {}):
    return _ok(
        {
            "patterns_found": random.randint(0, 5),
            "patterns": [
                {"type": "expense_spike", "severity": "medium", "frequency": 3},
                {"type": "visit_gap", "severity": "low", "frequency": 1},
            ],
            "anomaly_score": round(random.uniform(0, 1), 2),
        }
    )


# ── Causal Inference ─────────────────────────────────────────────────────


@router.post("/causal/inference")
def causal_inference(params: dict = {}):
    return _ok(
        {
            "root_cause": "费用异常主要集中在一季度末，与季度考核周期吻合",
            "confidence": round(random.uniform(0.6, 0.9), 2),
            "supporting_evidence": [
                "Q1费用环比增长35%",
                "3月份费用占Q1总量的52%",
            ],
            "alternative_hypotheses": [
                {"hypothesis": "季度末冲刺导致费用集中", "likelihood": "high"},
                {"hypothesis": "新产品上市推广投入增加", "likelihood": "medium"},
            ],
        }
    )


# ── Narrative Generation ─────────────────────────────────────────────────


@router.post("/analysis/narrative")
def analysis_narrative(params: dict = {}):
    return _ok(
        {
            "title": "合规异常分析报告",
            "summary": "发现3个需要关注的风险模式，主要集中在费用合规领域。其中季度末费用集中问题是主要风险点。",
            "severity": "medium",
            "sections": [
                {"heading": "发现", "content": "季度末费用集中模式：Q1费用环比增长35%，其中3月占52%。"},
                {"heading": "根因", "content": "季度考核周期驱动的费用集中申报。"},
                {"heading": "建议", "content": "建议设置季度内费用预算平滑机制，避免季度末集中申报。"},
            ],
            "recommended_actions": ["设置月度费用预算上限", "季度末提前提醒", "大额费用预审批"],
            "generated_at": _ts(),
        }
    )


@router.post("/analysis/related-patterns")
def analysis_related_patterns(params: dict = {}):
    return _ok(
        {
            "related_patterns": [
                {"pattern": "费用集中申报", "affected_reps": ["代表A", "代表B", "代表C"], "correlation": 0.85},
                {"pattern": "拜访频率下降", "affected_reps": ["代表D", "代表E"], "correlation": 0.42},
            ],
            "cross_rep_anomalies": True,
        }
    )


# ── Red Light ────────────────────────────────────────────────────────────


@router.post("/compliance/red-light/trigger")
def red_light_trigger(params: dict = {}):
    return _ok(
        {
            "triggered": True,
            "level": params.get("level", "yellow"),
            "rep_id": params.get("rep_id", 1),
            "rule": params.get("rule", "费用超标"),
            "action_required": "需要区域经理审批",
            "triggered_at": _ts(),
        }
    )


# ── Compliance Check ─────────────────────────────────────────────────────


@router.post("/compliance/check")
def compliance_check(params: dict = {}):
    return _ok(
        {
            "status": "pass",
            "score": round(random.uniform(0.7, 1.0), 2),
            "rules_checked": 12,
            "violations_found": 0,
            "checked_at": _ts(),
        }
    )
