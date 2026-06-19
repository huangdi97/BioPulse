import random
from typing import List

_ENGAGEMENT_WEIGHTS = {
    "email_open": 0.15,
    "email_click": 0.25,
    "meeting_attend": 0.35,
    "content_download": 0.10,
    "webinar_register": 0.20,
    "form_submit": 0.30,
}

_CHURN_FACTORS = [
    "declining_email_engagement",
    "missed_appointments",
    "negative_sentiment_feedback",
    "competitor_content_consumption",
    "long_inactivity_window",
]


def _mock_activity_vector(hcp_id: str) -> dict:
    seed = abs(hash(hcp_id)) % (2**31)
    rng = random.Random(seed)
    return {k: rng.randint(0, 10) for k in _ENGAGEMENT_WEIGHTS}


def predict_engagement_score(hcp_id: str) -> float:
    raw = _mock_activity_vector(hcp_id)
    total_weight = sum(_ENGAGEMENT_WEIGHTS.values())
    numerator = 0.0
    for activity, weight in _ENGAGEMENT_WEIGHTS.items():
        numerator += raw.get(activity, 0) * weight / 10.0
    score = numerator / total_weight
    if score < 0.0:
        return 0.0
    if score > 1.0:
        return 1.0
    return round(score, 4)


def predict_churn_risk(hcp_id: str) -> dict:
    seed = abs(hash(hcp_id)) % (2**31)
    rng = random.Random(seed + 999)
    raw = _mock_activity_vector(hcp_id)
    # active_count intentionally unused — kept for future model integration
    engagement = predict_engagement_score(hcp_id)
    factors: List[str] = []
    if raw.get("email_open", 0) < 3:
        factors.append("declining_email_engagement")
    if raw.get("meeting_attend", 0) < 1:
        factors.append("missed_appointments")
    if rng.random() < 0.3:
        factors.append("negative_sentiment_feedback")
    if raw.get("content_download", 0) > raw.get("email_click", 0) + 2:
        factors.append("competitor_content_consumption")
    days_since_last = rng.randint(0, 90)
    if days_since_last > 45:
        factors.append("long_inactivity_window")

    if engagement < 0.3 or len(factors) >= 3:
        risk = "high"
    elif engagement < 0.6 or len(factors) >= 2:
        risk = "medium"
    else:
        risk = "low"
    return {"risk": risk, "factors": factors, "engagement_score": engagement}


def get_next_best_action(hcp_id: str) -> dict:
    risk_info = predict_churn_risk(hcp_id)
    risk = risk_info["risk"]
    factors = risk_info["factors"]
    if risk == "high":
        action = "send_personalized_retention_email"
        reason = "HCP at high churn risk; re-engage with tailored content."
        channel = "email"
    elif risk == "medium":
        action = "invite_to_upcoming_webinar"
        reason = "Moderate engagement detected; deepen relationship via event."
        channel = "email"
    else:
        action = "share_new_research_summary"
        reason = "HCP is engaged; provide value-added scientific content."
        channel = "email_or_portal"
    return {
        "hcp_id": hcp_id,
        "recommended_action": action,
        "reason": reason,
        "channel": channel,
        "risk_level": risk,
        "contributing_factors": factors,
    }
