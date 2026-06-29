class TerritoryService:
    _store: dict[int, dict] = {}
    _next_id: int = 1

    def create_territory(
        self,
        name: str,
        region: str,
        provinces: list[str],
        hospitals: list[str],
    ) -> dict:
        tid = self._next_id
        self._next_id += 1
        record = {
            "id": tid,
            "name": name,
            "region": region,
            "provinces": provinces,
            "hospitals": hospitals,
            "assigned_rep": None,
            "monthly_visits": 0,
            "quarterly_targets": {},
            "progress": {},
        }
        self._store[tid] = record
        return record

    def assign_rep(self, territory_id: int, rep_id: int) -> dict:
        t = self._store.get(territory_id)
        if not t:
            raise ValueError(f"Territory {territory_id} not found")
        t["assigned_rep"] = rep_id
        return t

    def set_targets(
        self,
        territory_id: int,
        monthly_visits: int,
        quarterly_targets: dict,
    ) -> dict:
        t = self._store.get(territory_id)
        if not t:
            raise ValueError(f"Territory {territory_id} not found")
        t["monthly_visits"] = monthly_visits
        t["quarterly_targets"] = quarterly_targets
        return t

    def get_progress(self, territory_id: int) -> dict:
        t = self._store.get(territory_id)
        if not t:
            raise ValueError(f"Territory {territory_id} not found")
        return t.get("progress", {})

    def optimize_route(self, territory_id: int, start_location: str) -> dict:
        t = self._store.get(territory_id)
        if not t:
            raise ValueError(f"Territory {territory_id} not found")
        return {
            "territory_id": territory_id,
            "start_location": start_location,
            "hospitals": t["hospitals"],
            "optimized_route": t["hospitals"][:],
            "estimated_distance_km": len(t["hospitals"]) * 15,
            "estimated_duration_min": len(t["hospitals"]) * 30,
        }
