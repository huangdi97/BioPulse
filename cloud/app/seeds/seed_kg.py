import sqlite3


def seed_kg(conn: sqlite3.Connection) -> None:
    """Insert default KG entities and relations if tables are empty."""
    count = conn.execute("SELECT COUNT(*) FROM kg_entities").fetchone()[0]
    if count > 0:
        return
    now = "2026-05-25 10:00:00"
    entities = [
        (
            "kg:hcp:zhang",
            "hcp",
            "张主任",
            '["张明远主任医师","张主任医师"]',
            '{"hospital":"北京协和医院","department":"肿瘤科","tier":"A"}',
            "",
            0,
            "active",
            1.0,
        ),
        (
            "kg:hcp:li",
            "hcp",
            "李医生",
            '["李雪梅副主任医师","李雪梅医生"]',
            '{"hospital":"北京大学第一医院","department":"心血管内科","tier":"A"}',
            "",
            0,
            "active",
            1.0,
        ),
        (
            "kg:drug:xinyaoa",
            "drug",
            "新药A",
            '["GLP-1受体激动剂"]',
            '{"category":"糖尿病治疗","status":"已上市"}',
            "",
            0,
            "active",
            1.0,
        ),
        (
            "kg:drug:jingpinb",
            "drug",
            "竞品B",
            "[]",
            '{"category":"糖尿病治疗","competitor":true}',
            "",
            0,
            "active",
            1.0,
        ),
        (
            "kg:disease:diabetes2",
            "disease",
            "2型糖尿病",
            "[]",
            '{"prevalence":"高"}',
            "",
            0,
            "active",
            1.0,
        ),
    ]
    for (
        entity_id,
        entity_type,
        name,
        aliases,
        properties,
        source_table,
        source_row_id,
        status,
        confidence,
    ) in entities:
        conn.execute(
            "INSERT INTO kg_entities (entity_id, entity_type, name, aliases, properties, "
            "source_table, source_row_id, status, confidence, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                entity_id,
                entity_type,
                name,
                aliases,
                properties,
                source_table,
                source_row_id,
                status,
                confidence,
                now,
            ),
        )
    relations = [
        ("kg:hcp:zhang", "kg:drug:xinyaoa", "prescribes", 1.0),
        ("kg:drug:jingpinb", "kg:drug:xinyaoa", "competes", 0.9),
        ("kg:disease:diabetes2", "kg:drug:xinyaoa", "treats", 1.0),
        ("kg:hcp:li", "kg:drug:jingpinb", "prescribes", 0.7),
        ("kg:hcp:zhang", "kg:hcp:li", "collaborates", 0.8),
        ("kg:drug:xinyaoa", "kg:disease:diabetes2", "belongs_to", 1.0),
    ]
    for source, target, rel_type, weight in relations:
        conn.execute(
            "INSERT INTO kg_relations (source_entity_id, target_entity_id, relation_type, weight, created_at) VALUES (?,?,?,?,?)",
            (source, target, rel_type, weight, now),
        )
    conn.commit()
