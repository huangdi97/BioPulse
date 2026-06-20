"""Rule category module."""

from enum import Enum


class RuleCategory(str, Enum):
    PROHIBITED_WORD = "prohibited_word"
    MANDATORY_CLAIM = "mandatory_claim"
    DOSAGE_LIMIT = "dosage_limit"
    COMPARATIVE_CLAIM = "comparative_claim"
