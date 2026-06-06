"""HCP 管理服务模块。"""

from typing import Optional

from fastapi import HTTPException
from starlette import status

from assistant.app.repositories import HcpRepository
from assistant.app.services.base import BaseService


class HcpService(BaseService):
    """HCP 管理服务，提供 HCP 的增删改查等业务操作。"""

    def create_hcp(self, body, user_id: int) -> dict:
        """创建HCP记录。

        Args:
            body: HCP请求体; user_id: 用户ID

        Returns:
            dict: 包含新记录 id 的结果
        """
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
        """分页查询HCP列表。

        Args:
            page: 页码; page_size: 每页条数; name: 可选姓名模糊查询; hospital: 可选医院模糊查询; department: 可选科室模糊查询; level: 可选级别过滤

        Returns:
            tuple: (items, total, page, page_size, total_pages)
        """
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
        """根据ID获取HCP详情。

        Args:
            hcp_id: HCP ID

        Returns:
            dict: HCP记录详情
        """
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
        """更新HCP记录。

        Args:
            hcp_id: HCP ID; body: 更新数据请求体

        Returns:
            dict: 更新后的HCP记录
        """
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
        """软删除HCP记录。

        Args:
            hcp_id: HCP ID
        """
        conn = self._connection()
        try:
            repo = HcpRepository(conn)
            row = repo.get_by_id(hcp_id)
            if not row or row["is_active"] != 1:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="HCP not found")
            repo.soft_delete(hcp_id)
        finally:
            conn.close()
