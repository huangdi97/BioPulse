def log_action(db, user_id: int, action: str, entity_type: str,
                entity_id: int = None, detail: str = "",
                source_end: str = "cloud", ip_address: str = ""):
    db.execute(
        "INSERT INTO audit_logs (user_id, action, entity_type, entity_id, detail, source_end, ip_address) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (user_id, action, entity_type, entity_id, detail, source_end, ip_address),
    )
    db.commit()
