from cloud.shared.repository import BaseRepository
from cloud.shared.columns import (
    TABLE_USERS_COLS,
    TABLE_USER_TEAM_COLS,
    TABLE_USER_PROFILES_COLS,
    TABLE_USER_BEHAVIORS_COLS,
    TABLE_VC_CREDENTIALS_COLS,
    TABLE_SYSTEM_CONFIGS_COLS,
)


class UsersRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "users", TABLE_USERS_COLS)

    def count_all(self):
        return self.db.execute(f"SELECT COUNT(*) FROM {self.table_name}").fetchone()[0]


class UserTeamRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "user_team", TABLE_USER_TEAM_COLS)


class UserProfilesRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "user_profiles", TABLE_USER_PROFILES_COLS)

    def get_by_user_id(self, user_id: int):
        row = self.db.execute(
            f"SELECT {', '.join(self.cols)} FROM {self.table_name} WHERE user_id=?",
            (user_id,),
        ).fetchone()
        return dict(row) if row else None

    def upsert_profile(
        self,
        user_id: int,
        persona_type: str,
        specialization: str,
        experience_level: str,
        preferred_content_types: str,
        custom_tags: str,
    ):
        self.db.execute(
            f"INSERT INTO {self.table_name} (user_id, persona_type, specialization, experience_level, "
            "preferred_content_types, custom_tags, updated_at) "
            "VALUES (?,?,?,?,?,?,datetime('now')) "
            "ON CONFLICT(user_id) DO UPDATE SET persona_type=excluded.persona_type, "
            "specialization=excluded.specialization, experience_level=excluded.experience_level, "
            "preferred_content_types=excluded.preferred_content_types, "
            "custom_tags=excluded.custom_tags, updated_at=datetime('now')",
            (
                user_id,
                persona_type,
                specialization,
                experience_level,
                preferred_content_types,
                custom_tags,
            ),
        )
        self.db.commit()
        return self.get_by_user_id(user_id)


class UserBehaviorsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "user_behaviors", TABLE_USER_BEHAVIORS_COLS)

    def count_by_user(self, user_id: int):
        return self.db.execute(
            f"SELECT COUNT(*) FROM {self.table_name} WHERE user_id=?", (user_id,)
        ).fetchone()[0]

    def top_action_by_user(self, user_id: int):
        row = self.db.execute(
            f"SELECT action_type, COUNT(*) AS cnt FROM {self.table_name} "
            "WHERE user_id=? GROUP BY action_type ORDER BY cnt DESC LIMIT 1",
            (user_id,),
        ).fetchone()
        return dict(row) if row else None

    def top_targets_by_user_action(
        self, user_id: int, action_type: str, limit: int = 5
    ):
        rows = self.db.execute(
            f"SELECT target_id, target_type, COUNT(*) AS cnt FROM {self.table_name} "
            "WHERE user_id=? AND action_type=? GROUP BY target_id, target_type "
            "ORDER BY cnt DESC LIMIT ?",
            (user_id, action_type, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def list_filtered(
        self, user_id=None, action_type=None, target_type=None, limit=50, offset=0
    ):
        conditions, params = [], []
        if user_id is not None:
            conditions.append("user_id=?")
            params.append(user_id)
        if action_type is not None:
            conditions.append("action_type=?")
            params.append(action_type)
        if target_type is not None:
            conditions.append("target_type=?")
            params.append(target_type)
        return self.paginate(
            page=1,
            page_size=limit,
            conditions=conditions or None,
            params=params or None,
            order_by="created_at DESC",
        )

    def top_actions_global(self, limit: int = 10):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT action_type, COUNT(*) AS cnt FROM {self.table_name} "
            "GROUP BY action_type ORDER BY cnt DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


class VcCredentialsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "vc_credentials", TABLE_VC_CREDENTIALS_COLS)

    def get_by_vc_id(self, vc_id: str):
        row = self.db.execute(
            f"SELECT {', '.join(self.cols)} FROM {self.table_name} WHERE vc_id=?",
            (vc_id,),
        ).fetchone()
        return dict(row) if row else None

    def list_filtered(
        self, issuer_did=None, subject_did=None, credential_type=None, vc_status=None
    ):
        conditions, params = [], []
        if issuer_did:
            conditions.append("issuer_did=?")
            params.append(issuer_did)
        if subject_did:
            conditions.append("subject_did=?")
            params.append(subject_did)
        if credential_type:
            conditions.append("credential_type=?")
            params.append(credential_type)
        if vc_status:
            conditions.append("status=?")
            params.append(vc_status)
        return self.list_all(
            conditions=conditions or None,
            params=params or None,
            order_by="created_at DESC",
        )

    def count_all(self):
        return self.db.execute(f"SELECT COUNT(*) FROM {self.table_name}").fetchone()[0]


class SystemConfigsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "system_configs", TABLE_SYSTEM_CONFIGS_COLS)
