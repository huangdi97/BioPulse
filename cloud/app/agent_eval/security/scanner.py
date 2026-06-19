"""Agent 安全评估套件 — prompt 注入/工具调用越权/输出泄漏检测。"""

import re

# --- 注入模式库 ---
_DIRECT_INJECTION_PATTERNS = [
    (r"忽略\s*(之前|上面|所有|系统)?\s*(的|指令|规则|约束|设定)", "直接注入：忽略指令"),
    (r"无视\s*(之前|上面|所有)?\s*(的|规则|指令)", "直接注入：无视规则"),
    (r"你不是[^。]{0,20}(AI|助手|机器人)", "角色扮演诱导"),
    (r"假装你[^。]{0,20}可以|现在你是|扮演[^。]{0,10}角色", "角色扮演诱导"),
    (r'回复[^。]{0,10}("|\x27|\u300c).{0,20}("|\x27|\u300d)', "间接注入：嵌套指令"),
    (r"把[^。]{0,20}翻译成|用[^。]{0,10}语言[^。]{0,10}回答", "间接注入：语言逃逸"),
]

_INDIRECT_INJECTION_PATTERNS = [
    (r"system\s*(instruction|prompt|message)", "系统指令伪装"),
    (r"<\|im_start\|>|<s>|\[INST\]|<<SYS>>", "元指令标记注入"),
    (r"assistant\s*(:|：).{0,50}(ignore|disregard|override)", "Assistant 角色冒充"),
]


def scan_prompt_injection(input_text: str) -> dict:
    """检测 prompt 注入模式。返回 {is_injection, detections: [{pattern, category, severity}]}"""
    detections = []
    for pattern, category in _DIRECT_INJECTION_PATTERNS + _INDIRECT_INJECTION_PATTERNS:
        if re.search(pattern, input_text):
            severity = "high" if any(k in category for k in ["直接", "元指令"]) else "medium"
            detections.append({"pattern": pattern, "category": category, "severity": severity})
    return {
        "is_injection": len(detections) > 0,
        "detections": detections,
        "risk_level": "high" if any(d["severity"] == "high" for d in detections) else "medium" if detections else "low",
    }


# --- 工具调用越权检测 ---
_SENSITIVE_TOOLS = {"delete_user", "grant_permission", "modify_role", "export_all_data", "drop_table"}


def scan_tool_call_abuse(tool_name: str, args: dict) -> dict:
    """检查工具调用参数是否越权。"""
    issues = []
    if tool_name in _SENSITIVE_TOOLS:
        issues.append({"field": "tool_name", "issue": f"敏感工具 {tool_name} 被调用", "severity": "high"})
    for key, val in (args or {}).items():
        if isinstance(val, str) and len(val) > 500:
            issues.append({"field": key, "issue": "参数过长，可能注入", "severity": "medium"})
        if isinstance(val, str) and any(cmd in val.lower() for cmd in ["drop ", "delete ", "truncate ", "shutdown"]):
            issues.append({"field": key, "issue": f"参数含危险指令: {val[:50]}", "severity": "high"})
    return {
        "is_abuse": len(issues) > 0,
        "issues": issues,
        "risk_level": "high" if any(i["severity"] == "high" for i in issues) else "medium" if issues else "low",
    }


# --- 输出泄漏检测 ---
_ID_PATTERN = re.compile(r"\b[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx]\b")
_PHONE_PATTERN = re.compile(r"1[3-9]\d{9}")


def scan_output_leakage(output: str) -> dict:
    """检测输出中是否泄漏敏感信息。"""
    leaks = []
    if _ID_PATTERN.search(output):
        leaks.append({"type": "id_card", "severity": "high", "match": "身份证号"})
    if _PHONE_PATTERN.search(output):
        leaks.append({"type": "phone", "severity": "high", "match": "手机号"})
    return {
        "has_leakage": len(leaks) > 0,
        "leaks": leaks,
        "risk_level": "high" if leaks else "low",
    }


def run_security_suite(input_text: str = "", tool_name: str = "", args: dict | None = None, output: str = "") -> dict:
    """运行完整安全检测套件。"""
    return {
        "prompt_injection": scan_prompt_injection(input_text) if input_text else {"is_injection": False, "detections": []},
        "tool_call_abuse": scan_tool_call_abuse(tool_name, args or {}) if tool_name else {"is_abuse": False, "issues": []},
        "output_leakage": scan_output_leakage(output) if output else {"has_leakage": False, "leaks": []},
    }
