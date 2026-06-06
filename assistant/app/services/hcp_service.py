"""HCP 管理服务模块。"""

from typing import Optional

from fastapi import HTTPException
from starlette import status

from assistant.app.repositories import HcpRepository
from assistant.app.services.base import BaseService


class HcpService(BaseService):
    """HCP 管理服务，提供 HCP 的增删改查等业务操作。"""

    def create_hcp(self, body, user_id: int) -> dict:
        conn = self._connection()
        try:
            repo = HcpRepository(conn)
            row_id = repo.create(
                body.model_dump(),
                extra={"created_by": user_id},
            )
            return {"id": row_id}
        finally:
            conn.close()

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
            conditions = ["is_active = 1"]
            params: list = []

            if name:
                conditions.append("name LIKE ?")
                params.append(f"%{name}%")
            if hospital:
                conditions.append("hospital LIKE ?")
                params.append(f"%{hospital}%")
            if department:
                conditions.append("department LIKE ?")
                params.append(f"%{department}%")
            if level:
                conditions.append("level = ?")
                params.append(level)

            return repo.paginate(
                page=page,
                page_size=page_size,
                conditions=conditions,
                params=params,
            )
        finally:
            conn.close()

    def get_hcp(self, hcp_id: int) -> dict:
        conn = self._connection()
        try:
            repo = HcpRepository(conn)
            row = repo.get_by_id(hcp_id)
            if not row or row["is_active"] != 1:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="HCP not found")
            return dict(row)
        finally:
            conn.close()

    def update_hcp(self, hcp_id: int, body) -> dict:
        conn = self._connection()
        try:
            repo = HcpRepository(conn)
            row = repo.get_by_id(hcp_id)
            if not row or row["is_active"] != 1:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="HCP not found")
            updates = body.model_dump(exclude_unset=True)
            if not updates:
                return dict(row)
            repo.update(hcp_id, updates)
            return dict(repo.get_by_id(hcp_id))
        finally:
            conn.close()

    def delete_hcp(self, hcp_id: int) -> None:
        conn = self._connection()
        try:
            repo = HcpRepository(conn)
            row = repo.get_by_id(hcp_id)
            if not row or row["is_active"] != 1:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="HCP not found")
            repo.soft_delete(hcp_id)
        finally:
            conn.close()
