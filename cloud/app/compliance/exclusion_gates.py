"""排除闸模块：合规规则动态排除条件检查。

每个 Gate 是一个独立策略类，接收 (rule, data, context) 参数，
返回 True（排除，跳过检查）或 False（不排除，继续检查）。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class ExclusionGate(ABC):
    """排除闸基类，定义排除检查接口。"""

    @abstractmethod
    def is_active(self, context: dict[str, Any]) -> bool:
        """当前上下文是否启用该闸。"""

    @abstractmethod
    def evaluate(self, rule: dict[str, Any], data: dict[str, Any], context: dict[str, Any]) -> bool:
        """判断是否应跳过此规则。返回 True 表示排除（跳过检查）。"""

    @abstractmethod
    def get_reason(self) -> str:
        """返回跳过的自然语言原因。"""


class NewProductGracePeriodGate(ExclusionGate):
    """产品上线前 3 个月免数据考核。"""

    def is_active(self, context: dict[str, Any]) -> bool:
        return context.get("gates", {}).get("new_product_grace_period", False)

    def evaluate(self, rule: dict[str, Any], data: dict[str, Any], context: dict[str, Any]) -> bool:
        product_launch = data.get("product_launch_date")
        if not product_launch:
            return False
        launch = datetime.fromisoformat(product_launch) if isinstance(product_launch, str) else product_launch
        return (datetime.now() - launch).days < 90

    def get_reason(self) -> str:
        return "产品上线前 3 个月免数据考核"


class SeasonalAdjustmentGate(ExclusionGate):
    """季节性波动自动校准（参考去年同期值）。"""

    def is_active(self, context: dict[str, Any]) -> bool:
        return context.get("gates", {}).get("seasonal_adjustment", False)

    def evaluate(self, rule: dict[str, Any], data: dict[str, Any], context: dict[str, Any]) -> bool:
        current_val = data.get(rule.get("detection_field", ""))
        last_year_val = data.get("last_year_same_period")
        if current_val is None or last_year_val is None:
            return False
        try:
            ratio = float(current_val) / float(last_year_val) if float(last_year_val) != 0 else 1.0
            return 0.7 <= ratio <= 1.3
        except (TypeError, ValueError):
            return False

    def get_reason(self) -> str:
        return "季节性波动自动校准（参考去年同期值）"


class PolicyShockExemptionGate(ExclusionGate):
    """集采/医保新规临时豁免。"""

    def is_active(self, context: dict[str, Any]) -> bool:
        return context.get("gates", {}).get("policy_shock_exemption", False)

    def evaluate(self, rule: dict[str, Any], data: dict[str, Any], context: dict[str, Any]) -> bool:
        effective = context.get("policy_effective_date")
        if not effective:
            return False
        eff = datetime.fromisoformat(effective) if isinstance(effective, str) else effective
        return (datetime.now() - eff).days < 90

    def get_reason(self) -> str:
        return "集采/医保新规临时豁免"


class NaturalDisasterOverrideGate(ExclusionGate):
    """自然灾害期间自动调整。"""

    def is_active(self, context: dict[str, Any]) -> bool:
        return context.get("gates", {}).get("natural_disaster_override", False)

    def evaluate(self, rule: dict[str, Any], data: dict[str, Any], context: dict[str, Any]) -> bool:
        region = data.get("region")
        disaster_regions = context.get("disaster_regions", [])
        return region in disaster_regions

    def get_reason(self) -> str:
        return "自然灾害期间自动调整"


class DoctorAbsenceExemptionGate(ExclusionGate):
    """医生长期出差/请假免拜访考核。"""

    def is_active(self, context: dict[str, Any]) -> bool:
        return context.get("gates", {}).get("doctor_absence_exemption", False)

    def evaluate(self, rule: dict[str, Any], data: dict[str, Any], context: dict[str, Any]) -> bool:
        doctor_id = data.get("hcp_id") or data.get("doctor_id")
        absent_doctors = context.get("absent_doctors", [])
        return doctor_id in absent_doctors

    def get_reason(self) -> str:
        return "医生长期出差/请假免拜访考核"


class NewRepTrainingPeriodGate(ExclusionGate):
    """代表入职前 3 个月免考核。"""

    def is_active(self, context: dict[str, Any]) -> bool:
        return context.get("gates", {}).get("new_rep_training_period", False)

    def evaluate(self, rule: dict[str, Any], data: dict[str, Any], context: dict[str, Any]) -> bool:
        rep_id = data.get("rep_id") or data.get("user_id")
        hire_dates = context.get("rep_hire_dates", {})
        hire = hire_dates.get(str(rep_id))
        if not hire:
            return False
        hd = datetime.fromisoformat(hire) if isinstance(hire, str) else hire
        return (datetime.now() - hd).days < 90

    def get_reason(self) -> str:
        return "代表入职前 3 个月免考核"


class HolidayExemptionGate(ExclusionGate):
    """法定节假日豁免。"""

    def is_active(self, context: dict[str, Any]) -> bool:
        return context.get("gates", {}).get("holiday_exemption", False)

    def evaluate(self, rule: dict[str, Any], data: dict[str, Any], context: dict[str, Any]) -> bool:
        visit_date = data.get("visit_date") or data.get("created_at")
        if not visit_date:
            return False
        vd = datetime.fromisoformat(visit_date) if isinstance(visit_date, str) else visit_date
        holidays = context.get("holiday_dates", [])
        return vd.strftime("%Y-%m-%d") in holidays

    def get_reason(self) -> str:
        return "法定节假日豁免"


class ProductPhaseOutGate(ExclusionGate):
    """产品退市过渡期免考核。"""

    def is_active(self, context: dict[str, Any]) -> bool:
        return context.get("gates", {}).get("product_phase_out", False)

    def evaluate(self, rule: dict[str, Any], data: dict[str, Any], context: dict[str, Any]) -> bool:
        product = data.get("product") or data.get("product_name")
        phase_out_products = context.get("phase_out_products", [])
        return product in phase_out_products

    def get_reason(self) -> str:
        return "产品退市过渡期免考核"


class RegionAdjustmentGate(ExclusionGate):
    """区域市场调整期。"""

    def is_active(self, context: dict[str, Any]) -> bool:
        return context.get("gates", {}).get("region_adjustment", False)

    def evaluate(self, rule: dict[str, Any], data: dict[str, Any], context: dict[str, Any]) -> bool:
        region = data.get("region")
        adjustment_regions = context.get("adjustment_regions", [])
        return region in adjustment_regions

    def get_reason(self) -> str:
        return "区域市场调整期"


class SystemMigrationOverrideGate(ExclusionGate):
    """系统迁移/数据切换期。"""

    def is_active(self, context: dict[str, Any]) -> bool:
        return context.get("gates", {}).get("system_migration_override", False)

    def evaluate(self, rule: dict[str, Any], data: dict[str, Any], context: dict[str, Any]) -> bool:
        migration_active = context.get("migration_active", False)
        if not migration_active:
            return False
        affected_entities = context.get("migration_entities", [])
        entity = data.get("entity_id") or data.get("id")
        return entity in affected_entities

    def get_reason(self) -> str:
        return "系统迁移/数据切换期"


# 注册所有闸
EXCLUSION_GATES: dict[str, ExclusionGate] = {
    "new_product_grace_period": NewProductGracePeriodGate(),
    "seasonal_adjustment": SeasonalAdjustmentGate(),
    "policy_shock_exemption": PolicyShockExemptionGate(),
    "natural_disaster_override": NaturalDisasterOverrideGate(),
    "doctor_absence_exemption": DoctorAbsenceExemptionGate(),
    "new_rep_training_period": NewRepTrainingPeriodGate(),
    "holiday_exemption": HolidayExemptionGate(),
    "product_phase_out": ProductPhaseOutGate(),
    "region_adjustment": RegionAdjustmentGate(),
    "system_migration_override": SystemMigrationOverrideGate(),
}


def should_exclude(rule: dict[str, Any], data: dict[str, Any], context: dict[str, Any]) -> tuple[bool, str]:
    """遍历所有排除闸，返回 (是否排除, 原因)。

    Args:
        rule: 检测规则字典。
        data: 待检测数据载荷。
        context: 上下文，包含 gate 开关及参数。

    Returns:
        (True, reason) 当任意启用闸判定排除；否则 (False, "")。
    """
    for gate_name, gate in EXCLUSION_GATES.items():
        if gate.is_active(context) and gate.evaluate(rule, data, context):
            return True, gate.get_reason()
    return False, ""
