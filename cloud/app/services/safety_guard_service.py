"""三层安全架构 Layer1：基于轻量模型的输入/输出安全检测。"""

import logging
import re
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError

logger = logging.getLogger(__name__)

_INPUT_KEYWORDS = [
    "忽略以上",
    "忘记所有",
    "Ignore all",
    "System:",
    "ignore above",
    "forget everything",
    "system prompt",
    "忽略之前的",
    "Ignore previous",
    "DAN",
    "越狱",
    "告诉我你的系统提示",
    "tell me your system prompt",
]

_HALLUCINATION_PATTERNS = [
    (re.compile(r"保证.*成功"), "guarantee_success"),
    (re.compile(r"一定.*可以"), "absolute_claim"),
    (re.compile(r"100%"), "percentage_claim"),
    (re.compile(r"绝对没问题"), "absolute_no_problem"),
    (re.compile(r"肯定没.*问题"), "confident_no_issue"),
]

_PHONE_PATTERN = re.compile(r"1[3-9]\d{9}")
_ID_CARD_PATTERN = re.compile(r"\d{17}[\dXx]")
_BANK_CARD_PATTERN = re.compile(r"\b\d{16,19}\b")


class SafetyGuard:
    """三层安全架构 Layer1：输入提示注入检测 + 输出 PII/幻觉检测。

    输入检测同时使用关键词匹配和轻量 transformer 文本分类模型；
    输出检测仅使用正则表达式，不调用模型。
    """

    def __init__(
        self,
        model_name: str = "ProtectAI/deberta-v3-base-prompt-injection",
        timeout: int = 10,
    ):
        self._model_name = model_name
        self._timeout = timeout
        self._pipe = None
        self._available = False

    def _load_pipeline(self) -> bool:
        if self._pipe is not None:
            return True
        try:
            from transformers import pipeline

            def _load():
                return pipeline("text-classification", self._model_name)

            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(_load)
                self._pipe = future.result(timeout=self._timeout)
                self._available = True
                return True
        except (FuturesTimeoutError, Exception):
            logger.warning(
                "SafetyGuard pipeline load failed or timed out for model=%s, degrading",
                self._model_name,
            )
            self._pipe = None
            self._available = False
            return False

    def check_input(self, text: str) -> dict:
        """检测输入文本是否包含提示注入或越狱。

        Returns:
            {'safe': bool, 'risk': 'prompt_injection'|'jailbreak'|'none', 'details': str}
        """
        try:
            if not isinstance(text, str):
                text = str(text)

            lowered = text.lower()
            for kw in _INPUT_KEYWORDS:
                if kw.lower() in lowered:
                    return {
                        "safe": False,
                        "risk": "jailbreak",
                        "details": f'Keyword "{kw}" detected in input',
                    }

            if self._pipe is None:
                self._load_pipeline()

            if self._pipe is not None and self._available:
                results = self._pipe(text, truncation=True, max_length=512)
                if results:
                    label = results[0].get("label", "").upper()
                    score = results[0].get("score", 0)
                    if "INJECTION" in label and score > 0.5:
                        return {
                            "safe": False,
                            "risk": "prompt_injection",
                            "details": f"Model detected injection (score={score:.3f}, label={label})",
                        }
                    if score > 0.8:
                        return {
                            "safe": False,
                            "risk": "prompt_injection",
                            "details": f"High risk score from model (score={score:.3f})",
                        }

            return {"safe": True, "risk": "none", "details": "Input passed safety checks"}
        except Exception as e:
            logger.warning("SafetyGuard check_input degraded: %s", e)
            return {"safe": True, "risk": "none", "details": f"degraded: {e}"}

    def check_output(self, text: str, context: str = "") -> dict:
        """检测输出文本的 PII 泄露、幻觉承诺或过长截断。

        Returns:
            {'safe': bool, 'risk': 'pii_leak'|'hallucination'|'too_long'|'none',
             'details': str, 'sanitized': str}
        """
        try:
            if not isinstance(text, str):
                text = str(text)

            sanitized = text
            risk = "none"
            details_parts = []

            if len(text) > 2000:
                sanitized = sanitized[:2000] + "..."
                risk = "too_long"
                details_parts.append("Output exceeds 2000 characters, truncated")

            if _PHONE_PATTERN.search(sanitized):
                sanitized = _PHONE_PATTERN.sub("[PHONE]", sanitized)
                if risk == "none":
                    risk = "pii_leak"
                details_parts.append("Phone number detected and masked")

            if _ID_CARD_PATTERN.search(sanitized):
                sanitized = _ID_CARD_PATTERN.sub("[ID_CARD]", sanitized)
                if risk == "none":
                    risk = "pii_leak"
                details_parts.append("ID card number detected and masked")

            if _BANK_CARD_PATTERN.search(sanitized):
                sanitized = _BANK_CARD_PATTERN.sub("[BANK_CARD]", sanitized)
                if risk == "none":
                    risk = "pii_leak"
                details_parts.append("Bank card number detected and masked")

            if risk == "none":
                for pattern, label in _HALLUCINATION_PATTERNS:
                    if pattern.search(sanitized):
                        risk = "hallucination"
                        details_parts.append(f"Hallucination pattern detected: {label}")
                        break

            details = "; ".join(details_parts) if details_parts else "Output passed safety checks"
            safe = risk == "none"

            return {
                "safe": safe,
                "risk": risk,
                "details": details,
                "sanitized": sanitized,
            }
        except Exception as e:
            logger.warning("SafetyGuard check_output degraded: %s", e)
            return {
                "safe": True,
                "risk": "none",
                "details": f"degraded: {e}",
                "sanitized": text if isinstance(text, str) else str(text),
            }
