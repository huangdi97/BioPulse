"""Compliance module."""

import re
from typing import List

from pydantic import BaseModel

from shared.rule_category import RuleCategory  # noqa: F401


class ComplianceCheckResult(BaseModel):
    """Result of a compliance content check."""

    passed: bool
    violations: List[str] = []
    score: float


_COMPARATIVE_PATTERNS = re.compile(
    r"\b(better\s+than|superior\s+to|best|faster\s+than|stronger\s+than|more\s+effective|greatest)\b",
    re.IGNORECASE,
)
_NUMBER_PATTERN = re.compile(r"\d+\.?\d*")


def check_content(content: str, rules: List[dict]) -> ComplianceCheckResult:
    """Check content against a list of compliance rules.

    Each rule dict must have 'category' and 'keyword' keys.
    Optional 'max_value' key for dosage_limit rules.

    Args:
        content: The text content to check.
        rules: List of rule dicts with category, keyword, and optional max_value.

    Returns:
        ComplianceCheckResult with violations list and score.
    """
    violations: List[str] = []
    content_lower = content.lower()

    for rule in rules:
        category = rule["category"]
        keyword = rule.get("keyword", "")

        if category == RuleCategory.PROHIBITED_WORD:
            if keyword and keyword.lower() in content_lower:
                violations.append(f"Prohibited word found: '{keyword}'")

        elif category == RuleCategory.MANDATORY_CLAIM:
            if keyword and keyword.lower() not in content_lower:
                violations.append(f"Mandatory claim missing: '{keyword}'")

        elif category == RuleCategory.DOSAGE_LIMIT:
            max_value = rule.get("max_value")
            if max_value is not None:
                numbers = _NUMBER_PATTERN.findall(content)
                for num_str in numbers:
                    try:
                        if float(num_str) > float(max_value):
                            violations.append(f"Dosage exceeds limit: {num_str} > {max_value} '{keyword}'")
                    except (ValueError, OverflowError):
                        continue

        elif category == RuleCategory.COMPARATIVE_CLAIM:
            matches = _COMPARATIVE_PATTERNS.findall(content)
            if matches:
                joined = ", ".join(matches)
                violations.append(f"Comparative claims found: {joined}")

    total = len(rules)
    score = calculate_score(total, len(violations))
    passed = len(violations) == 0
    return ComplianceCheckResult(passed=passed, violations=violations, score=score)


def calculate_score(total: int, violations: int) -> float:
    """Calculate a compliance score between 0.0 and 1.0.

    Each violation reduces the score proportionally. Returns 1.0 when
    there are no rules to check against.

    Args:
        total: Total number of rules checked.
        violations: Number of violations found.

    Returns:
        A float between 0.0 and 1.0 inclusive.
    """
    if total == 0:
        return 1.0
    return round(max(0.0, 1.0 - violations / total), 2)
