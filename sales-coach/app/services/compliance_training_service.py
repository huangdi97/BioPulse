"""合规培训材料审核服务。"""

from sales_coach.app.schemas.compliance_training import (
    ComplianceCheckResult,
    TrainingMaterial,
    Violation,
)

_MATERIALS: dict[str, TrainingMaterial] = {}
_RESULTS: dict[str, ComplianceCheckResult] = {}

_OFF_LABEL_TERMS = ("超适应症", "说明书外", "未获批", "扩大适应症", "适用于所有患者")
_MISLEADING_COMPARISON_TERMS = ("显著优于", "全面领先", "最佳", "唯一", "完胜", "远超", "没有竞品")
_CLAIM_TERMS = ("显著改善", "降低风险", "提升疗效", "安全性更好", "改善预后")
_EVIDENCE_TERMS = ("数据", "研究", "文献", "RCT", "真实世界", "指南", "来源", "p值", "CI", "%")


def save_training_material(material: TrainingMaterial) -> TrainingMaterial:
    """保存待检查材料。"""

    _MATERIALS[material.id] = material
    return material


def check_compliance(material_id: str) -> ComplianceCheckResult:
    """检查超适应症推广、误导性比较和缺乏数据支持。"""

    material = _MATERIALS.get(material_id)
    content = material.content if material else ""
    violations: list[Violation] = []
    if _contains_any(content, _OFF_LABEL_TERMS):
        violations.append(
            Violation(
                type="超适应症推广",
                description="材料包含可能超出批准适应症或说明书范围的表述。",
                suggestion="删除说明书外推广内容，改为使用已批准适应症和标准表述。",
            )
        )
    if _contains_any(content, _MISLEADING_COMPARISON_TERMS):
        violations.append(
            Violation(
                type="误导性比较",
                description="材料包含绝对化或可能误导的竞品比较表述。",
                suggestion="使用客观、可验证且有依据的比较，避免绝对化措辞。",
            )
        )
    if _contains_any(content, _CLAIM_TERMS) and not _contains_any(content, _EVIDENCE_TERMS):
        violations.append(
            Violation(
                type="缺乏数据支持",
                description="材料提出疗效或安全性获益，但未提供明确数据或来源。",
                suggestion="补充研究名称、关键数据、来源和适用人群，或弱化获益表述。",
            )
        )
    risk_level = _risk_level(violations)
    result = ComplianceCheckResult(
        material_id=material_id,
        passed=not violations,
        violations=violations,
        risk_level=risk_level,
    )
    _RESULTS[material_id] = result
    return result


def get_compliance_result(material_id: str) -> ComplianceCheckResult:
    """获取材料最近一次合规检查结果。"""

    if material_id not in _RESULTS:
        return check_compliance(material_id)
    return _RESULTS[material_id]


def _contains_any(content: str, terms: tuple[str, ...]) -> bool:
    normalized = content.lower()
    return any(term.lower() in normalized for term in terms)


def _risk_level(violations: list[Violation]) -> str:
    if len(violations) >= 2:
        return "high"
    if violations:
        return "medium"
    return "low"
