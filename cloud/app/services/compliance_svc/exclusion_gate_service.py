"""排除闸统一模块 — 10种排除闸从零散嵌入抽离为统一模块。"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass
class ExclusionContext:
    """排除闸评估上下文。"""

    rep_id: str
    region: str
    timestamp: str
    violation_type: str
    historical_data: Optional[dict] = None
    product_launch_date: Optional[str] = None
    policy_event: Optional[str] = None
    season: Optional[str] = None
    rep_created_at: Optional[str] = None


@dataclass
class ExclusionResult:
    """排除闸评估结果。"""

    exempt: bool
    reason: str
    gate_name: str
    checked_at: str

    def to_dict(self) -> dict:
        return {
            "exempt": self.exempt,
            "reason": self.reason,
            "gate_name": self.gate_name,
            "checked_at": self.checked_at,
        }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _days_between(start_str: str, end_str: str) -> int:
    """计算两个ISO日期之间的天数。"""
    from datetime import datetime

    try:
        start = datetime.fromisoformat(start_str)
        end = datetime.fromisoformat(end_str)
        return abs((end - start).days)
    except (ValueError, TypeError):
        return 999


# --- 前6种闸：有规则逻辑 ---


def gate_1_new_product_exemption(ctx: ExclusionContext) -> ExclusionResult:
    """新品导入免检 — 上市90天内不考核。"""
    if ctx.product_launch_date:
        days = _days_between(ctx.product_launch_date, ctx.timestamp)
        if days <= 90:
            return ExclusionResult(
                exempt=True,
                reason=f"新品导入免检期（{days}天/90天）",
                gate_name="新品导入免检",
                checked_at=_now(),
            )
    return ExclusionResult(exempt=False, reason="", gate_name="新品导入免检", checked_at=_now())


def gate_2_seasonal_calibration(ctx: ExclusionContext) -> ExclusionResult:
    """季节性校准 — 波动<20%自动豁免。"""
    if ctx.historical_data and ctx.season:
        current = ctx.historical_data.get("current_value", 0)
        historical = ctx.historical_data.get("historical_seasonal_avg", 0)
        if historical > 0 and current > 0:
            ratio = abs(current - historical) / historical
            if ratio < 0.2:
                return ExclusionResult(
                    exempt=True,
                    reason=f"季节性波动{ratio:.1%}<20%，自动校准",
                    gate_name="季节性校准",
                    checked_at=_now(),
                )
    return ExclusionResult(exempt=False, reason="", gate_name="季节性校准", checked_at=_now())


def gate_3_policy_exemption(ctx: ExclusionContext) -> ExclusionResult:
    """政策冲击豁免 — 集采/医保/新规期间临时豁免。"""
    policy_keywords = ["集采", "医保", "新规", "合规新规", "政策调整"]
    if ctx.policy_event:
        for kw in policy_keywords:
            if kw in ctx.policy_event:
                return ExclusionResult(
                    exempt=True,
                    reason=f"政策冲击豁免: {ctx.policy_event}",
                    gate_name="政策冲击豁免",
                    checked_at=_now(),
                )
    return ExclusionResult(exempt=False, reason="", gate_name="政策冲击豁免", checked_at=_now())


# 受灾区域列表（可外部配置）
_DISASTER_REGIONS: list[str] = []


def gate_4_disaster_exemption(ctx: ExclusionContext) -> ExclusionResult:
    """自然灾害豁免。"""
    if ctx.region in _DISASTER_REGIONS:
        return ExclusionResult(
            exempt=True,
            reason=f"受灾区域豁免: {ctx.region}",
            gate_name="自然灾害豁免",
            checked_at=_now(),
        )
    return ExclusionResult(exempt=False, reason="", gate_name="自然灾害豁免", checked_at=_now())


_SPECIAL_APPROVED_TYPES = ["特殊审批活动", "政府接待", "公益项目", "学术会议赞助"]


def gate_5_special_approval_exemption(ctx: ExclusionContext) -> ExclusionResult:
    """特殊审批活动豁免。"""
    if ctx.violation_type in _SPECIAL_APPROVED_TYPES:
        return ExclusionResult(
            exempt=True,
            reason=f"特殊审批活动豁免: {ctx.violation_type}",
            gate_name="特殊审批活动豁免",
            checked_at=_now(),
        )
    return ExclusionResult(exempt=False, reason="", gate_name="特殊审批活动豁免", checked_at=_now())


def gate_6_new_rep_exemption(ctx: ExclusionContext) -> ExclusionResult:
    """新代表试用期豁免 — 注册90天内不考核。"""
    if ctx.rep_created_at:
        days = _days_between(ctx.rep_created_at, ctx.timestamp)
        if days <= 90:
            return ExclusionResult(
                exempt=True,
                reason=f"新代表试用期（{days}天/90天）",
                gate_name="新代表试用期",
                checked_at=_now(),
            )
    return ExclusionResult(exempt=False, reason="", gate_name="新代表试用期", checked_at=_now())


# --- 后4种闸：预留接口 ---


def gate_7_low_base_calibration(ctx: ExclusionContext) -> ExclusionResult:
    """低基数校准（预留）。"""
    return ExclusionResult(exempt=False, reason="未实现", gate_name="低基数校准", checked_at=_now())


def gate_8_historical_trend_compensation(ctx: ExclusionContext) -> ExclusionResult:
    """历史趋势补偿（预留）。"""
    return ExclusionResult(exempt=False, reason="未实现", gate_name="历史趋势补偿", checked_at=_now())


def gate_9_competitor_interference(ctx: ExclusionContext) -> ExclusionResult:
    """竞品异常干扰排除（预留）。"""
    return ExclusionResult(exempt=False, reason="未实现", gate_name="竞品异常干扰排除", checked_at=_now())


def gate_10_data_integrity_check(ctx: ExclusionContext) -> ExclusionResult:
    """数据完整性检查（预留）。"""
    return ExclusionResult(exempt=False, reason="未实现", gate_name="数据完整性检查", checked_at=_now())


# --- 所有闸 ---

_ALL_GATES = [
    gate_1_new_product_exemption,
    gate_2_seasonal_calibration,
    gate_3_policy_exemption,
    gate_4_disaster_exemption,
    gate_5_special_approval_exemption,
    gate_6_new_rep_exemption,
    gate_7_low_base_calibration,
    gate_8_historical_trend_compensation,
    gate_9_competitor_interference,
    gate_10_data_integrity_check,
]


def evaluate_all(context: ExclusionContext) -> list[ExclusionResult]:
    """运行所有排除闸，返回全部结果。"""
    return [gate(context) for gate in _ALL_GATES]


def should_exempt(context: ExclusionContext) -> tuple[bool, str]:
    """任一闸通过则豁免。返回 (exempt, reason)。"""
    for result in evaluate_all(context):
        if result.exempt:
            return (True, result.reason)
    return (False, "")
