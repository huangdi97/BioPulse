from cloud.shared.repository import BaseRepository
from cloud.shared.columns import (
    TABLE_OPPORTUNITIES_COLS,
    TABLE_CUSTOMERS_COLS,
    TABLE_CUSTOMER_INTERACTIONS_COLS,
    TABLE_HCP_INTERACTIONS_COLS,
    TABLE_HCP_PROFILES_COLS,
    TABLE_HCP_SIMULATIONS_COLS,
)


class OpportunitiesRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "opportunities", TABLE_OPPORTUNITIES_COLS)


class CustomersRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "customers", TABLE_CUSTOMERS_COLS)

    def exists(self, customer_id: int):
        return (
            self.db.execute(
                f"SELECT id FROM {self.table_name} WHERE id=?", (customer_id,)
            ).fetchone()
            is not None
        )


class CustomerInteractionsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "customer_interactions", TABLE_CUSTOMER_INTERACTIONS_COLS)

    def list_by_customer_id(self, customer_id: int):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE customer_id=? ORDER BY conducted_at DESC",
            (customer_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def list_filtered(self, type_=None, conducted_by=None, page=1, page_size=20):
        conditions, params = [], []
        if type_:
            conditions.append("type=?")
            params.append(type_)
        if conducted_by is not None:
            conditions.append("conducted_by=?")
            params.append(conducted_by)
        return self.paginate(
            page=page,
            page_size=page_size,
            conditions=conditions or None,
            params=params or None,
            order_by="conducted_at DESC",
        )


class HcpInteractionsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "hcp_interactions", TABLE_HCP_INTERACTIONS_COLS)

    def count_by_hcp_id(self, hcp_id: int):
        return self.db.execute(
            f"SELECT COUNT(*) FROM {self.table_name} WHERE hcp_id=?", (hcp_id,)
        ).fetchone()[0]

    def get_last_by_hcp_id(self, hcp_id: int):
        placeholders = ", ".join(self.cols)
        row = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE hcp_id=? ORDER BY conducted_at DESC LIMIT 1",
            (hcp_id,),
        ).fetchone()
        return dict(row) if row else None

    def list_by_hcp_id(self, hcp_id: int, page=1, page_size=20):
        conditions = ["hcp_id=?"]
        params = [hcp_id]
        return self.paginate(
            page=page,
            page_size=page_size,
            conditions=conditions,
            params=params,
            order_by="conducted_at DESC",
        )

    def get_recent_by_hcp_id(self, hcp_id: int, limit: int = 5):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE hcp_id=? ORDER BY conducted_at DESC LIMIT ?",
            (hcp_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]


class HcpProfilesRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "hcp_profiles", TABLE_HCP_PROFILES_COLS)

    def list_filtered(self, tier=None, specialty=None, city=None, page=1, page_size=20):
        conditions, params = [], []
        if tier:
            conditions.append("tier=?")
            params.append(tier)
        if specialty:
            conditions.append("specialty=?")
            params.append(specialty)
        if city:
            conditions.append("city=?")
            params.append(city)
        return self.paginate(
            page=page,
            page_size=page_size,
            conditions=conditions or None,
            params=params or None,
        )

    def count_active(self):
        return self.db.execute(
            f"SELECT COUNT(*) FROM {self.table_name} WHERE is_active=1"
        ).fetchone()[0]

    def tier_distribution(self):
        rows = self.db.execute(
            f"SELECT tier, COUNT(*) as cnt FROM {self.table_name} WHERE is_active=1 GROUP BY tier"
        ).fetchall()
        return {r["tier"]: r["cnt"] for r in rows}


class HcpSimulationsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "hcp_simulations", TABLE_HCP_SIMULATIONS_COLS)

    def count_by_hcp_id(self, hcp_id: int):
        return self.db.execute(
            f"SELECT COUNT(*) FROM {self.table_name} WHERE hcp_id=?", (hcp_id,)
        ).fetchone()[0]

    def count_all(self):
        return self.db.execute(f"SELECT COUNT(*) FROM {self.table_name}").fetchone()[0]

    def get_recent(self, limit: int = 5):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    def list_filtered(self, hcp_id=None, status_=None, page=1, page_size=20):
        conditions, params = [], []
        if hcp_id is not None:
            conditions.append("hcp_id=?")
            params.append(hcp_id)
        if status_:
            conditions.append("status=?")
            params.append(status_)
        return self.paginate(
            page=page,
            page_size=page_size,
            conditions=conditions or None,
            params=params or None,
            order_by="created_at DESC",
        )
