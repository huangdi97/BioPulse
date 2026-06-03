from cloud.shared.columns import (
    TABLE_KG_ENTITIES_COLS,
    TABLE_KG_RELATIONS_COLS,
    TABLE_KG_SEARCH_CACHE_COLS,
)
from cloud.shared.repository import BaseRepository


class KgEntitiesRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "kg_entities", TABLE_KG_ENTITIES_COLS)

    def get_by_entity_id(self, entity_id: str):
        row = self.db.execute(
            f"SELECT {', '.join(self.cols)} FROM {self.table_name} WHERE entity_id=?",
            (entity_id,),
        ).fetchone()
        return dict(row) if row else None

    def exists_entity_id(self, entity_id: str):
        return self.db.execute(f"SELECT id FROM {self.table_name} WHERE entity_id=?", (entity_id,)).fetchone() is not None

    def list_filtered(self, entity_type=None, name=None, status_="active"):
        conditions, params = [], []
        if entity_type:
            conditions.append("entity_type=?")
            params.append(entity_type)
        if name:
            conditions.append("name LIKE ?")
            params.append(f"%{name}%")
        if status_:
            conditions.append("status=?")
            params.append(status_)
        return self.list_all(
            conditions=conditions or None,
            params=params or None,
            order_by="created_at DESC",
        )

    def search_by_name_and_types(self, query: str, entity_types=None, limit: int = 20):
        conditions = ["status='active'", "name LIKE ?"]
        params: list = [f"%{query}%"]
        if entity_types:
            ph = ",".join(["?"] * len(entity_types))
            conditions.append(f"entity_type IN ({ph})")
            params.extend(entity_types)
        placeholders = ", ".join(self.cols)
        where = " WHERE " + " AND ".join(conditions)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name}{where} LIMIT {limit}",
            params,
        ).fetchall()
        return [dict(r) for r in rows]

    def count_active(self):
        return self.db.execute(f"SELECT COUNT(*) FROM {self.table_name} WHERE status='active'").fetchone()[0]

    def count_by_entity_type(self):
        rows = self.db.execute(f"SELECT entity_type, COUNT(*) as cnt FROM {self.table_name} WHERE status='active' GROUP BY entity_type").fetchall()
        return [{"type": r["entity_type"], "count": r["cnt"]} for r in rows]

    def soft_delete_by_entity_id(self, entity_id: str) -> bool:
        cursor = self.db.execute(
            f"UPDATE {self.table_name} SET status='inactive', updated_at=CURRENT_TIMESTAMP WHERE entity_id=?",
            (entity_id,),
        )
        self.db.commit()
        return cursor.rowcount > 0

    def top_active(self, limit: int = 5):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE status='active' ORDER BY confidence DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


class KgRelationsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "kg_relations", TABLE_KG_RELATIONS_COLS)

    def list_by_entity_id(self, entity_id: str):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE source_entity_id=? OR target_entity_id=?",
            (entity_id, entity_id),
        ).fetchall()
        return [dict(r) for r in rows]

    def list_filtered(self, source=None, target=None, relation_type=None):
        conditions, params = [], []
        if source:
            conditions.append("source_entity_id=?")
            params.append(source)
        if target:
            conditions.append("target_entity_id=?")
            params.append(target)
        if relation_type:
            conditions.append("relation_type=?")
            params.append(relation_type)
        return self.list_all(
            conditions=conditions or None,
            params=params or None,
            order_by="created_at DESC",
        )

    def list_by_entity_ids_batch(self, entity_ids):
        if not entity_ids:
            return []
        ph = ",".join(["?"] * len(entity_ids))
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE source_entity_id IN ({ph}) OR target_entity_id IN ({ph})",
            entity_ids + entity_ids,
        ).fetchall()
        return [dict(r) for r in rows]

    def count_all(self):
        return self.db.execute(f"SELECT COUNT(*) FROM {self.table_name}").fetchone()[0]

    def count_by_relation_type(self):
        rows = self.db.execute(f"SELECT relation_type, COUNT(*) as cnt FROM {self.table_name} GROUP BY relation_type").fetchall()
        return [{"type": r["relation_type"], "count": r["cnt"]} for r in rows]

    def top_connected(self, limit: int = 10):
        rows = self.db.execute(
            f"""SELECT e.name, e.entity_type, COUNT(r.id) as degree FROM kg_entities e
                LEFT JOIN {self.table_name} r ON e.entity_id=r.source_entity_id OR e.entity_id=r.target_entity_id
                WHERE e.status='active' GROUP BY e.entity_id ORDER BY degree DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        return [{"name": r["name"], "type": r["entity_type"], "degree": r["degree"]} for r in rows]


class KgSearchCacheRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "kg_search_cache", TABLE_KG_SEARCH_CACHE_COLS)

    def count_all(self):
        return self.db.execute(f"SELECT COUNT(*) FROM {self.table_name}").fetchone()[0]
