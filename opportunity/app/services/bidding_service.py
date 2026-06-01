from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from starlette import status

from opportunity.app.repositories import BiddingInfoRepository
from opportunity.app.services.base import BaseService


class BiddingService(BaseService):
    def create_bidding(self, body, user_id: int) -> int:
        repo = BiddingInfoRepository(self.db)
        now = datetime.now(timezone.utc).isoformat()
        return repo.create(
            body.model_dump(),
            extra={
                "created_by": user_id,
                "created_at": now,
                "updated_at": now,
            },
        )

    def list_bidding(
        self,
        page: int,
        page_size: int,
        status_val: Optional[str] = None,
        hospital: Optional[str] = None,
        department: Optional[str] = None,
        product_category: Optional[str] = None,
    ) -> tuple:
        repo = BiddingInfoRepository(self.db)
        conditions = ["is_active = 1"]
        params: list = []

        if status_val:
            conditions.append("status = ?")
            params.append(status_val)
        if hospital:
            conditions.append("hospital LIKE ?")
            params.append(f"%{hospital}%")
        if department:
            conditions.append("department LIKE ?")
            params.append(f"%{department}%")
        if product_category:
            conditions.append("product_category LIKE ?")
            params.append(f"%{product_category}%")

        return repo.paginate(
            page,
            page_size,
            conditions=conditions,
            params=params,
            order_by="id DESC",
        )

    def get_bidding(self, bidding_id: int) -> dict:
        repo = BiddingInfoRepository(self.db)
        row = repo.get_by_id(bidding_id)
        if not row or row["is_active"] != 1:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Bidding record not found"
            )
        return dict(row)

    def update_bidding(self, bidding_id: int, body) -> dict:
        repo = BiddingInfoRepository(self.db)
        row = repo.get_by_id(bidding_id)
        if not row or row["is_active"] != 1:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Bidding record not found"
            )

        updates = body.model_dump(exclude_unset=True)
        if not updates:
            return dict(row)

        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        repo.update(bidding_id, updates)
        return dict(repo.get_by_id(bidding_id))

    def delete_bidding(self, bidding_id: int) -> None:
        repo = BiddingInfoRepository(self.db)
        row = repo.get_by_id(bidding_id)
        if not row or row["is_active"] != 1:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Bidding record not found"
            )
        repo.soft_delete(bidding_id)

    def get_bidding_raw(self, bidding_id: int):
        return self.db.execute(
            "SELECT * FROM bidding_info WHERE id = ? AND is_active = 1",
            (bidding_id,),
        ).fetchone()
