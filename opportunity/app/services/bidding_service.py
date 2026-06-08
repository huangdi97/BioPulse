"""投标相关业务逻辑服务，处理投标数据的管理和查询。"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from starlette import status

from opportunity.app.repositories import BiddingInfoRepository
from opportunity.app.services.base import BaseCrudService

"""招投标管理服务，负责招标信息的增删改查。"""


class BiddingService(BaseCrudService):
    """招投标信息管理：创建、列表查询（支持多条件筛选）、更新、软删除。"""

    def __init__(self, db=None):
        super().__init__(repository_class=BiddingInfoRepository, entity_name="Bidding", db=db)

    def create_bidding(self, body, user_id: int) -> int:
        """创建招标信息记录。

        Args:
            body: 招标信息请求体; user_id: 用户ID

        Returns:
            int: 新招标记录ID
        """
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
        """分页查询招标信息列表。

        Args:
            page: 页码; page_size: 每页条数; status_val: 可选状态过滤; hospital: 可选医院模糊查询; department: 可选科室模糊查询; product_category: 可选产品类别模糊查询

        Returns:
            tuple: (items, total, page, page_size, total_pages)
        """
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
        """根据ID获取招标信息详情。

        Args:
            bidding_id: 招标信息ID

        Returns:
            dict: 招标信息记录详情
        """
        repo = BiddingInfoRepository(self.db)
        row = repo.get_by_id(bidding_id)
        if not row or row["is_active"] != 1:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bidding record not found")
        return dict(row)

    def update_bidding(self, bidding_id: int, body) -> dict:
        """更新招标信息记录。

        Args:
            bidding_id: 招标信息ID; body: 更新数据请求体

        Returns:
            dict: 更新后的招标信息记录
        """
        repo = BiddingInfoRepository(self.db)
        row = repo.get_by_id(bidding_id)
        if not row or row["is_active"] != 1:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bidding record not found")

        updates = body.model_dump(exclude_unset=True)
        if not updates:
            return dict(row)

        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        repo.update(bidding_id, updates)
        return dict(repo.get_by_id(bidding_id))

    def delete_bidding(self, bidding_id: int) -> None:
        """软删除招标信息记录。

        Args:
            bidding_id: 招标信息ID
        """
        repo = BiddingInfoRepository(self.db)
        row = repo.get_by_id(bidding_id)
        if not row or row["is_active"] != 1:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bidding record not found")
        repo.soft_delete(bidding_id)

    def get_bidding_raw(self, bidding_id: int):
        """获取招标信息的原始数据库行（不抛出HTTP异常）。

        Args:
            bidding_id: 招标信息ID

        Returns:
            sqlite3.Row | None: 原始数据库行
        """
        return self.db.execute(
            "SELECT * FROM bidding_info WHERE id = ? AND is_active = 1",
            (bidding_id,),
        ).fetchone()
