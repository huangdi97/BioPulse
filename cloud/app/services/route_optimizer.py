import math


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two points on Earth in km."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def _nearest_neighbor_route(points: list[dict]) -> list[dict]:
    if not points:
        return []
    unvisited = points[:]
    route = [unvisited.pop(0)]
    while unvisited:
        last = route[-1]
        nearest = min(
            unvisited,
            key=lambda p: haversine(last["lat"], last["lng"], p["lat"], p["lng"]),
        )
        route.append(nearest)
        unvisited.remove(nearest)
    return route


def optimize_route(points: list[dict]) -> list[dict]:
    """Optimize PI visit route using Nearest Neighbor TSP with priority.

    Input: [{pi_id, name, lat, lng, priority}]
    Output: [{pi_id, name, visit_order, estimated_distance_km}]
    """
    if not points:
        return []

    valid = [
        p
        for p in points
        if -90 <= p.get("lat", 0) <= 90 and -180 <= p.get("lng", 0) <= 180
    ]
    if not valid:
        return []

    high = [p for p in valid if p.get("priority") == "high"]
    normal = [p for p in valid if p.get("priority") != "high"]

    ordered = _nearest_neighbor_route(high) + _nearest_neighbor_route(normal)

    result = []
    cumulative = 0.0
    for i, p in enumerate(ordered):
        if i > 0:
            prev = ordered[i - 1]
            cumulative += haversine(prev["lat"], prev["lng"], p["lat"], p["lng"])
        result.append(
            {
                "pi_id": p["pi_id"],
                "name": p["name"],
                "visit_order": i + 1,
                "estimated_distance_km": round(cumulative, 2),
            }
        )
    return result


def estimate_travel_time(distance_km: float) -> float:
    """Estimate travel time in hours assuming average 40 km/h."""
    return round(distance_km / 40.0, 2)
