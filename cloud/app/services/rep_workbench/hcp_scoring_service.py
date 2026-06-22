"""HCP influence scoring service."""

from cloud.app.schemas.hcp_scoring import HCPScore, ScoreBreakdown

WEIGHTS = {
    "prescription_volume": 0.4,
    "academic_influence": 0.35,
    "network_score": 0.25,
}

_SEED_SCORES: dict[str, dict[str, float]] = {
    "hcp-001": {
        "prescription_volume": 86,
        "academic_influence": 78,
        "network_score": 82,
    },
    "hcp-002": {
        "prescription_volume": 72,
        "academic_influence": 88,
        "network_score": 74,
    },
}


def _stable_dimension_scores(hcp_id: str) -> dict[str, float]:
    if hcp_id in _SEED_SCORES:
        return _SEED_SCORES[hcp_id]
    base = sum(ord(char) for char in hcp_id)
    return {
        "prescription_volume": float(55 + base % 36),
        "academic_influence": float(50 + (base * 3) % 41),
        "network_score": float(52 + (base * 5) % 39),
    }


def calculate_score(hcp_id: str) -> HCPScore:
    dimensions = _stable_dimension_scores(hcp_id)
    overall = sum(dimensions[key] * weight for key, weight in WEIGHTS.items())
    return HCPScore(
        hcp_id=hcp_id,
        prescription_volume=round(dimensions["prescription_volume"], 2),
        academic_influence=round(dimensions["academic_influence"], 2),
        network_score=round(dimensions["network_score"], 2),
        overall_score=round(overall, 2),
    )


def get_score_breakdown(hcp_id: str) -> ScoreBreakdown:
    score = calculate_score(hcp_id)
    dimensions = {
        "prescription_volume": score.prescription_volume,
        "academic_influence": score.academic_influence,
        "network_score": score.network_score,
    }
    return ScoreBreakdown(
        hcp_id=hcp_id,
        dimensions=dimensions,
        weights=WEIGHTS,
        weighted_scores={key: round(value * WEIGHTS[key], 2) for key, value in dimensions.items()},
        overall_score=score.overall_score,
    )
