"""Multi-stop route optimization service."""

from math import asin, cos, radians, sin, sqrt
from threading import Lock

from assistant.app.schemas.route_optimization import RouteResult, RouteStop

_LOCK = Lock()
_ROUTE_HISTORY: dict[str, list[RouteResult]] = {}

_KNOWN_STARTS: dict[str, tuple[float, float]] = {
    "上海南京东路100号": (31.2357, 121.4814),
    "上海人民广场": (31.2304, 121.4737),
}


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    radius_km = 6371.0
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    return 2 * radius_km * asin(sqrt(a))


def _start_point(start: str, stops: list[RouteStop]) -> tuple[float, float]:
    if start in _KNOWN_STARTS:
        return _KNOWN_STARTS[start]
    if stops:
        return stops[0].lat, stops[0].lng
    return 31.2304, 121.4737


def _time_window_rank(stop: RouteStop) -> str:
    return stop.time_window or "99:99"


def optimize_route(start: str, stops: list[RouteStop]) -> RouteResult:
    """Approximate TSP with nearest-neighbor, priority, and time-window weighting."""
    remaining = list(stops)
    optimized: list[RouteStop] = []
    current_lat, current_lng = _start_point(start, stops)
    total_distance = 0.0

    while remaining:

        def score(stop: RouteStop) -> tuple[float, str]:
            distance = _haversine_km(current_lat, current_lng, stop.lat, stop.lng)
            priority_penalty = (10 - stop.priority) * 0.35
            return distance + priority_penalty, _time_window_rank(stop)

        next_stop = min(remaining, key=score)
        leg_distance = _haversine_km(current_lat, current_lng, next_stop.lat, next_stop.lng)
        total_distance += leg_distance
        optimized.append(next_stop)
        remaining.remove(next_stop)
        current_lat, current_lng = next_stop.lat, next_stop.lng

    total_distance = round(total_distance, 2)
    total_duration = int(round(total_distance / 28 * 60 + len(optimized) * 8)) if optimized else 0
    result = RouteResult(
        optimized_order=optimized,
        total_distance_km=total_distance,
        total_duration_min=total_duration,
    )
    with _LOCK:
        _ROUTE_HISTORY.setdefault("default", []).append(result)
    return result


def get_history(rep_id: str) -> list[RouteResult]:
    return _ROUTE_HISTORY.get(rep_id, _ROUTE_HISTORY.get("default", []))
