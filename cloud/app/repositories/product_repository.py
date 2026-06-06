"""产品数据访问层。"""

import json
import sqlite3
from typing import Optional


class ProductRepository:
    """产品仓库，管理产品信息、规格、价格、认证等数据。"""

    def __init__(self, db: sqlite3.Connection):
        self.db = db
        self._ensure_table()

    def _ensure_table(self):
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS products ("
            "product_id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "name TEXT NOT NULL, "
            "category TEXT NOT NULL DEFAULT '', "
            "brand TEXT NOT NULL DEFAULT '', "
            "model TEXT NOT NULL DEFAULT '', "
            "spec TEXT NOT NULL DEFAULT '', "
            "unit_price REAL NOT NULL DEFAULT 0.0, "
            "keywords TEXT NOT NULL DEFAULT '[]', "
            "tech_params TEXT NOT NULL DEFAULT '{}', "
            "cert_status TEXT NOT NULL DEFAULT ''"
            ")"
        )
        self.db.commit()

    def create(
        self,
        name: str,
        category: str = "",
        brand: str = "",
        model: str = "",
        spec: str = "",
        unit_price: float = 0.0,
        keywords: list | None = None,
        tech_params: dict | None = None,
        cert_status: str = "",
    ) -> int:
        cursor = self.db.execute(
            "INSERT INTO products (name, category, brand, model, spec, "
            "unit_price, keywords, tech_params, cert_status) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                name,
                category,
                brand,
                model,
                spec,
                unit_price,
                json.dumps(keywords or []),
                json.dumps(tech_params or {}),
                cert_status,
            ),
        )
        self.db.commit()
        return cursor.lastrowid

    def get_by_id(self, product_id: int) -> Optional[dict]:
        row = self.db.execute("SELECT * FROM products WHERE product_id = ?", (product_id,)).fetchone()
        if row:
            return dict(row)
        return None

    def update(self, product_id: int, **kwargs) -> bool:
        allowed = {
            "name",
            "category",
            "brand",
            "model",
            "spec",
            "unit_price",
            "keywords",
            "tech_params",
            "cert_status",
        }
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return False
        if "keywords" in updates:
            updates["keywords"] = json.dumps(updates["keywords"])
        if "tech_params" in updates:
            updates["tech_params"] = json.dumps(updates["tech_params"])
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [product_id]
        cursor = self.db.execute(f"UPDATE products SET {set_clause} WHERE product_id = ?", values)
        self.db.commit()
        return cursor.rowcount > 0

    def delete(self, product_id: int) -> bool:
        cursor = self.db.execute("DELETE FROM products WHERE product_id = ?", (product_id,))
        self.db.commit()
        return cursor.rowcount > 0

    def search(self, q: str = "", category: str = "") -> list[dict]:
        conditions = []
        params = []
        if q:
            pattern = f"%{q}%"
            conditions.append("(name LIKE ? OR keywords LIKE ? OR brand LIKE ? OR model LIKE ?)")
            params.extend([pattern, pattern, pattern, pattern])
        if category:
            conditions.append("category = ?")
            params.append(category)
        where = ""
        if conditions:
            where = " WHERE " + " AND ".join(conditions)
        rows = self.db.execute(f"SELECT * FROM products{where} ORDER BY product_id DESC", params).fetchall()
        return [dict(r) for r in rows]
