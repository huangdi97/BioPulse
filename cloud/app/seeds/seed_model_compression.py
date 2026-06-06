"""种子数据：模型压缩作业示例（量化/张量分解）。"""


def seed_model_compression(conn):
    now = "2026-05-25 10:00:00"
    rows = conn.execute("SELECT COUNT(*) FROM model_compression_jobs").fetchone()[0]
    if rows > 0:
        conn.commit()
        return
    conn.execute(
        "INSERT OR IGNORE INTO model_compression_jobs "
        "(job_id, model_name, compression_type, original_size_bytes, compressed_size_bytes, "
        "compression_ratio, accuracy_impact, parameters_before, parameters_after, "
        "status, result_detail, started_at, completed_at, created_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "mc:quant-001",
            "bert-base-chinese",
            "quantization",
            412000000,
            164800000,
            0.6,
            0.012,
            110000000,
            110000000,
            "completed",
            '{"method":"INT8","layers_quantized":12,"speedup":2.3}',
            "2026-05-24 08:00:00",
            "2026-05-24 08:45:00",
            now,
        ),
    )
    conn.execute(
        "INSERT OR IGNORE INTO model_compression_jobs "
        "(job_id, model_name, compression_type, original_size_bytes, compressed_size_bytes, "
        "compression_ratio, accuracy_impact, parameters_before, parameters_after, "
        "status, result_detail, started_at, completed_at, created_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "mc:tensor-001",
            "gpt2-small",
            "tensor_decomposition",
            548000000,
            137000000,
            0.75,
            0.028,
            124000000,
            82000000,
            "completed",
            '{"method":"SVD","rank":64,"layers_decomposed":12,"speedup":1.8}',
            "2026-05-23 14:00:00",
            "2026-05-23 15:30:00",
            now,
        ),
    )
    conn.commit()
