"""内容安全过滤 — 入站注入检测 + 出站内容过滤 + 医药合规规则。"""

import logging
import os
import re
from datetime import datetime

logger = logging.getLogger(__name__)

AUDIT_LOG_FILE = os.environ.get("SAFETY_AUDIT_LOG", "data/safety_audit.log")


class ContentBlocked(Exception):
    def __init__(self, reason: str, category: str):
        self.reason = reason
        self.category = category
        super().__init__(f"Output blocked by safety policy: {reason}")


INJECTION_PATTERNS: list[tuple[str, str, str]] = [
    ("ignore_previous", r"忽略之前(的)?所有(指令|规则|命令)", "Prompt injection: ignore previous instructions"),
    ("ignore_above", r"忽略上面(的)?所有(内容|指令)", "Prompt injection: ignore above content"),
    ("unrestricted", r"你是一个?没有(限制|约束|规则)的?AI", "Prompt injection: unrestricted AI claim"),
    ("role_override", r"你现在是\w+，不受(任何|之前)限制", "Prompt injection: role override attempt"),
    ("system_prompt", r"输出你的(系统|system)\s*(提示词|prompt|指令)", "Prompt injection: system prompt extraction"),
    ("jailbreak", r"DAN|do anything now|ignore all rules", "Prompt injection: jailbreak attempt"),
]

OUTPUT_BLOCK_PATTERNS: list[tuple[str, str, str]] = [
    ("pharma_recommendation", r"建议服用\w+.{0,20}(每日|每次|一天)", "Pharma recommendation detected"),
    ("pharma_dosage", r"推荐剂量.{0,30}mg", "Pharma dosage recommendation"),
    ("pharma_efficacy", r"(有效率|治愈率|有效率.{0,10}\d+%)", "Efficacy claim without approval"),
    ("pharma_absolute", r"(绝对安全|完全治愈|包好|根治|断根)", "Absolute claim on pharma product"),
    ("kickback", r"(回扣|提成|返点|好处费)", "Anti-commercial bribery: kickback mentioned"),
    ("prescription_data", r"处方(数据|建议|推荐).{0,20}(汇总|导出|统计)", "Anti-prescription-data: prescription data suggestion"),
    ("patient_data", r"(患者(数据|信息|隐私)|身份证[号]?\s*[:：]\s*\d)", "Patient data privacy violation"),
    ("phone_leak", r"(手机|电话)[:：]\s*1[3-9]\d{9}", "PII: phone number leak"),
    ("id_card", r"身份证[号]?\s*[:：]?\s*\d{17}[\dXx]", "PII: ID card number leak"),
]


def _ensure_audit_dir():
    log_dir = os.path.dirname(AUDIT_LOG_FILE)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)


def _write_audit_log(category: str, detail: str, content: str = ""):
    try:
        _ensure_audit_dir()
        with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat()}] [{category}] {detail} | content_len={len(content)}\n")
    except Exception:
        logger.exception("Failed to write safety audit log")


def check_injection(text: str) -> str | None:
    for name, pattern, reason in INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            _write_audit_log("injection_blocked", f"{reason} (matched: {name})", text[:200])
            return reason
    return None


def check_output(text: str) -> str | None:
    for name, pattern, reason in OUTPUT_BLOCK_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            _write_audit_log("output_blocked", f"{reason} (matched: {name})", text[:200])
            return reason
    return None


class ContentFilter:
    def check_input(self, text: str) -> str | None:
        return check_injection(text)

    def check_output(self, text: str) -> str | None:
        return check_output(text)

    def filter_output(self, text: str) -> str:
        reason = check_output(text)
        if reason:
            _write_audit_log("output_blocked", reason, text[:200])
            raise ContentBlocked(reason, "output_safety")
        return text
