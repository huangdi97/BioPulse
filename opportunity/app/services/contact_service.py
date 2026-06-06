"""联系人服务，处理客户联系人信息的管理和查询。"""

from datetime import datetime, timezone

from fastapi import HTTPException
from starlette import status

from opportunity.app.repositories import ContactRecordRepository
from opportunity.app.services.base import BaseService

"""联系记录服务，管理商机线索下的联系沟通记录。"""


class ContactService(BaseService):
    """联系记录管理：创建、分页列表（按商机关联）、详情查询、更新、软删除。"""

    def _check_opportunity_exists(self, opportunity_id: int) -> None:
        row = self.db.execute(
            "SELECT id FROM opportunity WHERE id = ? AND is_active = 1",
            (opportunity_id,),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found")

    def create_contact(self, body, opportunity_id: int, user_id: int) -> int:
        self._check_opportunity_exists(opportunity_id)
        repo = ContactRecordRepository(self.db)
        now = datetime.now(timezone.utc).isoformat()
        return repo.create(
            body.model_dump(),
            extra={
                "opportunity_id": opportunity_id,
                "created_by": user_id,
                "created_at": now,
            },
        )

    def list_contacts(self, opportunity_id: int, page: int, page_size: int) -> tuple:
        self._check_opportunity_exists(opportunity_id)
        repo = ContactRecordRepository(self.db)
        return repo.paginate(
            page,
            page_size,
            conditions=["opportunity_id = ?"],
            params=[opportunity_id],
            order_by="id DESC",
        )

    def get_contact(self, contact_id: int) -> dict:
        repo = ContactRecordRepository(self.db)
        row = repo.get_by_id(contact_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
        return dict(row)

    def update_contact(self, contact_id: int, body) -> dict:
        repo = ContactRecordRepository(self.db)
        row = repo.get_by_id(contact_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")

        updates = body.model_dump(exclude_unset=True)
        if not updates:
            return dict(row)

        repo.update(contact_id, updates)
        return dict(repo.get_by_id(contact_id))

    def delete_contact(self, contact_id: int) -> None:
        repo = ContactRecordRepository(self.db)
        row = repo.get_by_id(contact_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
        repo.soft_delete(contact_id)
