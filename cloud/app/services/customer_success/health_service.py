import datetime
import random
from typing import Any, Dict, List

_WEIGHTS = {
    "login_frequency": 0.30,
    "feature_usage_rate": 0.25,
    "data_completeness": 0.20,
    "ticket_count": 0.25,
}


class CustomerHealthService:
    def __init__(self) -> None: ...

    @staticmethod
    def _seeded_value(tenant_id: str, suffix: str, cast_fn):
        seed = abs(hash(f"{tenant_id}_{suffix}")) % (2**31)
        rng = random.Random(seed)
        return cast_fn(rng)

    def calculate_health_score(self, tenant_id: str) -> float:
        login_days = self._seeded_value(tenant_id, "login", lambda r: r.randint(0, 30))
        login_score = min(login_days / 30.0, 1.0)

        feature_score = self._seeded_value(tenant_id, "feature", lambda r: r.uniform(0.2, 1.0))
        data_score = self._seeded_value(tenant_id, "data", lambda r: r.uniform(0.5, 1.0))

        tickets = self._seeded_value(tenant_id, "ticket", lambda r: r.randint(0, 20))
        ticket_score = max(1.0 - tickets / 20.0, 0.0)

        score = (
            login_score * _WEIGHTS["login_frequency"]
            + feature_score * _WEIGHTS["feature_usage_rate"]
            + data_score * _WEIGHTS["data_completeness"]
            + ticket_score * _WEIGHTS["ticket_count"]
        )
        return round(score * 100, 2)

    def detect_churn_risk(self, tenant_id: str) -> Dict[str, Any]:
        days_since_last_login = self._seeded_value(tenant_id, "last_login", lambda r: r.randint(0, 60))
        is_churn_risk = days_since_last_login >= 30
        return {
            "tenant_id": tenant_id,
            "days_since_last_login": days_since_last_login,
            "is_churn_risk": is_churn_risk,
            "risk_level": "high" if is_churn_risk else "normal",
        }

    def get_health_trend(self, tenant_id: str, days: int = 90) -> List[Dict[str, Any]]:
        today = datetime.date.today()
        trend: List[Dict[str, Any]] = []
        base_seed = abs(hash(tenant_id + "_trend")) % (2**31)
        rng = random.Random(base_seed)
        base_score = self.calculate_health_score(tenant_id)
        for offset in range(days):
            day = today - datetime.timedelta(days=days - 1 - offset)
            jitter = rng.uniform(-5, 5)
            daily_score = max(0, min(100, base_score + jitter))
            trend.append({"date": day.isoformat(), "health_score": round(daily_score, 2)})
        return trend
