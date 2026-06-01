"""Seed product data for demo purposes."""

import sqlite3
import json


def seed_products(conn: sqlite3.Connection):
    conn.execute(
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
    existing = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    if existing > 0:
        return
    conn.execute(
        "INSERT INTO products (name, category, brand, model, spec, unit_price, keywords, tech_params, cert_status) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "FBS 胎牛血清",
            "细胞培养试剂",
            "Gibco",
            "10099-141",
            "500ml",
            6800.0,
            json.dumps(["FBS", "胎牛血清", "fetal bovine serum", "细胞培养"]),
            json.dumps(
                {
                    "origin": "South America",
                    "sterility": "sterile-filtered",
                    "endotoxin": "<10 EU/ml",
                    "hemoglobin": "<25 mg/dl",
                }
            ),
            "CE/IVD",
        ),
    )
    conn.commit()
