"""团队服务管理团队信息与成员协作。"""

from typing import Optional

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import TeamsRepository, UserTeamRepository
from shared.base import validate_columns
from shared.base_service import BaseService
from shared.columns import TABLE_TEAMS_COLS


def _row_to_team_out(row) -> dict:
    """将数据库行转换为团队输出字典。

    Args:
        row: 数据库查询结果行

    Returns:
        团队信息字典
    """
    return {
        "id": row["id"],
        "name": row["name"],
        "description": row["description"],
        "is_active": row["is_active"],
        "created_by": row["created_by"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


class TeamService(BaseService):
    """团队管理服务，提供团队的增删改查与成员管理功能。"""

    def _get_repos(self):
        """获取团队和用户团队仓库实例。

        Returns:
            包含 TeamsRepository 和 UserTeamRepository 的元组
        """
        return TeamsRepository(self._connection()), UserTeamRepository(self._connection())

    def _get_team_or_404(self, team_id: int):
        """根据ID获取团队，不存在则返回404。

        Args:
            team_id: 团队ID

        Returns:
            团队数据行

        Raises:
            HTTPException: 团队不存在时返回404
        """
        teams_repo, _ = self._get_repos()
        row = teams_repo.get_by_id(team_id)
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Team not found")
        return row

    def create_team(self, name: str, description: Optional[str], created_by: int) -> dict:
        """创建新团队。

        Args:
            name: 团队名称
            description: 团队描述
            created_by: 创建者用户ID

        Returns:
            创建的团队信息字典
        """
        teams_repo, _ = self._get_repos()
        team_id = teams_repo.create(
            {
                "name": name,
                "description": description,
                "created_by": created_by,
                "created_at": "CURRENT_TIMESTAMP",
                "updated_at": "CURRENT_TIMESTAMP",
            }
        )
        row = teams_repo.get_by_id(team_id)
        return _row_to_team_out(row)

    def list_teams(self, name: Optional[str] = None, page: int = 1, page_size: int = 20) -> dict:
        """查询团队列表，支持按名称筛选和分页。

        Args:
            name: 团队名称筛选（模糊匹配）
            page: 页码
            page_size: 每页数量

        Returns:
            包含 items、total、page、page_size、total_pages 的字典
        """
        teams_repo, _ = self._get_repos()
        conditions = ["is_active=1"]
        params = []
        if name:
            conditions.append("name LIKE ?")
            params.append(f"%{name}%")

        total, total_pages, rows = teams_repo.paginate(
            page=page,
            page_size=page_size,
            conditions=conditions,
            params=params,
            order_by="id DESC",
        )
        items = [_row_to_team_out(r) for r in rows]
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    def get_team(self, team_id: int) -> dict:
        """获取团队详情，包含成员信息。

        Args:
            team_id: 团队ID

        Returns:
            包含团队基本信息和成员列表的字典
        """
        teams_repo, _ = self._get_repos()
        row = self._get_team_or_404(team_id)

        member_rows = self.db.execute(
            "SELECT ut.user_id, u.username, ut.role FROM user_team ut LEFT JOIN users u ON ut.user_id = u.id WHERE ut.team_id=?",
            (team_id,),
        ).fetchall()

        members = [
            {
                "user_id": m["user_id"],
                "username": m["username"],
                "role": m["role"],
            }
            for m in member_rows
        ]

        data = _row_to_team_out(row)
        data["member_count"] = len(members)
        data["members"] = members
        return data

    def update_team(
        self,
        team_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[int] = None,
    ) -> dict:
        """更新团队信息。

        Args:
            team_id: 团队ID
            name: 新团队名称（可选）
            description: 新团队描述（可选）
            is_active: 是否启用（可选）

        Returns:
            更新后的团队信息字典
        """
        teams_repo, _ = self._get_repos()
        self._get_team_or_404(team_id)

        updates = {}
        if name is not None:
            updates["name"] = name
        if description is not None:
            updates["description"] = description
        if is_active is not None:
            updates["is_active"] = is_active

        if not updates:
            row = teams_repo.get_by_id(team_id)
            return _row_to_team_out(row)

        updates["updated_at"] = "CURRENT_TIMESTAMP"
        validate_columns({k: True for k in updates}, "teams", TABLE_TEAMS_COLS)
        teams_repo.update(team_id, updates)

        row = teams_repo.get_by_id(team_id)
        return _row_to_team_out(row)

    def delete_team(self, team_id: int) -> None:
        """软删除团队。

        Args:
            team_id: 团队ID
        """
        teams_repo, _ = self._get_repos()
        self._get_team_or_404(team_id)
        teams_repo.soft_delete(team_id)

    def add_member(self, team_id: int, user_id: int, role: str = "member") -> None:
        """添加团队成员。

        Args:
            team_id: 团队ID
            user_id: 用户ID
            role: 角色（默认 member）

        Raises:
            HTTPException: 成员已存在时返回409冲突
        """
        teams_repo, user_team_repo = self._get_repos()
        self._get_team_or_404(team_id)

        try:
            user_team_repo.create(
                {
                    "user_id": user_id,
                    "team_id": team_id,
                    "role": role,
                    "created_at": "CURRENT_TIMESTAMP",
                }
            )
        except Exception:  # noqa: BLE001  # DB constraints (unique, foreign key) may vary by backend
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                detail="Member already in team",
            )

    def remove_member(self, team_id: int, user_id: int) -> None:
        """移除团队成员。

        Args:
            team_id: 团队ID
            user_id: 用户ID

        Raises:
            HTTPException: 成员不存在时返回404
        """
        teams_repo, _ = self._get_repos()
        self._get_team_or_404(team_id)

        cur = self.db.execute(
            "DELETE FROM user_team WHERE team_id=? AND user_id=?",
            (team_id, user_id),
        )
        self.db.commit()

        if cur.rowcount == 0:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Member not found in team")
