"""HCP 管理服务模块。"""

from typing import Optional

from assistant.app.repositories import HcpRepository
from shared.base_service import BaseCrudService
from shared.hcp_service import BaseHcpService


class HcpService(BaseHcpService, BaseCrudService):
    """HCP 管理服务，提供 HCP 的增删改查等业务操作。"""

    def __init__(self, db=None):
        super().__init__(repository_class=HcpRepository, entity_name="HCP", db=db)

    def create_hcp(self, body, user_id: int) -> dict:
        return self.create(body, user_id)

    def list_hcps(
        self,
        page: int,
        page_size: int,
        name: Optional[str] = None,
        hospital: Optional[str] = None,
        department: Optional[str] = None,
        level: Optional[str] = None,
    ) -> tuple:
        conn = self._connection()
        try:
            repo = HcpRepository(conn)
            conditions, params = self._build_list_conditions(name, hospital, department, level)
            return repo.paginate(page=page, page_size=page_size, conditions=conditions, params=params)
        finally:
            self._close_connection(conn)

    def get_hcp(self, hcp_id: int) -> dict:
        conn = self._connection()
        try:
            repo = HcpRepository(conn)
            row = repo.get_by_id(hcp_id)
            if not row or row["is_active"] != 1:
                from fastapi import HTTPException
                from starlette import status
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="HCP not found")
            return dict(row)
        finally:
            self._close_connection(conn)

    def update_hcp(self, hcp_id: int, body) -> dict:
        conn = self._connection()
        try:
            repo = HcpRepository(conn)
            row = repo.get_by_id(hcp_id)
            if not row or row["is_active"] != 1:
                from fastapi import HTTPException
                from starlette import status
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="HCP not found")
            updates = body.model_dump(exclude_unset=True)
            if not updates:
                return dict(row)
            repo.update(hcp_id, updates)
            return dict(repo.get_by_id(hcp_id))
        finally:
            self._close_connection(conn)

    def delete_hcp(self, hcp_id: int) -> None:
        conn = self._connection()
        try:
            repo = HcpRepository(conn)
            row = repo.get_by_id(hcp_id)
            if not row or row["is_active"] != 1:
                from fastapi import HTTPException
                from starlette import status
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="HCP not found")
            repo.soft_delete(hcp_id)
        finally:
            self._close_connection(conn)
