"""HCP channel preference analysis."""

from statistics import mean

_CHANNEL_LABELS = {
    "wechat": "微信",
    "phone": "电话",
    "face_to_face": "面对面",
    "email": "邮件",
}

_INTERACTION_HISTORY: dict[str, dict[str, list[dict[str, float]]]] = {
    "hcp-001": {
        "wechat": [
            {"open_rate": 0.92, "answer_rate": 0.0, "acceptance_rate": 0.86},
            {"open_rate": 0.88, "answer_rate": 0.0, "acceptance_rate": 0.82},
        ],
        "phone": [
            {"open_rate": 0.0, "answer_rate": 0.61, "acceptance_rate": 0.55},
            {"open_rate": 0.0, "answer_rate": 0.58, "acceptance_rate": 0.52},
        ],
        "face_to_face": [
            {"open_rate": 0.0, "answer_rate": 0.0, "acceptance_rate": 0.76},
            {"open_rate": 0.0, "answer_rate": 0.0, "acceptance_rate": 0.72},
        ],
        "email": [
            {"open_rate": 0.49, "answer_rate": 0.0, "acceptance_rate": 0.38},
            {"open_rate": 0.44, "answer_rate": 0.0, "acceptance_rate": 0.35},
        ],
    },
    "hcp-002": {
        "wechat": [{"open_rate": 0.63, "answer_rate": 0.0, "acceptance_rate": 0.55}],
        "phone": [{"open_rate": 0.0, "answer_rate": 0.82, "acceptance_rate": 0.78}],
        "face_to_face": [{"open_rate": 0.0, "answer_rate": 0.0, "acceptance_rate": 0.68}],
        "email": [{"open_rate": 0.71, "answer_rate": 0.0, "acceptance_rate": 0.59}],
    },
}


def _history_for(hcp_id: str) -> dict[str, list[dict[str, float]]]:
    return _INTERACTION_HISTORY.get(hcp_id) or _INTERACTION_HISTORY["hcp-001"]


def _score(channel: str, records: list[dict[str, float]]) -> float:
    if not records:
        return 0.0
    open_rate = mean(record.get("open_rate", 0.0) for record in records)
    answer_rate = mean(record.get("answer_rate", 0.0) for record in records)
    acceptance_rate = mean(record.get("acceptance_rate", 0.0) for record in records)
    if channel in {"wechat", "email"}:
        return round((open_rate * 0.55 + acceptance_rate * 0.45) * 100, 1)
    if channel == "phone":
        return round((answer_rate * 0.60 + acceptance_rate * 0.40) * 100, 1)
    if channel == "face_to_face":
        return round(acceptance_rate * 100, 1)
    return round((open_rate * 0.35 + answer_rate * 0.25 + acceptance_rate * 0.40) * 100, 1)


def analyze_preference(hcp_id: str) -> list[dict]:
    """Return channel labels sorted by preference score."""
    scored = [
        {
            "channel": channel,
            "label": _CHANNEL_LABELS[channel],
            "preference_score": _score(channel, records),
            "signals": {
                "message_open_rate": round(mean(record.get("open_rate", 0.0) for record in records) * 100, 1),
                "call_answer_rate": round(mean(record.get("answer_rate", 0.0) for record in records) * 100, 1),
                "acceptance_rate": round(mean(record.get("acceptance_rate", 0.0) for record in records) * 100, 1),
                "interaction_count": len(records),
            },
        }
        for channel, records in _history_for(hcp_id).items()
    ]
    return sorted(scored, key=lambda item: item["preference_score"], reverse=True)


def get_preferred_strategy(hcp_id: str) -> dict:
    preferences = analyze_preference(hcp_id)
    primary = preferences[0]
    secondary = preferences[1] if len(preferences) > 1 else primary
    return {
        "hcp_id": hcp_id,
        "channel_tags": [item["label"] for item in preferences],
        "preferred_channels": preferences,
        "strategy": {
            "primary_channel": primary["label"],
            "backup_channel": secondary["label"],
            "touch_sequence": [primary["label"], secondary["label"], "会后资料邮件"],
            "recommendation": f"优先使用{primary['label']}触达，未响应时切换到{secondary['label']}，内容控制在疾病教育与合规材料范围内。",
        },
    }
