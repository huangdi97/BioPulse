from typing import Optional

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import TeamsRepository, UserTeamRepository
from cloud.app.services.base import BaseService
from shared.base import validate_columns
from shared.columns import TABLE_TEAMS_COLS


def _row_to_team_out(row) -> dict:
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
    def _get_repos(self):
        return TeamsRepository(self.db), UserTeamRepository(self.db)

    def _get_team_or_404(self, team_id: int):
        teams_repo, _ = self._get_repos()
        row = teams_repo.get_by_id(team_id)
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Team not found")
        return row

    def create_team(
        self, name: str, description: Optional[str], created_by: int
    ) -> dict:
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

    def list_teams(
        self, name: Optional[str] = None, page: int = 1, page_size: int = 20
    ) -> dict:
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
        teams_repo, _ = self._get_repos()
        row = self._get_team_or_404(team_id)

        member_rows = self.db.execute(
            "SELECT ut.user_id, u.username, ut.role "
            "FROM user_team ut "
            "LEFT JOIN users u ON ut.user_id = u.id "
            "WHERE ut.team_id=?",
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
        teams_repo, _ = self._get_repos()
        self._get_team_or_404(team_id)
        teams_repo.soft_delete(team_id)

    def add_member(self, team_id: int, user_id: int, role: str = "member") -> None:
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
        except Exception:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                detail="Member already in team",
            )

    def remove_member(self, team_id: int, user_id: int) -> None:
        teams_repo, _ = self._get_repos()
        self._get_team_or_404(team_id)

        cur = self.db.execute(
            "DELETE FROM user_team WHERE team_id=? AND user_id=?",
            (team_id, user_id),
        )
        self.db.commit()

        if cur.rowcount == 0:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, detail="Member not found in team"
            )
