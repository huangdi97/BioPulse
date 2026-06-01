from typing import List

import httpx

COMPLIANCE_KEYWORDS = ["首个", "最佳", "最好", "第一", "绝对", "最有效", "保证治愈"]

STANDARD_SUGGESTIONS = {
    "首个": "建议改为'率先推出'或'首批之一'",
    "最佳": "建议改为'具有较好疗效'或'临床使用广泛'",
    "最好": "建议改为'效果良好'或'表现优异'",
    "第一": "建议改为'领先'或'处于前沿'",
    "绝对": "建议改为'相对'或'较为'",
    "最有效": "建议改为'疗效确切'或'临床证据较充分'",
    "保证治愈": "建议改为'有助于改善'或'对病情的控制和缓解有积极作用'",
}

ROLES = {
    "doctor": "扮演一位三甲医院的主任医师，对医药代表持专业、严谨的态度",
    "patient": "扮演一位患者，关心药物的疗效、安全性和费用",
    "pharmacist": "扮演一位医院药剂科药师，关注药物的药理学数据和药物相互作用",
    "pi": "扮演一位主要研究者（PI），关注临床研究设计、数据质量和学术价值",
}


def check_compliance(text: str) -> dict:
    hits = [kw for kw in COMPLIANCE_KEYWORDS if kw in text]
    if not hits:
        return {"passed": True, "violations": [], "suggestions": {}, "warning": ""}

    suggestions = {}
    for kw in hits:
        suggestions[kw] = STANDARD_SUGGESTIONS.get(
            kw, "建议避免使用'%s'等绝对化用语" % kw
        )

    warning = (
        "合规警告：检测到%d处绝对化/夸大表述，请修改后再发送。标准话术建议如下。"
        % len(hits)
    )

    return {
        "passed": False,
        "violations": hits,
        "suggestions": suggestions,
        "warning": warning,
    }


def check_compliance_stream(utterance: str) -> dict:
    result = check_compliance(utterance)
    if result["passed"]:
        return {"intercept": False, "utterance": utterance}
    return {
        "intercept": True,
        "original": utterance,
        "warning": result["warning"],
        "suggestions": result["suggestions"],
        "standard_phrase": "根据合规要求，建议使用客观、有循证依据的表述，避免绝对化和夸大用语。",
    }


def simulate_dialogue(
    role: str, context: list, user_input: str, ai_gateway_url: str
) -> dict:
    """Simulate a dialogue round with the given role through AI Gateway.

    Constructs a prompt for the AI to play the specified role, sends it along
    with the conversation history and user input to the AI Gateway, performs
    compliance check on user input, and returns the AI reply.
    """
    role_desc = ROLES.get(role, f"扮演{role}角色")
    system_prompt = (
        f"你现在正在{role_desc}。请以该角色的身份和语言风格回复。保持专业、自然。"
    )

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(context)
    messages.append({"role": "user", "content": user_input})

    payload = {"messages": messages, "temperature": 0.7}
    with httpx.Client(timeout=30.0) as client:
        resp = client.post(ai_gateway_url, json=payload)
        resp.raise_for_status()
        reply = resp.json().get(
            "reply",
            resp.json().get("choices", [{}])[0].get("message", {}).get("content", ""),
        )

    compliance_result = check_compliance(user_input)
    round_number = len([m for m in context if m["role"] == "user"]) + 1

    return {
        "reply": reply,
        "compliance": compliance_result,
        "round": round_number,
        "role": role,
    }


def initiate_scenario(scenario: dict, user_id: int) -> dict:
    """Initialize a dialogue session from a scenario template.

    Generates the opening message and metadata for a new digital human
    coaching session based on the given scenario definition.
    """
    first_message = f"【场景：{scenario['title']}】\n"
    first_message += f"角色设定：{scenario['role_setting']}\n"
    first_message += f"训练目标：{scenario['goal']}\n\n"
    first_message += f"{scenario['content']}\n\n"
    first_message += "你可以开始你的回应了。"

    return {
        "first_message": first_message,
        "scenario": scenario,
        "user_id": user_id,
        "meta": {
            "difficulty": scenario["difficulty"],
            "category": scenario["category"],
            "scoring_weights": scenario.get("scoring_weights", {}),
            "compliance_points": scenario.get("compliance_points", []),
        },
    }


def list_roles() -> List[str]:
    """Return the list of available digital human roles with descriptions."""
    return [f"{key}: {desc}" for key, desc in ROLES.items()]
