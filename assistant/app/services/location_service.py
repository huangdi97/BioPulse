import math
from datetime import datetime, timezone

from fastapi import HTTPException
from starlette import status

from assistant.app.repositories import HcpLocationRepository
from assistant.app.services.base import BaseService


def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class LocationService(BaseService):
    def create(self, hcp_id: int, body, user_id: int) -> dict:
        hcp = self.db.execute("SELECT id FROM hcp WHERE id = ? AND is_active = 1", (hcp_id,)).fetchone()
        if not hcp:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="HCP not found")
        repo = HcpLocationRepository(self.db)
        now = datetime.now(timezone.utc).isoformat()
        location_id = repo.create(
            data={
                "hcp_id": hcp_id,
                "address": body.address,
                "latitude": body.latitude,
                "longitude": body.longitude,
                "is_primary": body.is_primary if body.is_primary is not None else 1,
                "notes": body.notes,
            },
            extra={"created_by": user_id, "created_at": now, "updated_at": now},
        )
        return {"id": location_id}

    def list(self, hcp_id: int) -> list:
        repo = HcpLocationRepository(self.db)
        rows = repo.list_all(
            conditions=["hcp_id=?", "is_active=1"],
            params=[hcp_id],
            order_by="is_primary DESC, id ASC",
        )
        return [dict(r) for r in rows]

    def update(self, location_id: int, body) -> dict:
        repo = HcpLocationRepository(self.db)
        row = repo.get_by_id(location_id)
        if not row or not row["is_active"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")
        updates = body.model_dump(exclude_unset=True)
        if not updates:
            return dict(row)
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        repo.update(location_id, updates)
        return dict(repo.get_by_id(location_id))

    def delete(self, location_id: int) -> None:
        repo = HcpLocationRepository(self.db)
        row = repo.get_by_id(location_id)
        if not row or not row["is_active"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")
        repo.soft_delete(location_id)

    def optimize_route(self, body) -> dict:
        if not body.hcp_ids:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="hcp_ids is required",
            )

        placeholders = ",".join("?" for _ in body.hcp_ids)
        rows = self.db.execute(
            f"""SELECT h.id as hcp_id, h.name as hcp_name, l.address, l.latitude, l.longitude
                FROM hcp h JOIN hcp_location l ON h.id = l.hcp_id
                WHERE h.id IN ({placeholders}) AND l.is_active = 1 AND l.latitude IS NOT NULL AND l.longitude IS NOT NULL
                AND l.is_primary = 1""",
            body.hcp_ids,
        ).fetchall()
        if not rows:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No locations found for given HCP IDs",
            )

        stops = [dict(r) for r in rows]
        current_lat = body.start_lat
        current_lng = body.start_lng
        unvisited = stops[:]
        ordered = []
        total_distance = 0.0

        max_results = body.max_results if body.max_results else len(unvisited)

        while unvisited and len(ordered) < max_results:
            nearest = min(
                unvisited,
                key=lambda s: haversine(current_lat, current_lng, s["latitude"], s["longitude"]),
            )
            dist = haversine(current_lat, current_lng, nearest["latitude"], nearest["longitude"])
            total_distance += dist
            ordered.append(
                {
                    "hcp_id": nearest["hcp_id"],
                    "hcp_name": nearest["hcp_name"],
                    "address": nearest["address"],
                    "distance_km": round(dist, 2),
                    "order": len(ordered) + 1,
                }
            )
            current_lat = nearest["latitude"]
            current_lng = nearest["longitude"]
            unvisited.remove(nearest)

        return {
            "optimized_route": ordered,
            "total_distance_km": round(total_distance, 2),
            "total_hcps": len(ordered),
        }
